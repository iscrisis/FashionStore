"""Repositorio de CU12 — Consultar resultados de sincronización."""

from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from modules.P5_ComprasVentasYPagos.Models.venta import Venta
from modules.P4_ReservasYAtencion.Models.reserva import Reserva


class ConsultarResultadoRepository:
    """Consulta resultados persistidos de sincronización en PostgreSQL."""

    def __init__(self, db: Session):
        self.db = db

    def obtener_venta_por_uuid_origen(self, empresa_id: int, uuid_origen: str) -> Venta | None:
        """Obtener venta sincronizada por UUID local.

        Si CU11 la confirmó, Venta.uuid_operacion_offline estará poblado.
        """
        stmt = select(Venta).where(
            and_(
                Venta.empresa_id == empresa_id,
                Venta.uuid_operacion_offline == uuid_origen,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def obtener_reserva_por_uuid_origen(self, empresa_id: int, uuid_origen: str) -> Reserva | None:
        """Obtener reserva sincronizada por UUID local.

        Si CU11 la confirmó, Reserva.uuid_operacion_offline estará poblado.
        """
        stmt = select(Reserva).where(
            and_(
                Reserva.empresa_id == empresa_id,
                Reserva.uuid_operacion_offline == uuid_origen,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def listar_ventas_sincronizadas(
        self,
        empresa_id: int,
        sucursal_id: int | None = None,
    ) -> list[Venta]:
        """Listar ventas que fueron sincronizadas (tienen uuid_operacion_offline)."""
        stmt = select(Venta).where(
            and_(
                Venta.empresa_id == empresa_id,
                Venta.uuid_operacion_offline.isnot(None),
            )
        )
        if sucursal_id:
            stmt = stmt.where(Venta.sucursal_id == sucursal_id)

        return self.db.execute(stmt.order_by(Venta.created_at.desc())).scalars().all()

    def listar_reservas_sincronizadas(
        self,
        empresa_id: int,
        sucursal_id: int | None = None,
    ) -> list[Reserva]:
        """Listar reservas que fueron sincronizadas (tienen uuid_operacion_offline)."""
        stmt = select(Reserva).where(
            and_(
                Reserva.empresa_id == empresa_id,
                Reserva.uuid_operacion_offline.isnot(None),
            )
        )
        if sucursal_id:
            stmt = stmt.where(Reserva.sucursal_id == sucursal_id)

        return self.db.execute(stmt.order_by(Reserva.created_at.desc())).scalars().all()
