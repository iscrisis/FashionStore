"""Esquemas de entrada/salida para CU11 — Sincronizar operaciones pendientes."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SincronizarVentaOfflineDetalleIn(BaseModel):
    """Detalle de venta offline a sincronizar."""
    producto_variante_id: int
    cantidad: int
    precio_unitario: Decimal | float
    subtotal: Decimal | float


class SincronizarVentaOfflineIn(BaseModel):
    """Venta presencial offline a sincronizar.

    uuid: Identificador único generado localmente (IndexedDB)
    tipo_operacion: 'VENTA_OFFLINE' (para extensión futura)
    sucursal_id: Solicitado pero validado contra actor.sucursal_id
    empresa_id: Solicitado pero validado contra actor.empresa_id
    """
    uuid: str = Field(..., description="UUID único generado en IndexedDB")
    tipo_operacion: Literal["VENTA_OFFLINE"]
    empresa_id: int
    sucursal_id: int
    fecha_operacion_local: str
    detalles: list[SincronizarVentaOfflineDetalleIn]
    metodo_pago: Literal["EFECTIVO"] = "EFECTIVO"
    monto_recibido: Decimal | float | None = None
    total: Decimal | float


class SincronizarReservaOfflineDetalleIn(BaseModel):
    """Detalle de reserva offline a sincronizar."""
    producto_variante_id: int
    cantidad: int


class SincronizarReservaOfflineIn(BaseModel):
    """Reserva offline a sincronizar.

    uuid: Identificador único generado localmente (IndexedDB)
    tipo_operacion: 'RESERVA_OFFLINE' (para extensión futura)
    cliente_id: ID del cliente que hizo la reserva (del actor autenticado)
    fecha_reserva: Fecha de la reserva (YYYY-MM-DD)
    hora_inicio: Hora de inicio del bloque (HH:MM)
    """
    uuid: str = Field(..., description="UUID único generado en IndexedDB")
    tipo_operacion: Literal["RESERVA_OFFLINE"]
    empresa_id: int
    sucursal_id: int
    cliente_id: int
    fecha_reserva: str  # "2026-11-08"
    hora_inicio: str    # "10:00"
    detalles: list[SincronizarReservaOfflineDetalleIn]


# Respuestas
class ResultadoSincronizacionVenta(BaseModel):
    """Resultado de sincronizar una venta offline."""
    uuid_local: str
    venta_id: int | None
    codigo_venta: str | None
    estado: Literal["CONFIRMADA", "RECHAZADA", "CONFLICTO"]
    motivo: str | None = None
    total: Decimal | None = None


class ResultadoSincronizacionReserva(BaseModel):
    """Resultado de sincronizar una reserva offline."""
    uuid_local: str
    reserva_id: int | None
    codigo_reserva: str | None
    estado: Literal["CONFIRMADA", "RECHAZADA", "CONFLICTO"]
    motivo: str | None = None
