"""CU31 -- Emitir comprobante de venta (Cliente/Cajero).

Comprobante INTERNO de FashionStore -- nunca una factura fiscal (sin NIT, sin
impuestos, sin facturación electrónica): un resumen legible de una Venta ya
PAGADA, calculado en el momento a partir de las entidades que ya existen
(Venta, VentaDetalle, Pago, Usuario, Sucursal, Producto/ProductoVariante).

No crea ninguna tabla propia -- a diferencia de CU26, un comprobante no tiene
trazabilidad propia que persistir: es una PROYECCIÓN de solo lectura sobre
datos que CU22/CU23/CU24/CU25 ya guardaron. Por eso "generarlo" no es un paso
aparte con su propio estado: en cuanto `Venta.estado == PAGADA`, el
comprobante YA está disponible -- GET /comprobantes/{venta_id} siempre
recalcula desde la base actual, nunca desde una copia guardada. Ninguno de
esos cuatro CU se modifica para "avisarle" a CU31 -- no hace falta: no hay
ningún evento que emitir ni ningún dato que sincronizar.

Autorización: SOLO el Cliente dueño de la venta (`Venta.cliente_id`) o un
Cajero de la MISMA sucursal (`Venta.sucursal_id == actor.sucursal_id`) pueden
consultarlo -- nunca se confía en `cliente_id`/`venta_id`/`sucursal_id` que
Angular envíe, todo se resuelve del JWT (ver router.py/service.py).

El envío por correo (POST /comprobantes/{venta_id}/enviar) reutiliza
app/integrations/mailer.py tal cual (ahora con soporte opcional de adjuntos,
ver ese archivo) -- nunca bloquea ni revierte la venta si el SMTP falla: el
pago ya aprobado por CU23/CU25 es lo que cuenta como "venta completada"; el
correo es solo una notificación posterior, best-effort (ver service.py).
"""
