"""Contratos de salida de CU27 -- Consultar historial de compras (Cliente/Cajero).

JSON limpio, sin nada específico de Angular -- Flutter reutilizará estos
mismos endpoints tal cual para "Mis compras" (ver __init__.py). Ningún
endpoint recibe cliente_id/sucursal_id en el body ni en la query -- ambos
salen SIEMPRE del actor autenticado (ver router.py/service.py); los únicos
parámetros de entrada son los filtros (fecha/código), que no identifican a
nadie.

Campos monetarios como `float`, NUNCA `Decimal` -- mismo motivo ya
documentado en CU21/CU24/CU25/CU26/CU31 (Pydantic v2 serializa `Decimal`
como STRING por defecto).
"""

from datetime import datetime

from pydantic import BaseModel


class SucursalHistorialOut(BaseModel):
    id: int
    nombre: str
    ciudad: str


class VentaHistorialOut(BaseModel):
    """Una fila del historial -- SIEMPRE de una Venta PAGADA (ver
    service.py: cualquier otro estado queda fuera del listado). `estado`
    de la Venta en sí NUNCA cambia por una devolución/cambio (CU26 no lo
    toca) -- `tiene_postventa`/`leyenda_postventa` son la única forma de
    reflejar esa información aquí, calculados en el momento a partir de
    DevolucionCambio, nunca guardados ni inventados como un estado nuevo de
    Venta."""

    venta_id: int
    codigo_venta: str
    fecha: datetime
    sucursal: SucursalHistorialOut
    cliente_nombre: str | None
    tipo: str
    metodo_pago: str
    total: float
    tiene_postventa: bool
    leyenda_postventa: str | None
