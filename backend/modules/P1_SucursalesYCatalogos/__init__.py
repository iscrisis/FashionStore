"""Paquete funcional P1 — Sucursales y catálogo.

Agrupa los casos de uso relacionados con la red de tiendas físicas y los datos
base del catálogo de FashionStore:

- CU06 — Gestionar sucursales (implementado)
- CU07..CU12 — catálogo, inventario, proveedores, reservas, ventas, reportes (pendientes)

``Models/`` contiene las entidades compartidas por los CU de este paquete
(Ciudad, Sucursal). Cada ``CUxx_.../`` contiene únicamente la lógica exclusiva
de ese caso de uso (router, schemas, service, repository).
"""
