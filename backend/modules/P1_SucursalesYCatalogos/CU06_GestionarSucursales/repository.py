"""Acceso a datos de Ciudad y Sucursal necesario para CU06.

Consulta los mismos modelos que expone modules/P1_SucursalesYCatalogos/Models;
no crea tablas ni modelos paralelos.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal


class CiudadesRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, is_active: bool | None = None) -> list[Ciudad]:
        stmt = select(Ciudad)
        if is_active is not None:
            stmt = stmt.where(Ciudad.is_active == is_active)
        stmt = stmt.order_by(Ciudad.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, ciudad_id: int) -> Ciudad | None:
        return self.db.get(Ciudad, ciudad_id)

    def existe_nombre(self, nombre: str, excluyendo_id: int | None = None) -> bool:
        stmt = select(func.count()).select_from(Ciudad).where(
            func.lower(Ciudad.nombre) == nombre.strip().lower()
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Ciudad.id != excluyendo_id)
        return self.db.execute(stmt).scalar_one() > 0

    def crear(self, ciudad: Ciudad) -> Ciudad:
        self.db.add(ciudad)
        self.db.commit()
        self.db.refresh(ciudad)
        return ciudad

    def guardar(self, ciudad: Ciudad) -> Ciudad:
        self.db.commit()
        self.db.refresh(ciudad)
        return ciudad


class SucursalesRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(
        self,
        search: str | None = None,
        ciudad_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[Sucursal]:
        stmt = select(Sucursal)
        if search:
            patron = f"%{search.strip().lower()}%"
            stmt = stmt.where(func.lower(Sucursal.nombre).like(patron))
        if ciudad_id is not None:
            stmt = stmt.where(Sucursal.ciudad_id == ciudad_id)
        if is_active is not None:
            stmt = stmt.where(Sucursal.is_active == is_active)
        stmt = stmt.order_by(Sucursal.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, sucursal_id: int) -> Sucursal | None:
        return self.db.get(Sucursal, sucursal_id)

    def existe_nombre_en_ciudad(
        self, nombre: str, ciudad_id: int, excluyendo_id: int | None = None
    ) -> bool:
        stmt = select(func.count()).select_from(Sucursal).where(
            Sucursal.ciudad_id == ciudad_id,
            func.lower(Sucursal.nombre) == nombre.strip().lower(),
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Sucursal.id != excluyendo_id)
        return self.db.execute(stmt).scalar_one() > 0

    def crear(self, sucursal: Sucursal) -> Sucursal:
        self.db.add(sucursal)
        self.db.commit()
        self.db.refresh(sucursal)
        return sucursal

    def guardar(self, sucursal: Sucursal) -> Sucursal:
        self.db.commit()
        self.db.refresh(sucursal)
        return sucursal
