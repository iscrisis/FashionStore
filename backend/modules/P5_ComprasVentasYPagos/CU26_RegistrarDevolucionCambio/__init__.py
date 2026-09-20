"""CU26 -- Registrar devolución o cambio (Cajero).

Permite al Cajero buscar una Venta PAGADA (por `codigo_venta`, ej. VT-00001 --
NUNCA lista todas las ventas de todos los Clientes, ver router.py) y procesar,
prenda por prenda, una DEVOLUCION o un CAMBIO -- ver Models/devolucion.py
(`DevolucionCambio`) para la trazabilidad y el resto de los docstrings de
este paquete para las reglas de negocio completas.

Reutiliza Venta/VentaDetalle (CU22/CU24), Pago (CU23/CU25) y StockSucursal
(CU14/15/16) tal cual existen -- la única tabla propia de este módulo es
DevolucionCambio, ya creada por la migración de CU26.

Ambas operaciones (DEVOLUCION/CAMBIO) actualizan el stock automáticamente en
la misma transacción -- CU26 nunca depende de que el Encargado registre un
movimiento manual aparte (CU16 es para ajustes por conteo físico/daño, un
caso completamente distinto).
"""
