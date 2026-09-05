"""Acceso de solo lectura a Ciudad y Sucursal para consulta pública -- CU07.

Lee los mismos modelos que administra CU06 (Ciudad, Sucursal); no los
duplica ni los modifica. Solo devuelve lo que el Administrador ya marcó como
activo.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal


class SucursalesPublicoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_ciudades_activas(self) -> list[Ciudad]:
        stmt = select(Ciudad).where(Ciudad.is_active.is_(True)).order_by(Ciudad.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def listar_sucursales_activas(self, ciudad_id: int | None = None) -> list[Sucursal]:
        stmt = select(Sucursal).where(Sucursal.is_active.is_(True))
        if ciudad_id is not None:
            stmt = stmt.where(Sucursal.ciudad_id == ciudad_id)
        stmt = stmt.order_by(Sucursal.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def obtener_sucursal_activa(self, sucursal_id: int) -> Sucursal | None:
        stmt = select(Sucursal).where(Sucursal.id == sucursal_id, Sucursal.is_active.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()
