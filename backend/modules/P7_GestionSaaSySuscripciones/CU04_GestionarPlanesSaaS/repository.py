"""Repository de CU04 — Acceso a datos de planes SaaS."""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
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


class SuscripcionesRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_empresa(self, empresa_id: int) -> Suscripcion | None:
        """Obtiene la suscripción activa de una empresa."""
        stmt = select(Suscripcion).where(
            Suscripcion.empresa_id == empresa_id,
            Suscripcion.activa == True,
        ).order_by(Suscripcion.fecha_vencimiento.desc())
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, suscripcion_id: int) -> Suscripcion | None:
        """Obtiene una suscripción por ID."""
        return self._db.get(Suscripcion, suscripcion_id)

    def listar_por_empresa(self, empresa_id: int) -> list[Suscripcion]:
        """Lista todas las suscripciones de una empresa."""
        stmt = select(Suscripcion).where(
            Suscripcion.empresa_id == empresa_id
        ).order_by(Suscripcion.fecha_vencimiento.desc())
        return list(self._db.execute(stmt).scalars().all())

    def crear(self, suscripcion: Suscripcion) -> Suscripcion:
        """Crea una nueva suscripción."""
        self._db.add(suscripcion)
        self._db.commit()
        self._db.refresh(suscripcion)
        return suscripcion

    def guardar(self, suscripcion: Suscripcion) -> Suscripcion:
        """Guarda cambios en una suscripción."""
        self._db.commit()
        self._db.refresh(suscripcion)
        return suscripcion

    def eliminar(self, suscripcion: Suscripcion) -> None:
        """Elimina una suscripción."""
        self._db.delete(suscripcion)
        self._db.commit()

    def listar_por_plan(self, plan_id: int) -> list[Suscripcion]:
        """Lista todas las suscripciones de un plan."""
        stmt = select(Suscripcion).where(
            Suscripcion.plan_id == plan_id
        ).order_by(Suscripcion.fecha_vencimiento.desc())
        return list(self._db.execute(stmt).scalars().all())

    def contar_por_plan(self, plan_id: int) -> int:
        """Cuenta suscripciones de un plan."""
        stmt = select(func.count()).select_from(Suscripcion).where(
            Suscripcion.plan_id == plan_id
        )
        return self._db.execute(stmt).scalar_one()

    def contar_activas_por_plan(self, plan_id: int) -> int:
        """Cuenta suscripciones activas de un plan."""
        stmt = select(func.count()).select_from(Suscripcion).where(
            Suscripcion.plan_id == plan_id,
            Suscripcion.activa == True,
        )
        return self._db.execute(stmt).scalar_one()

    def contar_empresas_por_plan(self, plan_id: int) -> int:
        """Cuenta empresas únicas suscritas a un plan."""
        stmt = select(func.count(func.distinct(Suscripcion.empresa_id))).select_from(Suscripcion).where(
            Suscripcion.plan_id == plan_id
        )
        return self._db.execute(stmt).scalar_one()
