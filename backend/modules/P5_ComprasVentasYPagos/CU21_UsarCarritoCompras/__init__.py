"""CU21 -- Usar carrito de compras (Cliente).

El Cliente autenticado arma un carrito de COMPRA DIGITAL -- producto +
variante (talla+color, CU08) + cantidad -- antes de cualquier compra real.
Nada de este módulo crea Reserva (CU17), Venta ni Pago, y nada escribe en
StockSucursal (ni `cantidad` el físico, ni `stock_reservado`, ver
Models/carrito.py) -- solo LEE stock para validar que la cantidad pedida sea
atendible por al menos una sucursal activa, sin comprometer ninguna unidad
para nadie.

Un carrito por Cliente (UniqueConstraint en Carrito.cliente_id), creado la
primera vez que agrega algo. Cada línea (CarritoItem) es una
ProductoVariante + cantidad -- agregar la MISMA variante de nuevo incrementa
esa cantidad en vez de crear una línea duplicada (UniqueConstraint
carrito_id+producto_variante_id); una variante distinta (otro color, otra
talla) sí es una línea nueva.

El precio mostrado es SIEMPRE Producto.precio_venta ACTUAL -- nunca se
persiste un precio en el carrito; el precio definitivo de una compra se
resuelve en un CU posterior, fuera de este alcance.
"""
