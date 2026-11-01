"""Repository de CU04 — Acceso a datos de planes SaaS."""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from modules.P7_GestionSaaSySuscripciones.Models.plan import Plan
from modules.P7_GestionSaaSySuscripciones.Models.suscripcion import Suscripcion


class PlanesRepository:
    def __init__(self, db: Session):
        self._db = db

    def listar(self, is_active: bool | None = None) -> list[Plan]:
        """Lista planes, opcionalmente filtrados por estado."""
        stmt = select(Plan)
        if is_active is not None:
            stmt = stmt.where(Plan.is_active == is_active)
        stmt = stmt.order_by(Plan.nombre)
        return list(self._db.execute(stmt).scalars().all())

    def get_by_id(self, plan_id: int) -> Plan | None:
        """Obtiene un plan por ID."""
        return self._db.get(Plan, plan_id)

    def get_by_slug(self, slug: str) -> Plan | None:
        """Obtiene un plan por slug."""
        stmt = select(Plan).where(Plan.slug == slug.strip().lower())
        return self._db.execute(stmt).scalar_one_or_none()

    def existe_nombre(self, nombre: str, excluyendo_id: int | None = None) -> bool:
        """Verifica si existe un plan con ese nombre."""
        stmt = select(func.count()).select_from(Plan).where(
            func.lower(Plan.nombre) == nombre.strip().lower()
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Plan.id != excluyendo_id)
        return self._db.execute(stmt).scalar_one() > 0

    def existe_slug(self, slug: str, excluyendo_id: int | None = None) -> bool:
        """Verifica si existe un plan con ese slug."""
        stmt = select(func.count()).select_from(Plan).where(
            func.lower(Plan.slug) == slug.strip().lower()
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Plan.id != excluyendo_id)
        return self._db.execute(stmt).scalar_one() > 0

    def crear(self, plan: Plan) -> Plan:
        """Crea un nuevo plan."""
        self._db.add(plan)
        self._db.commit()
        self._db.refresh(plan)
        return plan

    def guardar(self, plan: Plan) -> Plan:
        """Guarda cambios en un plan existente."""
        self._db.commit()
        self._db.refresh(plan)
        return plan

    def eliminar(self, plan: Plan) -> None:
        """Elimina un plan (marca como inactivo)."""
        self._db.delete(plan)
        self._db.commit()

    def tiene_suscripciones_activas(self, plan_id: int) -> bool:
        """Verifica si un plan tiene suscripciones activas."""
        stmt = select(func.count()).select_from(Suscripcion).where(
            Suscripcion.plan_id == plan_id,
            Suscripcion.activa == True,
        )
        return self._db.execute(stmt).scalar_one() > 0
