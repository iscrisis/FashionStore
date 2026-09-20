"""PK05 — Compras, ventas y pagos (CU21-...).

CU21_UsarCarritoCompras es el primer CU implementado de este paquete: permite
que un Cliente arme un carrito de COMPRA DIGITAL (producto + variante +
cantidad) previo a cualquier compra real -- sin crear Reserva, Venta ni Pago,
y sin tocar StockSucursal (ni `cantidad` ni `stock_reservado`). CU22 en
adelante (compra digital, pago electrónico, venta/pago presencial) quedan
fuera de este alcance y todavía no están implementados.

Este paquete tiene su propio directorio Models/ (en vez de sumar Carrito a
P1_SucursalesYCatalogos/Models) porque Carrito/CarritoItem son entidades
nuevas propias de PK05, no del catálogo/inventario de P1 -- mismo criterio ya
usado por P4_ReservasYAtencion para Reserva/ReservaDetalle: no tocar archivos
de P1/P2/P3/P4 para este CU.
"""
