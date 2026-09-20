"""PK04 — Reservas y atención (CU17-CU20).

CU17_CrearReservaPrendas es el primer CU implementado de este paquete: permite
que un Cliente reserve una prenda (producto + variante) en la sucursal que
elija, sin descontar stock -- solo valida disponibilidad al momento de crear
la reserva. CU18 (atender/cancelar reserva), CU19 y CU20 quedan fuera de este
alcance y todavía no están implementados.

Este paquete tiene su propio directorio Models/ (en vez de sumar Reserva a
P1_SucursalesYCatalogos/Models como hacen CU15/CU16) porque Reserva es una
entidad nueva propia de PK04, no del catálogo/inventario de P1 -- mantiene la
regla de no tocar archivos de P1/P2/P3 para este CU.
"""
