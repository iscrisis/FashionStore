"""Integración con Gemini API -- único punto de todo el backend que importa
el SDK de Gemini (`google-genai`) y lee GEMINI_API_KEY/GEMINI_MODEL (ver
app/core/config.py). Mismo criterio que app/integrations/stripe_client.py
con Stripe: la clave NUNCA se envía a Angular, nunca se registra en logs,
nunca se lee desde el request HTTP -- solo desde la variable de entorno del
proceso.

Gemini se usa para DOS tareas, nunca para más que eso:
  1. interpretar_consulta -- lee el mensaje del Cliente y devuelve ÚNICAMENTE
     un JSON con la intención y los criterios mencionados. Nunca ejecuta SQL,
     nunca genera SQL, nunca decide qué productos existen -- eso lo resuelve
     PostgreSQL a través de repository.py, siempre después de esta llamada
     (ver service.py).
  2. generar_respuesta -- redacta la respuesta final en lenguaje natural a
     partir de un "contexto comercial" de texto que arma service.py con
     datos YA verificados contra PostgreSQL. Se le indica explícitamente que
     no puede mencionar nada fuera de ese contexto.

Cualquier fallo (sin API key configurada, timeout, 429, 5xx, SDK no
instalado, JSON inválido, respuesta vacía) se traduce SIEMPRE a
GeminiNoDisponibleError -- CU29 nunca deja caer el catálogo por esto (ver
service.py: ambas llamadas tienen un fallback sin IA). El detalle interno del
error nunca se expone al Cliente, solo se registra en el log del servidor.

`cliente_gemini`/`generar_con_reintento`/`GeminiNoDisponibleError` son la
única parte de este archivo reutilizada fuera de CU29 -- CU30 (ver
CU30_ConsultarReportesIndicadores/gemini_client.py, "consulta inteligente"
del dashboard del Administrador) las importa tal cual en vez de duplicar la
construcción del cliente y el reintento. El resto (los dos prompts y
interpretar_consulta/generar_respuesta) es exclusivo del asistente/chatbot
de CU29 -- CU30 define sus propios prompts, específicos de reportes, sobre
esta misma base.
"""

import json
import logging
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_MENSAJE = 500
_MAX_TURNOS_HISTORIAL = 6
# Gemini devuelve 503 ("modelo con alta demanda") o 429 (cuota) con cierta
# frecuencia incluso con una clave válida -- son errores transitorios, no de
# configuración. Un único reintento corto absorbe la mayoría sin que el
# Cliente llegue a ver el mensaje de fallback por algo que se resuelve solo
# medio segundo después (ver _con_reintento).
_INTENTOS_MAXIMOS = 2
_ESPERA_ENTRE_INTENTOS_SEGUNDOS = 0.6


class GeminiNoDisponibleError(Exception):
    """Gemini no está configurado, no respondió a tiempo, agotó su cuota, o
    devolvió algo que no se pudo interpretar -- ver router.py/service.py,
    donde SIEMPRE se traduce a un mensaje amigable, nunca a un 500 con
    detalle interno."""


def cliente_gemini():
    """Construye el cliente del SDK -- utilidad base compartida (ver
    docstring del módulo), reutilizada tal cual por CU30."""
    if not settings.GEMINI_API_KEY:
        raise GeminiNoDisponibleError(
            "GEMINI_API_KEY no está configurada -- ver backend/.env.example."
        )
    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover - solo si falta la dependencia
        raise GeminiNoDisponibleError("El SDK de Gemini no está disponible.") from exc
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _formatear_historial(historial: list[dict]) -> str:
    turnos = historial[-_MAX_TURNOS_HISTORIAL:]
    if not turnos:
        return "(sin mensajes previos)"
    lineas = []
    for turno in turnos:
        rol = "Cliente" if turno.get("rol") == "usuario" else "Asistente"
        lineas.append(f"{rol}: {turno.get('texto', '')}")
    return "\n".join(lineas)


