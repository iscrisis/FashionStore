"""Acceso a datos de Usuario necesario para CU05 — Gestionar usuarios y roles.

Consulta el mismo modelo Usuario que usa CU01 (modules/P2_UsuariosYAccesos/Models);
no crea una segunda tabla ni un modelo paralelo. Las consultas son distintas a las
de CU01 (listado con filtros vs. búsqueda puntual por correo), por eso vive en su
propio repository.py, igual que ya hace CU01.

También consulta Sucursal y Proveedor (modules/P1_SucursalesYCatalogos/Models)
solo para validar sucursal_id/proveedor_id al crear/editar una cuenta — no los
duplica ni los administra.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
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
        # El Administrador General queda siempre fuera de CU05, sin importar los
        # filtros solicitados (ver también obtener() en service.py).
        stmt = select(Usuario).where(Usuario.rol != RolUsuario.ADMINISTRADOR)
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

    def get_sucursal(self, sucursal_id: int) -> Sucursal | None:
        return self.db.get(Sucursal, sucursal_id)

    def get_proveedor(self, proveedor_id: int) -> Proveedor | None:
        return self.db.get(Proveedor, proveedor_id)

    def proveedor_ya_vinculado(self, proveedor_id: int, excluyendo_usuario_id: int | None = None) -> bool:
        stmt = select(func.count()).select_from(Usuario).where(Usuario.proveedor_id == proveedor_id)
        if excluyendo_usuario_id is not None:
            stmt = stmt.where(Usuario.id != excluyendo_usuario_id)
        return self.db.execute(stmt).scalar_one() > 0

    def crear(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def guardar(self, usuario: Usuario) -> Usuario:
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
