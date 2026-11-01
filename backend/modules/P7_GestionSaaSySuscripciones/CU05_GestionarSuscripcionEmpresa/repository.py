"""Repository de CU05 — Acceso a datos de suscripciones."""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from modules.P7_GestionSaaSySuscripciones.Models.suscripcion import Suscripcion


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
