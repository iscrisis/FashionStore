"""Repository para CU13 — Queries de operaciones fallidas y auditoría."""

from datetime import datetime
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from modules.P5_ComprasVentasYPagos.Models.venta import Venta
from modules.P4_ReservasYAtencion.Models.reserva import Reserva
from modules.Models.operacion_sincronizacion_log import OperacionSincronizacionLog


class ReintentoRepository:
    """Acceso a datos para CU13."""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================================
    # CONSULTAS: Operaciones fallidas por reintentar
    # ============================================================================

    def obtener_ventas_fallidas(self, empresa_id: int, sucursal_id: int | None = None) -> list[Venta]:
        """Obtener ventas con uuid_operacion_offline pero sin confirmación final (RECHAZADA o CONFLICTO en auditoría)."""
        query = self.db.query(Venta).filter(
            and_(
                Venta.uuid_operacion_offline.isnot(None),
                Venta.empresa_id == empresa_id,
            )
        )

        if sucursal_id:
            query = query.filter(Venta.sucursal_id == sucursal_id)

        return query.all()

    def obtener_reservas_fallidas(self, empresa_id: int, sucursal_id: int | None = None) -> list[Reserva]:
        """Obtener reservas con uuid_operacion_offline pero sin confirmación final."""
        query = self.db.query(Reserva).filter(
            and_(
                Reserva.uuid_operacion_offline.isnot(None),
                Reserva.empresa_id == empresa_id,
            )
        )

        if sucursal_id:
            query = query.filter(Reserva.sucursal_id == sucursal_id)

        return query.all()

    def obtener_venta_por_uuid(self, empresa_id: int, uuid: str) -> Venta | None:
        """Obtener venta por UUID offline, validando empresa."""
        return self.db.query(Venta).filter(
            and_(
                Venta.uuid_operacion_offline == uuid,
                Venta.empresa_id == empresa_id,
            )
        ).first()

    def obtener_reserva_por_uuid(self, empresa_id: int, uuid: str) -> Reserva | None:
        """Obtener reserva por UUID offline, validando empresa."""
        return self.db.query(Reserva).filter(
            and_(
                Reserva.uuid_operacion_offline == uuid,
                Reserva.empresa_id == empresa_id,
            )
        ).first()

    # ============================================================================
    # AUDITORÍA: Registrar intentos
    # ============================================================================

    def registrar_intento(
        self,
        empresa_id: int,
        uuid_operacion: str,
        tipo_operacion: str,  # VENTA_OFFLINE, RESERVA_OFFLINE
        numero_intento: int,
        estado_resultado: str,  # CONFIRMADA, RECHAZADA, CONFLICTO
        motivo: str | None = None,
        error_tipo: str | None = None,
        http_status: int | None = None,
        tiempo_respuesta_ms: int | None = None,
        usuario_id: int | None = None,
    ) -> OperacionSincronizacionLog:
        """Registrar un intento de sincronización en la auditoría."""
        log = OperacionSincronizacionLog(
            empresa_id=empresa_id,
            uuid_operacion_offline=uuid_operacion,
            tipo_operacion=tipo_operacion,
            numero_intento=numero_intento,
            fecha_intento=datetime.utcnow(),
            estado_resultado=estado_resultado,
            motivo=motivo,
            error_tipo=error_tipo,
            http_status=http_status,
            tiempo_respuesta_ms=tiempo_respuesta_ms,
            usuario_id=usuario_id,
        )
        self.db.add(log)
        return log

    def obtener_historial_intento(self, empresa_id: int, uuid_operacion: str) -> list[OperacionSincronizacionLog]:
        """Obtener historial completo de intentos de una operación."""
        return self.db.query(OperacionSincronizacionLog).filter(
            and_(
                OperacionSincronizacionLog.uuid_operacion_offline == uuid_operacion,
                OperacionSincronizacionLog.empresa_id == empresa_id,
            )
        ).order_by(OperacionSincronizacionLog.fecha_intento).all()

    def obtener_ultimo_intento(self, empresa_id: int, uuid_operacion: str) -> OperacionSincronizacionLog | None:
        """Obtener el último intento registrado de una operación."""
        return self.db.query(OperacionSincronizacionLog).filter(
            and_(
                OperacionSincronizacionLog.uuid_operacion_offline == uuid_operacion,
                OperacionSincronizacionLog.empresa_id == empresa_id,
            )
        ).order_by(desc(OperacionSincronizacionLog.fecha_intento)).first()

    def contar_intentos_exitosos(self, empresa_id: int, uuid_operacion: str) -> int:
        """Contar intentos CONFIRMADA para esta operación."""
        return self.db.query(OperacionSincronizacionLog).filter(
            and_(
                OperacionSincronizacionLog.uuid_operacion_offline == uuid_operacion,
                OperacionSincronizacionLog.empresa_id == empresa_id,
                OperacionSincronizacionLog.estado_resultado == "CONFIRMADA",
            )
        ).count()

    def contar_intentos_totales(self, empresa_id: int, uuid_operacion: str) -> int:
        """Contar TODOS los intentos registrados para esta operación."""
        return self.db.query(OperacionSincronizacionLog).filter(
            and_(
                OperacionSincronizacionLog.uuid_operacion_offline == uuid_operacion,
                OperacionSincronizacionLog.empresa_id == empresa_id,
            )
        ).count()
