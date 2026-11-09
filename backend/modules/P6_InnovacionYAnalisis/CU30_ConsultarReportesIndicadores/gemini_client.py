"""Integración con Gemini u OpenRouter para la "consulta inteligente" de CU30.

Soporta dos proveedores configurables via app.core.config.IA_PROVIDER:
  - "gemini": Google Gemini API (GEMINI_API_KEY + GEMINI_MODEL)
  - "openrouter": OpenRouter API compatible con OpenAI (OPENROUTER_API_KEY + OPENROUTER_MODEL)

Ambos proveedores implementan la misma interfaz:
  - interpretar_consulta_reporte(consulta: str) -> dict
  - generar_resumen_reporte(contexto: str) -> str

Los DOS prompts de este archivo son exclusivos de reportes.

IA NUNCA calcula reportes, NUNCA consulta PostgreSQL, NUNCA genera SQL:
  1. interpretar_consulta_reporte -- lee la consulta y devuelve JSON con
     intención (lista CERRADA) y criterios (sucursal/periodo). FastAPI
     valida SIEMPRE en consulta_inteligente_service.py.
  2. generar_resumen_reporte -- redacta resumen a partir de datos YA
     verificados contra PostgreSQL.

Cualquier fallo -> GeminiNoDisponibleError -> fallback amigable (ver router.py).
"""

import json
import logging

from app.core.config import settings
from modules.P6_InnovacionYAnalisis.CU29_ObtenerRecomendacionesIA.gemini_client import (
    GeminiNoDisponibleError,
    cliente_gemini,
    generar_con_reintento,
)

logger = logging.getLogger(__name__)

_MAX_CONSULTA = 300

# Lista CERRADA -- Gemini nunca puede pedir un reporte que no esté acá (ver
# consulta_inteligente_service.py, que además valida esto de nuevo del lado
# de FastAPI antes de ejecutar cualquier Service).
INTENCIONES_VALIDAS = (
    "resumen_general",
    "ventas",
    "ingresos",
    "ventas_por_sucursal",
    "ventas_por_metodo_pago",
    "ventas_por_tipo",
    "productos_mas_vendidos",
    "inventario",
    "stock_bajo",
    "reservas",
    "devoluciones_cambios",
)

_PROMPT_INTERPRETACION = """Eres el módulo de interpretación de la "consulta inteligente" del \
dashboard de reportes de FashionStore (tienda de ropa), usado SOLO por el \
Administrador. La consulta puede venir escrita o transcrita desde un \
comando de voz. Devuelve ÚNICAMENTE un objeto JSON, sin texto adicional, \
sin markdown, con EXACTAMENTE esta forma:

{{
  "intencion": uno de [{intenciones}] o null,
  "sucursal": string (nombre de sucursal mencionado) o null,
  "periodo": "hoy" | "ayer" | "esta_semana" | "este_mes" | "mes_pasado" | "este_anio" o null,
  "mes_nombre": nombre de un mes en español (ej. "septiembre") o null,
  "fecha_desde": "YYYY-MM-DD" o null,
  "fecha_hasta": "YYYY-MM-DD" o null
}}

Reglas:
- "intencion" DEBE ser EXACTAMENTE uno de los valores de la lista, o null \
si la consulta no corresponde a ningún reporte -- nunca inventes otro valor.
- "sucursal" es el nombre tal como lo dijo el Administrador -- nunca lo \
inventes si no lo mencionó.
- Usa "periodo" para expresiones relativas (hoy/ayer/esta semana/este mes/ \
mes pasado/este año). Usa "mes_nombre" SOLO si mencionó un mes por nombre \
sin dar un rango exacto de días (ej. "en septiembre"). Usa "fecha_desde"/ \
"fecha_hasta" SOLO si dio un rango EXACTO de días (ej. "del 1 al 15 de \
septiembre").
- Si no menciona ningún periodo, deja los 4 campos de fecha en null.
- No agregues NINGÚN texto fuera del JSON.

Consulta del Administrador:
{consulta}
"""

