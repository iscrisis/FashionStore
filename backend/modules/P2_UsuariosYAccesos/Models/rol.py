"""Rol de usuario, compartido por todo el paquete P2 — Usuarios y accesos.

Un único mecanismo de login (CU01) sirve a los 6 roles del sistema. Todos son
actores humanos autenticables; pagos e IA son integraciones externas, no
usuarios, y por eso no tienen rol aquí.

SUPERADMIN es el rol de plataforma global (empresa_id = NULL), por encima de
los administradores de empresa (empresa_id = ID_EMPRESA).

PROVEEDOR se agrega como actor autenticable, pero todavía no tiene perfil ni
panel propio ni relación con sucursales — eso corresponde a un paso posterior.
"""

import enum


class RolUsuario(str, enum.Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMINISTRADOR = "ADMINISTRADOR"
    ENCARGADO_SUCURSAL = "ENCARGADO_SUCURSAL"
    CAJERO = "CAJERO"
    CLIENTE = "CLIENTE"
    PROVEEDOR = "PROVEEDOR"
