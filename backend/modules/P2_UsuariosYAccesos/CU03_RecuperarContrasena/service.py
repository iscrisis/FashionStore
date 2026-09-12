"""Reglas de negocio de CU03 -- Recuperar contraseña.

Flujo:
  1) solicitar(correo): si existe una cuenta ACTIVA con ese correo, genera un
     token aleatorio criptográficamente seguro (secrets.token_urlsafe), guarda
     solo su hash SHA-256 (nunca el token en claro) junto con su expiración, y
     envía el correo con el enlace. Si el correo no existe, la cuenta está
     inactiva, o el envío de correo falla, este método simplemente no hace
     nada más -- nunca lanza ni informa cuál fue el caso (ver router.py, que
     por eso siempre responde el mismo mensaje genérico sin importar qué pasó
     aquí adentro; así no se puede enumerar cuentas).
  2) restablecer(token, password): valida el token contra su hash, revisa
     expiración y uso previo, aplica hash_password (la MISMA función que ya
     usan CU01/CU02/CU05 -- no se duplica el hashing) y marca el token usado
     para que no vuelva a servir.

No crea otro sistema de usuarios ni otra autenticación: reutiliza el modelo
Usuario y UsuarioRepository de CU01 tal cual.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.integrations.mailer import EnvioCorreoError, enviar_correo
from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.repository import UsuarioRepository
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .repository import PasswordResetRepository

logger = logging.getLogger(__name__)

_TOKEN_NBYTES = 32  # secrets.token_urlsafe(32) -> ~43 caracteres, entropía de sobra.


class TokenInvalidoError(Exception):
    """Token inexistente, expirado o ya utilizado (indistinguibles hacia afuera)."""


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class PasswordResetService:
    def __init__(self, db: Session):
        self._usuarios = UsuarioRepository(db)
        self._repo = PasswordResetRepository(db)

    def solicitar(self, correo: str) -> None:
        usuario = self._usuarios.get_by_correo(correo)
        if usuario is None or not usuario.is_active:
            return

        token_plano = secrets.token_urlsafe(_TOKEN_NBYTES)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )
        self._repo.crear_token(usuario.id, _hash_token(token_plano), expires_at)

        enlace = f"{settings.FRONTEND_URL.rstrip('/')}/restablecer-contrasena?token={token_plano}"
        self._enviar_correo_recuperacion(usuario, enlace)

    def restablecer(self, token: str, nueva_password: str) -> None:
        registro = self._repo.get_token_por_hash(_hash_token(token))

        ahora = datetime.now(timezone.utc)
        if registro is None or registro.used_at is not None or registro.expires_at < ahora:
            raise TokenInvalidoError

        usuario = self._usuarios.get_by_id(registro.usuario_id)
        if usuario is None or not usuario.is_active:
            raise TokenInvalidoError

        usuario.password_hash = hash_password(nueva_password)
        self._repo.guardar_usuario(usuario)
        self._repo.marcar_token_usado(registro)

    def _enviar_correo_recuperacion(self, usuario: Usuario, enlace: str) -> None:
        minutos = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        asunto = "Restablece tu contraseña - FashionStore"
        cuerpo_texto = (
            f"Hola {usuario.nombre},\n\n"
            "Recibimos una solicitud para restablecer tu contraseña de FashionStore.\n"
            f"Abre este enlace para elegir una nueva contraseña (válido por {minutos} minutos):\n\n"
            f"{enlace}\n\n"
            "Si no solicitaste esto, puedes ignorar este correo: tu contraseña actual sigue funcionando."
        )
        cuerpo_html = f"""\
<div style="font-family: Arial, Helvetica, sans-serif; color: #191919; max-width: 480px; margin: 0 auto;">
  <h2 style="color: #a90012; margin-bottom: 4px;">FashionStore</h2>
  <p>Hola {usuario.nombre},</p>
  <p>Recibimos una solicitud para restablecer tu contraseña.</p>
  <p style="text-align: center; margin: 28px 0;">
    <a href="{enlace}"
       style="background:#a90012; color:#ffffff; padding:12px 24px; border-radius:6px;
              text-decoration:none; font-weight:bold; display:inline-block;">
      Restablecer contraseña
    </a>
  </p>
  <p style="color:#666666; font-size:13px;">
    Este enlace vence en {minutos} minutos y solo puede usarse una vez.
    Si no solicitaste este cambio, puedes ignorar este correo: tu contraseña actual sigue funcionando.
  </p>
</div>
"""
        try:
            enviar_correo(usuario.correo, asunto, cuerpo_html, cuerpo_texto)
        except EnvioCorreoError:
            # No se re-lanza: el llamador (router) siempre responde el mismo
            # mensaje genérico exista o no la cuenta, así que un fallo de SMTP
            # tampoco debe filtrarse hacia afuera -- pero sí queda en logs
            # para que un admin note que el correo no está llegando de verdad.
            logger.error("Token de recuperación generado pero el correo no pudo enviarse.")
