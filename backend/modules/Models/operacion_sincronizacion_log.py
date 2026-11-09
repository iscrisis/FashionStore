"""Modelo de auditoría para CU13 — Registro de intentos de sincronización."""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class OperacionSincronizacionLog(Base):
    """Registro de auditoría de cada intento de sincronización de operación offline.

    Permite rastrear:
    - Número de intentos
    - Fecha de cada intento
    - Estado resultado (CONFIRMADA, RECHAZADA, CONFLICTO)
    - Error HTTP y tipo de error
    - Tiempo de respuesta
    """

    __tablename__ = "operaciones_sincronizacion_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identifiers
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    uuid_operacion_offline: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tipo_operacion: Mapped[str] = mapped_column(String(50), nullable=False)  # VENTA_OFFLINE, RESERVA_OFFLINE

    # Intento
    numero_intento: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    fecha_intento: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Resultado
    estado_resultado: Mapped[str] = mapped_column(String(20), nullable=False)  # CONFIRMADA, RECHAZADA, CONFLICTO
    motivo: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Error (si aplica)
    error_tipo: Mapped[str | None] = mapped_column(String(100), nullable=True)  # timeout, stock_insuficiente, etc.
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tiempo_respuesta_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Contexto
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Índices compuestos para consultas rápidas
    __table_args__ = (
        Index('idx_uuid_empresa', 'uuid_operacion_offline', 'empresa_id'),
        Index('idx_empresa_tipo_estado', 'empresa_id', 'tipo_operacion', 'estado_resultado'),
        Index('idx_empresa_fecha', 'empresa_id', 'fecha_intento'),
    )

    def __repr__(self) -> str:
        return (
            f"<OperacionSincronizacionLog uuid={self.uuid_operacion_offline} "
            f"intento={self.numero_intento} estado={self.estado_resultado}>"
        )