_PROMPT_RESUMEN = """Eres el redactor de resúmenes del dashboard de reportes de FashionStore, \
para el Administrador. Redacta un resumen profesional y breve (máximo 3 \
frases, sin listas ni markdown, en español) basado ÚNICAMENTE en los datos \
del "Reporte" de abajo -- nunca menciones un monto, producto, sucursal, \
porcentaje o tendencia que no esté ahí. Puedes señalar hechos derivados \
directamente de los datos (ej. la sucursal con mayor ingreso, el producto \
más vendido, el método de pago principal), pero NUNCA inventes causas ni \
conclusiones comerciales ("esto ocurrió porque...") que el reporte no \
demuestra. Mantén un tono profesional y descriptivo.

Reporte:
{contexto}
"""


def interpretar_consulta_reporte(consulta: str) -> dict:
    """Interpreta la consulta usando el proveedor configurado (Gemini u OpenRouter)."""
    prompt = _PROMPT_INTERPRETACION.format(
        intenciones=", ".join(f'"{i}"' for i in INTENCIONES_VALIDAS),
        consulta=consulta.strip()[:_MAX_CONSULTA],
    )

    proveedor = settings.IA_PROVIDER.lower()

    if proveedor == "openrouter":
        # Usar OpenRouter - reemplazar {intenciones}, dejar {consulta} para openrouter_client
        from .openrouter_client import interpretar_consulta_reporte_openrouter
        intenciones_str = ", ".join(f'"{i}"' for i in INTENCIONES_VALIDAS)
        prompt_template = _PROMPT_INTERPRETACION.replace("{intenciones}", intenciones_str)
        return interpretar_consulta_reporte_openrouter(consulta.strip()[:_MAX_CONSULTA], prompt_template)

    # Por defecto: Gemini
    client = cliente_gemini()
    try:
        respuesta = generar_con_reintento(
            client,
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json", "temperature": 0.1},
        )
        texto = (respuesta.text or "").strip()
        datos = json.loads(texto)
        if not isinstance(datos, dict):
            raise ValueError("La interpretación de Gemini no fue un objeto JSON.")
        return datos
    except GeminiNoDisponibleError:
        raise
    except Exception as exc:
        exc_type = type(exc).__name__
        exc_msg = str(exc)[:150]
        http_code = getattr(exc, 'status_code', None) or getattr(exc, 'code', None)
        logger.warning(
            "[CU16/CU30] Gemini interpretación falló: %s (HTTP: %s) - %s",
            exc_type,
            http_code or "desconocido",
            exc_msg,
        )
        raise GeminiNoDisponibleError("Gemini no respondió a tiempo.") from exc


def generar_resumen_reporte(contexto: str) -> str:
    """Genera resumen usando el proveedor configurado (Gemini u OpenRouter)."""
    proveedor = settings.IA_PROVIDER.lower()

    if proveedor == "openrouter":
        # Usar OpenRouter
        from .openrouter_client import generar_resumen_reporte_openrouter
        return generar_resumen_reporte_openrouter(contexto, _PROMPT_RESUMEN)

    # Por defecto: Gemini
    prompt = _PROMPT_RESUMEN.format(contexto=contexto)
    client = cliente_gemini()
    try:
        respuesta = generar_con_reintento(
            client, model=settings.GEMINI_MODEL, contents=prompt, config={"temperature": 0.3}
        )
        texto = (respuesta.text or "").strip()
        if not texto:
            raise ValueError("Gemini devolvió un resumen vacío.")
        return texto
    except GeminiNoDisponibleError:
        raise
    except Exception as exc:
        exc_type = type(exc).__name__
        exc_msg = str(exc)[:150]
        http_code = getattr(exc, 'status_code', None) or getattr(exc, 'code', None)
        logger.warning(
            "[CU16/CU30] Gemini resumen falló: %s (HTTP: %s) - %s",
            exc_type,
            http_code or "desconocido",
            exc_msg,
        )
        raise GeminiNoDisponibleError("Gemini no respondió a tiempo.") from exc
