"""Rol de usuario, compartido por todo el paquete P2 — Usuarios y accesos.

Un único mecanismo de login (CU01) sirve a los 5 roles del sistema. Todos son
actores humanos autenticables; pagos e IA son integraciones externas, no
usuarios, y por eso no tienen rol aquí.

PROVEEDOR se agrega como actor autenticable, pero todavía no tiene perfil ni
panel propio ni relación con sucursales — eso corresponde a un paso posterior.
"""

import enum


class RolUsuario(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    ENCARGADO_SUCURSAL = "ENCARGADO_SUCURSAL"
    CAJERO = "CAJERO"
    CLIENTE = "CLIENTE"
    PROVEEDOR = "PROVEEDOR"
