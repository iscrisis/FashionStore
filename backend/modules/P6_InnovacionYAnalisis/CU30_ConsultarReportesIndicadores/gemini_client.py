"""Integración con Gemini para la "consulta inteligente" de CU30 (segunda
parte, dashboard del Administrador) -- interpreta la consulta en texto/voz
y, después, redacta un resumen a partir de datos YA calculados por
ReportesService (ver consulta_inteligente_service.py).

Reutiliza tal cual la infraestructura base ya existente de CU29
(CU29_ObtenerRecomendacionesIA/gemini_client.py: cliente_gemini,
generar_con_reintento, GeminiNoDisponibleError) -- misma
GEMINI_API_KEY/GEMINI_MODEL (ver app/core/config.py), sin una segunda
configuración independiente ni una segunda implementación del reintento.
Los DOS prompts de este archivo son exclusivos de reportes -- no comparten
nada con los del asistente/chatbot de CU29.

Gemini NUNCA calcula reportes, NUNCA consulta PostgreSQL, NUNCA genera SQL:
  1. interpretar_consulta_reporte -- lee la consulta del Administrador y
     devuelve ÚNICAMENTE un JSON con la intención (de una lista CERRADA) y
     los criterios mencionados (sucursal/periodo). FastAPI valida la
     intención y resuelve sucursal_id/fechas reales SIEMPRE en
     consulta_inteligente_service.py -- nunca confía ciegamente en lo que
     Gemini haya escrito ahí (ver ese archivo, _resolver_periodo).
  2. generar_resumen_reporte -- redacta el resumen final en lenguaje
     natural a partir de un "Reporte" de texto que consulta_inteligente_
     service.py arma con datos YA verificados contra PostgreSQL (los
     mismos Services de la primera parte de CU30). Se le indica
     explícitamente que no puede mencionar ni concluir nada fuera de eso.

Cualquier fallo se traduce SIEMPRE a GeminiNoDisponibleError -- CU30 base
(filtros manuales, KPIs, gráficos) sigue funcionando igual aunque esto
falle (ver router.py/consulta_inteligente_service.py).
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
    prompt = _PROMPT_INTERPRETACION.format(
        intenciones=", ".join(f'"{i}"' for i in INTENCIONES_VALIDAS),
        consulta=consulta.strip()[:_MAX_CONSULTA],
    )
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
        logger.warning("CU30 -- Gemini no pudo interpretar la consulta inteligente (%s).", type(exc).__name__)
        raise GeminiNoDisponibleError("Gemini no respondió a tiempo.") from exc


def generar_resumen_reporte(contexto: str) -> str:
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
        logger.warning("CU30 -- Gemini no pudo generar el resumen (%s).", type(exc).__name__)
        raise GeminiNoDisponibleError("Gemini no respondió a tiempo.") from exc
