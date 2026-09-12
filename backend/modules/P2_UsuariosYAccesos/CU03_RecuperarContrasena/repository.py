"""Acceso a datos propio de CU03 -- Recuperar contraseña: el token temporal
(password_reset_tokens) y el guardado del nuevo password_hash.

La búsqueda de Usuario por correo/id se reutiliza tal cual de CU01
(UsuarioRepository, ver service.py) -- no se duplica aquí ni se crea una
tabla paralela de usuarios.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.password_reset_token import PasswordResetToken
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


class PasswordResetRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_token(
        self, usuario_id: int, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        token = PasswordResetToken(usuario_id=usuario_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_token_por_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def marcar_token_usado(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        self.db.commit()

    def guardar_usuario(self, usuario: Usuario) -> Usuario:
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