_PROMPT_INTERPRETACION = """Eres el módulo de interpretación del asistente virtual de FashionStore, una \
tienda de ropa. Tu única tarea es leer el ÚLTIMO mensaje del cliente (el \
historial es solo contexto) y devolver ÚNICAMENTE un objeto JSON, sin texto \
adicional, sin explicaciones, sin marcado markdown, con EXACTAMENTE esta \
forma:

{{
  "intencion": "busqueda_producto" | "promociones" | "disponibilidad" | "recomendacion_personal" | "conversacion",
  "categoria": string o null,
  "color": string o null,
  "talla": string o null,
  "coleccion": string o null,
  "ciudad": string o null,
  "texto_busqueda": string o null,
  "presupuesto_max": number o null
}}

Reglas:
- Nunca inventes un valor que el cliente no mencionó -- usa null.
- "texto_busqueda" es una palabra clave corta (ej. tipo de prenda) si el \
cliente la mencionó y no encaja en los otros campos.
- "recomendacion_personal" es cuando el cliente pide una sugerencia general \
("qué me recomiendas", "algo parecido a lo que compré").
- "conversacion" es para saludos o mensajes que no piden productos.
- No agregues NINGÚN texto fuera del JSON.

Historial reciente:
{historial}

Último mensaje del cliente:
{mensaje}
"""

_PROMPT_RESPUESTA = """Eres el asistente virtual de FashionStore, una tienda de ropa boliviana. \
Responde en español, de forma breve, cálida y natural (máximo 3 frases, sin \
listas ni markdown). SOLO puedes mencionar los productos, precios, \
promociones y disponibilidad que aparecen en el "Contexto comercial" de \
abajo -- nunca inventes otro producto, precio, talla, color, promoción, \
sucursal o stock que no esté ahí. Si el contexto dice que no se encontraron \
productos, dilo con amabilidad e invita a explorar el catálogo, sin sonar \
como un error técnico.

Historial reciente:
{historial}

Mensaje del cliente:
{mensaje}

Contexto comercial (datos reales y verificados de FashionStore):
{contexto}
"""


def generar_con_reintento(client, **kwargs):
    """`client.models.generate_content` con un reintento corto -- 503 (alta
    demanda) y 429 (cuota) son frecuentes en Gemini incluso con una clave
    válida y suelen resolverse solos medio segundo después. Sin esto, CU29/
    CU30 caerían al fallback por algo transitorio que un segundo intento ya
    resuelve (importante para no verse frágil en una demo en vivo). Utilidad
    base compartida -- ver docstring del módulo."""
    ultimo_error: Exception | None = None
    for intento in range(1, _INTENTOS_MAXIMOS + 1):
        try:
            return client.models.generate_content(**kwargs)
        except Exception as exc:  # noqa: BLE001 - cualquier fallo de red/SDK es candidato a reintento
            ultimo_error = exc
            if intento < _INTENTOS_MAXIMOS:
                logger.info(
                    "CU29 -- Gemini falló (%s), reintentando (%s/%s)...",
                    type(exc).__name__,
                    intento,
                    _INTENTOS_MAXIMOS,
                )
                time.sleep(_ESPERA_ENTRE_INTENTOS_SEGUNDOS)
    raise ultimo_error  # type: ignore[misc]


def interpretar_consulta(mensaje: str, historial: list[dict]) -> dict:
    prompt = _PROMPT_INTERPRETACION.format(
        historial=_formatear_historial(historial), mensaje=mensaje.strip()[:_MAX_MENSAJE]
    )
    client = cliente_gemini()
    try:
        respuesta = generar_con_reintento(
            client,
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json", "temperature": 0.2},
        )
        texto = (respuesta.text or "").strip()
        datos = json.loads(texto)
        if not isinstance(datos, dict):
            raise ValueError("La interpretación de Gemini no fue un objeto JSON.")
        return datos
    except GeminiNoDisponibleError:
        raise
    except Exception as exc:
        logger.warning("CU29 -- Gemini no pudo interpretar la consulta (%s).", type(exc).__name__)
        raise GeminiNoDisponibleError("Gemini no respondió a tiempo.") from exc


def generar_respuesta(mensaje: str, historial: list[dict], contexto: str) -> str:
    prompt = _PROMPT_RESPUESTA.format(
        historial=_formatear_historial(historial),
        mensaje=mensaje.strip()[:_MAX_MENSAJE],
        contexto=contexto or "No se encontraron productos que coincidan con la consulta.",
    )
    client = cliente_gemini()
    try:
        respuesta = generar_con_reintento(
            client,
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={"temperature": 0.4},
        )
        texto = (respuesta.text or "").strip()
        if not texto:
            raise ValueError("Gemini devolvió una respuesta vacía.")
        return texto
    except GeminiNoDisponibleError:
        raise
    except Exception as exc:
        logger.warning("CU29 -- Gemini no pudo generar la respuesta final (%s).", type(exc).__name__)
        raise GeminiNoDisponibleError("Gemini no respondió a tiempo.") from exc
