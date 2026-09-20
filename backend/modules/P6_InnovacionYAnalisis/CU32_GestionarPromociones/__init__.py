"""CU32 -- Gestionar promociones (Administrador).

Permite al ADMINISTRADOR crear, consultar, editar y desactivar promociones
PORCENTUALES sobre uno o varios Producto -- nunca sobre ProductoVariante
(todas las variantes de un producto reciben el mismo descuento mientras la
promoción esté vigente). MVP: solo porcentual, ver Models/promocion.py para
lo que queda explícitamente fuera de alcance.

No crea un sistema de precios paralelo: `Producto.precio_venta` sigue siendo
SIEMPRE el precio base real, nunca se sobrescribe. El PRECIO EFECTIVO
(precio_base/precio_final/en_promocion/porcentaje_descuento) se calcula en
el momento, en un único lugar (ver precio_efectivo.py), y ese mismo cálculo
es el que reutilizan CU11 (catálogo/detalle público), CU21 (carrito), CU22
(compra digital) y CU24 (venta presencial) -- ninguno de esos CU implementa
su propia fórmula de descuento.

Autorización: SOLO un ADMINISTRADOR puede crear/editar/desactivar
promociones (ver router.py) -- el Cliente y el Cajero únicamente consultan,
indirectamente, el precio YA resuelto a través de los CU que sí consumen
(catálogo, carrito, compra, venta presencial), nunca a través de este
módulo.

Preparado para Flutter: toda la regla de descuento vive en FastAPI: Angular
(y más adelante Flutter) solo muestra `precio_base`/`precio_final`/
`en_promocion`/`porcentaje_descuento` ya calculados, nunca los recalcula.
"""
