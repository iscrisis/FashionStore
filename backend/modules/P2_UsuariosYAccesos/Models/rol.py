"""Rol de usuario, compartido por todo el paquete P2 — Usuarios y accesos.

Un único mecanismo de login (CU01) sirve a los 4 roles del sistema.
"""

import enum


class RolUsuario(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    ENCARGADO_SUCURSAL = "ENCARGADO_SUCURSAL"
    CAJERO = "CAJERO"
    CLIENTE = "CLIENTE"
