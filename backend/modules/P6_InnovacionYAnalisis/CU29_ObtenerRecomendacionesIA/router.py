"""Endpoint de CU29 -- Obtener recomendaciones mediante IA (Cliente/Invitado).

Un único endpoint conversacional: POST /asistente-ia/mensaje. Sin rol
obligatorio -- funciona igual para Invitado (sin token) y para CLIENTE
autenticado (JWT opcional, ver app.core.deps.get_current_usuario_opcional):
el actor se resuelve SIEMPRE del token si existe, nunca de un cliente_id que
Angular pudiera enviar (mismo criterio que CU27).

Angular (y, más adelante, Flutter) NUNCA llaman a Gemini directamente -- este
es el único punto de entrada; ver service.py para el flujo completo
(interpretar -> consultar PostgreSQL -> redactar). El try/except de aquí es
la última red de seguridad: CU29 es consultivo y nunca debe romper la
experiencia del Cliente en el catálogo, así que CUALQUIER fallo interno
(Gemini caído, error inesperado) siempre responde 200 con un mensaje
amigable -- nunca un 500 con detalle interno ni un stack trace.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario_opcional
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import MensajeAsistenteRequest, MensajeAsistenteResponse
from .service import AsistenteIAService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/asistente-ia", tags=["CU29 - Obtener recomendaciones mediante IA"])

_RESPUESTA_FALLBACK = {
    "respuesta": "El asistente no está disponible en este momento. Puedes seguir explorando nuestro catálogo.",
    "productos": [],
    "tipo": "fallback",
    "hay_mas_resultados": False,
}


@router.post("/mensaje", response_model=MensajeAsistenteResponse)
def enviar_mensaje(
    payload: MensajeAsistenteRequest,
    db: Session = Depends(get_db),
    actor: Usuario | None = Depends(get_current_usuario_opcional),
) -> MensajeAsistenteResponse:
    try:
        resultado = AsistenteIAService(db).responder(payload, actor)
    except Exception:
        logger.exception("CU29 -- fallo inesperado al responder el mensaje del asistente.")
        resultado = _RESPUESTA_FALLBACK
    return MensajeAsistenteResponse(**resultado)
