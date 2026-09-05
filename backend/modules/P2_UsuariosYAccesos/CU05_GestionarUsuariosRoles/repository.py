"""Acceso a datos de Usuario necesario para CU05 — Gestionar usuarios y roles.

Consulta el mismo modelo Usuario que usa CU01 (modules/P2_UsuariosYAccesos/Models);
no crea una segunda tabla ni un modelo paralelo. Las consultas son distintas a las
de CU01 (listado con filtros vs. búsqueda puntual por correo), por eso vive en su
propio repository.py, igual que ya hace CU01.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


class UsuariosRolesRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(
        self,
        search: str | None = None,
        rol: RolUsuario | None = None,
        is_active: bool | None = None,
    ) -> list[Usuario]:
        stmt = select(Usuario)
        if search:
            patron = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                func.lower(Usuario.nombre).like(patron) | func.lower(Usuario.correo).like(patron)
            )
        if rol is not None:
            stmt = stmt.where(Usuario.rol == rol)
        if is_active is not None:
            stmt = stmt.where(Usuario.is_active == is_active)
        stmt = stmt.order_by(Usuario.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)

    def get_by_correo(self, correo: str) -> Usuario | None:
        stmt = select(Usuario).where(Usuario.correo == correo)
        return self.db.execute(stmt).scalar_one_or_none()

    def contar_administradores_activos(self, excluyendo_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Usuario).where(
            Usuario.rol == RolUsuario.ADMINISTRADOR, Usuario.is_active.is_(True)
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Usuario.id != excluyendo_id)
        return self.db.execute(stmt).scalar_one()

    def crear(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def guardar(self, usuario: Usuario) -> Usuario:
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
