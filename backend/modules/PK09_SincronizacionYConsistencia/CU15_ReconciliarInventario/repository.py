"""Repository para CU15 — Reconciliar inventario."""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)


class ReconciliacionInventarioRepository:
    """CRUD e queries para reconciliación de inventario."""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================================
    # CONSULTAS: Operaciones offline confirmadas
    # ============================================================================

    def obtener_venta_offline_confirmada(self, empresa_id: int, uuid_operacion: str):
        """Obtener venta offline confirmada por UUID."""
        from modules.Models.venta import Venta

        return self.db.query(Venta).filter(
            and_(
                Venta.empresa_id == empresa_id,
                Venta.uuid_operacion_offline == uuid_operacion,
                Venta.estado == "CONFIRMADA",
            )
        ).first()

    def obtener_reserva_offline_confirmada(self, empresa_id: int, uuid_operacion: str):
        """Obtener reserva offline confirmada por UUID."""
        from modules.Models.reserva import Reserva

        return self.db.query(Reserva).filter(
            and_(
                Reserva.empresa_id == empresa_id,
                Reserva.uuid_operacion_offline == uuid_operacion,
                Reserva.estado == "CONFIRMADA",
            )
        ).first()

    def obtener_detalles_venta(self, venta_id: int):
        """Obtener detalles de venta (cantidades por variante)."""
        from modules.Models.venta_detalle import VentaDetalle

        return self.db.query(VentaDetalle).filter(
            VentaDetalle.venta_id == venta_id
        ).all()

    def obtener_detalles_reserva(self, reserva_id: int):
        """Obtener detalles de reserva (cantidades por variante)."""
        from modules.Models.reserva_detalle import ReservaDetalle

        return self.db.query(ReservaDetalle).filter(
            ReservaDetalle.reserva_id == reserva_id
        ).all()

    # ============================================================================
    # CONSULTAS: Stock actual
    # ============================================================================

    def obtener_stock_sucursal(self, sucursal_id: int, producto_variante_id: int):
        """Obtener stock actual de una variante en una sucursal."""
        from modules.Models.stock_sucursal import StockSucursal

        return self.db.query(StockSucursal).filter(
            and_(
                StockSucursal.sucursal_id == sucursal_id,
                StockSucursal.producto_variante_id == producto_variante_id,
            )
        ).first()

    # ============================================================================
    # CONSULTAS: Evidencia de movimientos
    # ============================================================================

    def obtener_movimiento_por_venta(self, venta_id: int, producto_variante_id: int):
        """Verificar si existe movimiento registrado para una venta."""
        from modules.Models.movimiento_inventario import MovimientoInventario

        return self.db.query(MovimientoInventario).filter(
            and_(
                MovimientoInventario.motivo.like(f"%venta_{venta_id}%"),
                MovimientoInventario.producto_variante_id == producto_variante_id,
            )
        ).first()

    def obtener_movimiento_por_reserva(self, reserva_id: int, producto_variante_id: int):
        """Verificar si existe movimiento registrado para una reserva."""
        from modules.Models.movimiento_inventario import MovimientoInventario

        return self.db.query(MovimientoInventario).filter(
            and_(
                MovimientoInventario.motivo.like(f"%reserva_{reserva_id}%"),
                MovimientoInventario.producto_variante_id == producto_variante_id,
            )
        ).first()

    # ============================================================================
    # CONSULTAS: Auditoría de reconciliaciones
    # ============================================================================

    def obtener_reconciliaciones_operacion(self, empresa_id: int, uuid_operacion: str):
        """Obtener historial de reconciliaciones de una operación (para idempotencia)."""
        from modules.Models.reconciliacion_inventario import ReconciliacionInventario

        return self.db.query(ReconciliacionInventario).filter(
            and_(
                ReconciliacionInventario.empresa_id == empresa_id,
                ReconciliacionInventario.uuid_operacion_offline == uuid_operacion,
            )
        ).order_by(ReconciliacionInventario.fecha_reconciliacion.desc()).all()

    def registrar_reconciliacion(
        self,
        empresa_id: int,
        sucursal_id: int,
        uuid_operacion: str,
        tipo_operacion: str,
        estado_general: str,
        detalles_json: str,
        motivo: Optional[str] = None,
    ):
        """Registrar resultado de reconciliación en auditoría."""
        from modules.Models.reconciliacion_inventario import ReconciliacionInventario
        from datetime import datetime

        reconciliacion = ReconciliacionInventario(
            empresa_id=empresa_id,
            sucursal_id=sucursal_id,
            uuid_operacion_offline=uuid_operacion,
            tipo_operacion=tipo_operacion,
            estado_general=estado_general,
            detalles_json=detalles_json,
            motivo_inconsistencia=motivo,
            fecha_reconciliacion=datetime.utcnow(),
        )
        self.db.add(reconciliacion)
        return reconciliacion
