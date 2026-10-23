"""Contratos de entrada/salida de CU19 -- Cancelar reserva (Cliente).

CU19 no define esquemas propios: reutiliza `ReservaOut` y `ReservaDetalleOut`
(ver CU17_CrearReservaPrendas/schemas.py) para mantener consistencia en las
respuestas. El cancelar de un detalle devuelve `ReservaDetalleOut`; el
cancelar de una reserva completa devuelve `ReservaOut` (la cabecera con todos
sus detalles actualizados).

Este archivo existe solo para coherencia: permite que otros módulos importen
esquemas de cancelación desde CU19 sin quebrar una convención de estructura
(cada CU = su propio paquete con router/service/schemas/repository si
corresponde), aunque internamente reutilice lo que CU17 ya escribió.
"""

from modules.P4_ReservasYAtencion.CU17_CrearReservaPrendas.schemas import (
    EstadoReservaOut,
    ReservaDetalleOut,
    ReservaOut,
)

__all__ = ["ReservaOut", "ReservaDetalleOut", "EstadoReservaOut"]
