"""Integración con OpenRouter API (LLM agnóstico) para CU30 consulta inteligente.

OpenRouter proporciona una API compatible con OpenAI, permitiendo usar múltiples
modelos (incluyendo modelos gratuitos como Llama, Mistral, etc.) sin tarjeta de crédito.

Reutiliza los prompts y esquema de respuesta de Gemini, adaptando solo la
integración HTTP al endpoint `/chat/completions` de OpenRouter.

Mismo criterio de manejo de errores: cualquier fallo -> GeminiNoDisponibleError
(nombre genérico para "IA no disponible", usado por ambos proveedores).
"""

import json
import logging
import time

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_CONSULTA = 300
_INTENTOS_MAXIMOS = 2
_ESPERA_ENTRE_INTENTOS_SEGUNDOS = 0.6
_TIMEOUT_SEGUNDOS = 30

# Reutilizar la excepción de CU29
from modules.P6_InnovacionYAnalisis.CU29_ObtenerRecomendacionesIA.gemini_client import (
    GeminiNoDisponibleError,
)


def cliente_openrouter():
    """Verifica que OpenRouter esté configurado correctamente."""
    if not settings.OPENROUTER_API_KEY:
        raise GeminiNoDisponibleError("OPENROUTER_API_KEY no está configurada.")
    if not settings.OPENROUTER_MODEL:
        raise GeminiNoDisponibleError("OPENROUTER_MODEL no está configurada.")
    if not settings.OPENROUTER_BASE_URL:
        raise GeminiNoDisponibleError("OPENROUTER_BASE_URL no está configurada.")


def generar_con_reintento_openrouter(prompt: str, response_format: str | None = None) -> str:
    """
    Llamada a OpenRouter con reintentos cortos.

    Args:
        prompt: El texto completo del prompt (ya formateado)
        response_format: "json_object" para JSON, None para texto libre

    Returns:
        Texto de respuesta del modelo

    Raises:
        GeminiNoDisponibleError: Si falla después de todos los reintentos
    """
    cliente_openrouter()  # Verificar configuración

    ultimo_error: Exception | None = None

    for intento in range(1, _INTENTOS_MAXIMOS + 1):
        try:
            # Endpoint de OpenRouter compatible con OpenAI
            url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"

            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://fashionstore.ai",  # Requerido por OpenRouter
                "X-Title": "FashionStore-Reports",
            }

            payload = {
                "model": settings.OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # Bajo para interpretación determinista
                "max_tokens": 1000,
                "timeout": _TIMEOUT_SEGUNDOS,
            }

            # JSON response si aplica
            if response_format == "json_object":
                payload["response_format"] = {"type": "json_object"}

            # Realizar request con timeout
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=_TIMEOUT_SEGUNDOS,
            )

            # Verificar status HTTP
            if response.status_code != 200:
                raise Exception(
                    f"OpenRouter HTTP {response.status_code}: {response.text[:200]}"
                )

            # Extraer respuesta
            data = response.json()
            if not data.get("choices") or not data["choices"][0].get("message"):
                raise ValueError("Respuesta incompleta de OpenRouter")

            texto = data["choices"][0]["message"]["content"].strip()
            if not texto:
                raise ValueError("OpenRouter devolvió contenido vacío")

            return texto

        except Exception as exc:
            ultimo_error = exc
            if intento < _INTENTOS_MAXIMOS:
                logger.info(
                    "[CU30/OpenRouter] Intento %d falló (%s), reintentando...",
                    intento,
                    type(exc).__name__,
                )
                time.sleep(_ESPERA_ENTRE_INTENTOS_SEGUNDOS)

    # Agotados los reintentos
    exc_type = type(ultimo_error).__name__
    exc_msg = str(ultimo_error)[:150]
    logger.warning(
        "[CU30/OpenRouter] Falló después de %d intentos: %s - %s",
        _INTENTOS_MAXIMOS,
        exc_type,
        exc_msg,
    )
    raise GeminiNoDisponibleError(f"OpenRouter no respondió a tiempo: {exc_type}") from ultimo_error


def interpretar_consulta_reporte_openrouter(consulta: str, prompt_template: str) -> dict:
    """
    Interpreta la consulta del Administrador usando OpenRouter.

    Args:
        consulta: Texto de la consulta (ej. "Ventas de este mes")
        prompt_template: Plantilla del prompt con {consulta}

    Returns:
        Dict con intencion, sucursal, periodo, etc.

    Raises:
        GeminiNoDisponibleError: Si falla
    """
    try:
        prompt = prompt_template.format(consulta=consulta.strip()[:_MAX_CONSULTA])
    except KeyError:
        # Si ya está formateado parcialmente, usar tal cual
        prompt = prompt_template

    try:
        texto = generar_con_reintento_openrouter(prompt, response_format="json_object")
        datos = json.loads(texto)
        if not isinstance(datos, dict):
            raise ValueError("La respuesta no fue un objeto JSON")
        return datos
    except GeminiNoDisponibleError:
        raise
    except Exception as exc:
        logger.warning(
            "[CU30/OpenRouter] Interpretación falló: %s - %s",
            type(exc).__name__,
            str(exc)[:150],
        )
        raise GeminiNoDisponibleError("OpenRouter no pudo interpretar la consulta") from exc


def generar_resumen_reporte_openrouter(contexto: str, prompt_template: str) -> str:
    """
    Genera un resumen natural de los datos del reporte usando OpenRouter.

    Args:
        contexto: Contexto de datos (ej. "Ventas totales: 1500. Ingresos: Bs 50000")
        prompt_template: Plantilla del prompt con {contexto}

    Returns:
        Resumen en lenguaje natural

    Raises:
        GeminiNoDisponibleError: Si falla
    """
    try:
        prompt = prompt_template.format(contexto=contexto)
    except KeyError:
        # Si ya está formateado, usar tal cual
        prompt = prompt_template

    try:
        texto = generar_con_reintento_openrouter(prompt, response_format=None)
        if not texto:
            raise ValueError("OpenRouter devolvió resumen vacío")
        return texto
    except GeminiNoDisponibleError:
        raise
    except Exception as exc:
        logger.warning(
            "[CU30/OpenRouter] Generación de resumen falló: %s - %s",
            type(exc).__name__,
            str(exc)[:150],
        )
        raise GeminiNoDisponibleError("OpenRouter no pudo generar el resumen") from exc
