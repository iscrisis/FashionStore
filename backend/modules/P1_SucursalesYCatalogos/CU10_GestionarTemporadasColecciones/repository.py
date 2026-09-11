"""Acceso a datos de Temporada y Colección necesario para CU10.

Consulta los mismos modelos que expone modules/P1_SucursalesYCatalogos/Models;
no crea tablas ni modelos paralelos.
"""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada


class TemporadasRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, search: str | None = None, is_active: bool | None = None) -> list[Temporada]:
        stmt = select(Temporada)
        if search:
            stmt = stmt.where(func.lower(Temporada.nombre).like(f"%{search.strip().lower()}%"))
        if is_active is not None:
            stmt = stmt.where(Temporada.is_active == is_active)
        stmt = stmt.order_by(Temporada.fecha_inicio.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, temporada_id: int) -> Temporada | None:
        return self.db.get(Temporada, temporada_id)

    def existe_nombre(self, nombre: str, excluyendo_id: int | None = None) -> bool:
        stmt = select(func.count()).select_from(Temporada).where(
            func.lower(Temporada.nombre) == nombre.strip().lower()
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Temporada.id != excluyendo_id)
        return self.db.execute(stmt).scalar_one() > 0

    def crear(self, temporada: Temporada) -> Temporada:
        self.db.add(temporada)
        self.db.commit()
        self.db.refresh(temporada)
        return temporada

    def guardar(self, temporada: Temporada) -> Temporada:
        self.db.commit()
        self.db.refresh(temporada)
        return temporada


class ColeccionesRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(
        self,
        search: str | None = None,
        temporada_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[Coleccion]:
        stmt = select(Coleccion)
        if search:
            stmt = stmt.where(func.lower(Coleccion.nombre).like(f"%{search.strip().lower()}%"))
        if temporada_id is not None:
            stmt = stmt.where(Coleccion.temporada_id == temporada_id)
        if is_active is not None:
            stmt = stmt.where(Coleccion.is_active == is_active)
        stmt = stmt.order_by(Coleccion.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, coleccion_id: int) -> Coleccion | None:
        return self.db.get(Coleccion, coleccion_id)

    def existe_nombre_en_temporada(
        self, nombre: str, temporada_id: int, excluyendo_id: int | None = None
    ) -> bool:
        stmt = select(func.count()).select_from(Coleccion).where(
            Coleccion.temporada_id == temporada_id,
            func.lower(Coleccion.nombre) == nombre.strip().lower(),
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Coleccion.id != excluyendo_id)
        return self.db.execute(stmt).scalar_one() > 0

    def crear(self, coleccion: Coleccion) -> Coleccion:
        self.db.add(coleccion)
        self.db.commit()
        self.db.refresh(coleccion)
        return coleccion

    def guardar(self, coleccion: Coleccion) -> Coleccion:
        self.db.commit()
        self.db.refresh(coleccion)
        return coleccion

    def desmarcar_destacadas(self, excluyendo_id: int) -> None:
        """Pone es_destacada_inicio=False en cualquier otra colección que lo
        tuviera en True, para que al marcar una nueva quede solo una."""
        stmt = (
            update(Coleccion)
            .where(Coleccion.es_destacada_inicio.is_(True), Coleccion.id != excluyendo_id)
            .values(es_destacada_inicio=False)
        )
        self.db.execute(stmt)

    def obtener_destacada_activa(self) -> Coleccion | None:
        stmt = select(Coleccion).where(
            Coleccion.es_destacada_inicio.is_(True), Coleccion.is_active.is_(True)
        )
        return self.db.execute(stmt).scalars().first()
