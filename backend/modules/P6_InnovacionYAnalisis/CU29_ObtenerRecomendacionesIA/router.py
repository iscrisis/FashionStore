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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario_opcional
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import MensajeAsistenteRequest, MensajeAsistenteResponse
from .service import AsistenteIAService
from modules.P7_GestionSaaSySuscripciones.CU05_GestionarSuscripcionEmpresa.service import (
    CapacidadesEmpresa,
    FuncionalidadNoHabilitadaError,
)

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
        # CU05: Validar que la empresa del usuario tenga acceso a reportes generativos con IA.
        # El asistente IA es una funcionalidad de reportes generativos.
        if actor and actor.empresa_id:
            capacidades = CapacidadesEmpresa(db, actor.empresa_id)
            capacidades.validar_acceso_a("reportes_generativos_ia")

        resultado = AsistenteIAService(db).responder(payload, actor)
    except FuncionalidadNoHabilitadaError as exc:
        # Si la funcionalidad no está habilitada, rechazar con 403.
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "La funcionalidad de asistente IA no está disponible en tu plan."
        ) from exc
    except Exception:
        logger.exception("CU29 -- fallo inesperado al responder el mensaje del asistente.")
        resultado = _RESPUESTA_FALLBACK
    return MensajeAsistenteResponse(**resultado)
