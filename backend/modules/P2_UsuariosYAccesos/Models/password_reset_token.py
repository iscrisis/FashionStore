"""Token temporal de un solo uso para CU03 -- Recuperar contraseña.

Vive en una tabla separada, no en Usuario: su ciclo de vida es efímero y
desacoplado del usuario (puede haber cero o varios tokens históricos por
cuenta, y ninguno de sus campos pertenece a la identidad del usuario en sí).

Solo se guarda el hash SHA-256 del token (ver CU03_RecuperarContrasena/
service.py), nunca el token en texto plano -- el valor real solo existe en el
enlace del correo y en memoria mientras se procesa la solicitud, igual
criterio que password_hash en Usuario (que tampoco guarda la contraseña en
claro).

No reutiliza JWT: un JWT es intencionalmente stateless (no se puede invalidar
del lado servidor sin una lista de revocación aparte), pero este token debe
poder invalidarse en el momento exacto en que se usa (un solo uso) -- eso
exige estado en base de datos de todas formas, así que un token aleatorio
opaco (secrets.token_urlsafe) más esta tabla es la solución más simple que ya
cumple el requisito, sin duplicar la infraestructura JWT de CU01.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
