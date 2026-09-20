"""CU27 -- Consultar historial de compras (Cliente/Cajero).

Lista de solo lectura sobre ventas YA PAGADAS -- ni crea, ni cambia, ni
duplica nada de lo que ya existe. Reutiliza Venta/VentaDetalle (CU22/CU24),
Pago (CU23/CU25) y Usuario (CU01) tal cual, y lee (nunca escribe)
DevolucionCambio (CU26) solo para calcular un `estado_comercial` amigable
("PAGADA" / "DEVOLUCION_PARCIAL" / "DEVUELTA") a partir de las unidades ya
devueltas o cambiadas -- el mismo criterio que ya usa CU26 internamente
(`cantidad_operada_por_detalle`), sin inventar un estado nuevo ni tocar
Venta.estado ni ningún modelo de CU26.

No tiene tabla propia -- a diferencia de CU26, no hay nada que persistir. No
expone ningún endpoint de detalle ni de comprobante propio: eso ya lo
resuelve CU31 (GET /comprobantes/{venta_id}, .../pdf, .../enviar) -- el
frontend de CU27 reutiliza esos mismos endpoints/componentes para "Ver" y
"Comprobante" en vez de duplicar esa lógica aquí (ver requerimiento
explícito "no duplicar lógica de comprobantes").

Dos endpoints, cada uno resolviendo su propio actor SIEMPRE desde el JWT
(nunca desde cliente_id/sucursal_id que Angular envíe):
  - GET /historial-compras/mias (CLIENTE) -- solo sus propias compras
    PAGADAS (nunca PENDIENTE_PAGO, nunca reservas RS-XXXXX sueltas, nunca
    ventas de otro Cliente).
  - GET /historial-compras/sucursal (CAJERO) -- todas las ventas PAGADAS de
    SU sucursal (`actor.sucursal_id`), sin importar qué Cajero las vendió --
    el historial sirve para atención posterior y devoluciones (CU26), no
    solo para "mis propias ventas".

Preparado para Flutter: filtrado, orden y autorización viven enteramente en
FastAPI -- Angular (y más adelante Flutter) solo consume JSON.
"""
