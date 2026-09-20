"""CU25 -- Procesar pago presencial (Cajero).

Confirma el pago (EFECTIVO/TARJETA/QR, nunca Stripe) de una Venta PRESENCIAL
PENDIENTE_PAGO que ya arma CU24 -- reutiliza Venta/VentaDetalle (CU22/CU24)
y Pago (CU23) tal cual, sin crear un segundo sistema de pagos. Al confirmar:
la Venta pasa a PAGADA, se descuenta stock_actual (y, si la venta vino de
una Reserva, también stock_reservado), y esa Reserva pasa a ATENDIDA -- todo
en una única operación segura e idempotente (una Venta ya PAGADA no puede
cobrarse dos veces).

CU26 (devoluciones/cambios) y CU31 (comprobante) reutilizarán después la
Venta ya pagada y este mismo Pago -- ninguno de los dos se implementa aquí.
"""
