"""CU05 — Gestionar usuarios y roles.

Administra USUARIO + ROL + ESTADO para cuentas internas (ADMINISTRADOR,
ENCARGADO_SUCURSAL, CAJERO). No administra inventario, sucursales ni stock.

El alcance por sucursal (para ENCARGADO_SUCURSAL/CAJERO) queda pendiente de que
exista CU06 — Gestionar sucursales: hoy esa entidad no existe en el proyecto, y
crearla aquí duplicaría un caso de uso que no pertenece a este paquete. Cuando
CU06 exista, este módulo deberá agregar la relación usuario↔sucursal mediante
una foreign key hacia esa entidad, sin duplicarla.
"""
