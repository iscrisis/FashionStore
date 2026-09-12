"""Envío de correos reales vía SMTP estándar.

Usa smtplib/email de la librería estándar de Python -- no agrega ninguna
dependencia nueva al proyecto. No pertenece a ningún caso de uso específico:
CU03 (recuperar contraseña) es su primer consumidor, pero cualquier
notificación futura por correo reutilizará esta misma función, igual criterio
que app/core/security.py con el hashing y el JWT.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class EnvioCorreoError(Exception):
    """El correo no pudo enviarse (SMTP no configurado o falló el envío)."""


def enviar_correo(destinatario: str, asunto: str, cuerpo_html: str, cuerpo_texto: str) -> None:
    if not settings.MAIL_HOST or not settings.MAIL_FROM:
        raise EnvioCorreoError(
            "SMTP no está configurado: definir MAIL_HOST y MAIL_FROM (ver .env.example)."
        )

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = settings.MAIL_FROM
    mensaje["To"] = destinatario
    mensaje.set_content(cuerpo_texto)
    mensaje.add_alternative(cuerpo_html, subtype="html")

    try:
        with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT, timeout=10) as smtp:
            if settings.MAIL_USE_TLS:
                smtp.starttls()
            if settings.MAIL_USERNAME:
                smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            smtp.send_message(mensaje)
    except (OSError, smtplib.SMTPException) as exc:
        # No se registra MAIL_PASSWORD ni el cuerpo del correo -- solo que el
        # envío falló, para que un admin note un SMTP mal configurado.
        logger.error("No se pudo enviar el correo a través de SMTP (%s).", type(exc).__name__)
        raise EnvioCorreoError("No se pudo enviar el correo.") from exc
