"""CU03 — Asociar usuarios y sucursales a empresa.

Módulo de servicios compartidos para la lógica de multitenant/SaaS.

La funcionalidad de asociación (asignar empresa_id) es reutilizada por:
- CU05 (crear usuario)
- CU06 (crear sucursal)

No tiene router propio — los endpoints están en CU05 y CU06.
"""
