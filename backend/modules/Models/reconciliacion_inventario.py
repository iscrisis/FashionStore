"""Modelo para auditoría de reconciliaciones de inventario (CU15)."""

from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ReconciliacionInventario(Base):
    """Auditoría de reconciliaciones de inventario después de operaciones offline.

    Permite verificar la consistencia sin aplicar ajustes automáticos.
    """

    __tablename__ = "reconciliacion_inventario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, nullable=False, index=True)
    sucursal_id = Column(Integer, nullable=False)
    uuid_operacion_offline = Column(String(255), nullable=False, index=True)
    tipo_operacion = Column(String(50), nullable=False)  # VENTA_OFFLINE, RESERVA_OFFLINE
    estado_general = Column(String(50), nullable=False)  # CONSISTENTE, DIVERGENCIA_DETECTADA, PENDIENTE_REVISION
    detalles_json = Column(Text, nullable=True)  # JSON con detalles por variante
    motivo_inconsistencia = Column(String(500), nullable=True)
    fecha_reconciliacion = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<ReconciliacionInventario uuid={self.uuid_operacion_offline} estado={self.estado_general}>"
