"""CU23 -- Procesar pago electrónico (Cliente).

Cobra una Venta DIGITAL PENDIENTE_PAGO (CU22, ver Models/venta.py) con
Stripe Checkout Hosted, modo TEST. Angular nunca ve datos de tarjeta ni
decide si el pago se completó -- solo pide una Checkout Session, redirige a
Stripe en la misma pestaña, y luego pide a FastAPI que verifique el
resultado directamente contra Stripe (ver service.py).
"""
