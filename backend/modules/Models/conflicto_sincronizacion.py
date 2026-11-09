"""Modelo de auditoría para CU14 — Registro de conflictos de sincronización."""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class ConflictoSincronizacion(Base):
    """Registro de conflictos detectados durante la sincronización.

    Permite rastrear:
    - Tipo de conflicto (stock insuficiente, variante no disponible, etc.)
    - UUID de la operación original
    - Estado de resolución (DETECTADO, RESUELTO, DESCARTADO, PENDIENTE_MANUAL)
    - Detalles del conflicto para tomar decisiones
    """

    __tablename__ = "conflictos_sincronizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identifiers
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    uuid_operacion_offline: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tipo_operacion: Mapped[str] = mapped_column(String(50), nullable=False)  # VENTA_OFFLINE, RESERVA_OFFLINE

    # Conflict Classification
    tipo_conflicto: Mapped[str] = mapped_column(String(100), nullable=False)  # STOCK_INSUFICIENTE, VARIANTE_NO_DISPONIBLE, etc.
    estado_conflicto: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DETECTADO"
    )  # DETECTADO, RESUELTO, DESCARTADO, PENDIENTE_MANUAL

    # Details for resolution decision
    motivo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    detalles_conflicto: Mapped[str | None] = mapped_column(String(2000), nullable=True)  # JSON con detalles técnicos

    # Operational context
    fecha_detectado: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_resolucion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usuario_resolucion_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Usuario que resolvió el conflicto

    # Prevention of automatic retries
    debe_reintentarse_automaticamente: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # CU13 debe consultar esto

    def __repr__(self) -> str:
        return (
            f"<ConflictoSincronizacion uuid={self.uuid_operacion_offline} "
            f"tipo={self.tipo_conflicto} estado={self.estado_conflicto}>"
        )

    # Composite indices for fast queries
    __table_args__ = (
        Index("idx_uuid_empresa_cu14", "uuid_operacion_offline", "empresa_id"),
        Index("idx_empresa_estado_cu14", "empresa_id", "estado_conflicto"),
        Index("idx_empresa_tipo_cu14", "empresa_id", "tipo_conflicto"),
        Index("idx_empresa_fecha_cu14", "empresa_id", "fecha_detectado"),
    )
