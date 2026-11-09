"""Schemas para CU15 — Reconciliar inventario."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReconciliacionVarianteDetail(BaseModel):
    """Detalle de reconciliación por variante."""
    producto_variante_id: int
    cantidad_operacion: int
    stock_actual: int
    stock_esperado: int
    diferencia: int
    estado: str  # CONSISTENTE, DIVERGENCIA_DETECTADA, PENDIENTE_REVISION


class ResultadoReconciliacion(BaseModel):
    """Resultado de reconciliación de una operación."""
    uuid_operacion_offline: str
    tipo_operacion: str  # VENTA_OFFLINE, RESERVA_OFFLINE
    empresa_id: int
    sucursal_id: int
    estado_general: str  # CONSISTENTE, DIVERGENCIA_DETECTADA, PENDIENTE_REVISION
    detalles: List[ReconciliacionVarianteDetail]
    motivo_inconsistencia: Optional[str] = None
    fecha_reconciliacion: datetime
    idempotencia_verificada: bool = True


class ConsultaReconciliacionRequest(BaseModel):
    """Request para consultar reconciliación de una operación."""
    uuid_operacion_offline: str
    tipo_operacion: str
    empresa_id: int


class ListaReconciliacionesResponse(BaseModel):
    """Respuesta con lista de reconciliaciones."""
    total: int
    reconciliaciones: List[ResultadoReconciliacion]
