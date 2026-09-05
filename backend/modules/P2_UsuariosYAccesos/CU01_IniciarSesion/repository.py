"""Acceso a datos de Usuario necesario para CU01 — Iniciar sesión."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_correo(self, correo: str) -> Usuario | None:
        stmt = select(Usuario).where(Usuario.correo == correo)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)
