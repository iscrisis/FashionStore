"""Endpoints de CU03 -- Recuperar contraseña.

Público: NO requiere sesión, igual que CU01 (login) y CU02 (registro), y vive
bajo el mismo prefix "/auth" que ambos por la misma razón (ver
CU01/router.py y CU02/router.py: el caso de uso queda identificado por la
ubicación del código y el tag de OpenAPI, no por la URL).

Ambos endpoints son deliberadamente "opacos" para no permitir enumerar
cuentas: /forgot-password siempre responde 200 con el mismo mensaje genérico
exista o no el correo (ver service.solicitar, que no distingue el caso), y
/reset-password solo informa si el token es válido o no -- nunca por qué
(expirado, ya usado o inexistente son indistinguibles desde afuera).

Respuestas JSON neutras (sin HTML, sin redirecciones): Angular hoy y Flutter
más adelante consumen exactamente el mismo contrato REST (ver CU01/router.py,
mismo criterio ya aplicado ahí).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from .schemas import ForgotPasswordRequest, MensajeGenericoResponse, ResetPasswordRequest
from .service import PasswordResetService, TokenInvalidoError

router = APIRouter(prefix="/auth", tags=["CU03 - Recuperar contraseña"])

_MENSAJE_SOLICITUD = (
    "Si existe una cuenta asociada a ese correo, recibirás instrucciones para "
    "restablecer tu contraseña."
)


@router.post("/forgot-password", response_model=MensajeGenericoResponse)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> MensajeGenericoResponse:
    PasswordResetService(db).solicitar(payload.correo)
    return MensajeGenericoResponse(message=_MENSAJE_SOLICITUD)


@router.post("/reset-password", response_model=MensajeGenericoResponse)
def reset_password(
    payload: ResetPasswordRequest, db: Session = Depends(get_db)
) -> MensajeGenericoResponse:
    try:
        PasswordResetService(db).restablecer(payload.token, payload.new_password)
    except TokenInvalidoError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "El enlace no es válido o ya expiró. Solicita uno nuevo.",
        ) from exc
    return MensajeGenericoResponse(message="Tu contraseña se actualizó correctamente.")
