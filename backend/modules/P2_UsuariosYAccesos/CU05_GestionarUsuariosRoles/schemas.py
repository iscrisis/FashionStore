"""Contratos de entrada/salida de CU05 — Gestionar usuarios y roles.

La vista administrativa extiende UsuarioPublico (de CU01) en lugar de duplicar
sus campos: reutiliza id/nombre/correo/rol y solo agrega lo que CU01 no necesita.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.schemas import UsuarioPublico
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario

# CU05 solo administra cuentas internas. CLIENTE se crea mediante CU02 (registro
# público) y no debe poder asignarse/reasignarse desde este caso de uso.
ROLES_INTERNOS = (RolUsuario.ADMINISTRADOR, RolUsuario.ENCARGADO_SUCURSAL, RolUsuario.CAJERO)


class RolDisponible(BaseModel):
    valor: RolUsuario
    etiqueta: str


class UsuarioAdminView(UsuarioPublico):
    model_config = ConfigDict(from_attributes=True)

    is_active: bool
    created_at: datetime


class UsuarioCrear(BaseModel):
    nombre: str
    correo: str
    password: str
    rol: RolUsuario
    is_active: bool = True


class UsuarioActualizar(BaseModel):
    nombre: str
    correo: str


class CambiarRolRequest(BaseModel):
    rol: RolUsuario


class CambiarEstadoRequest(BaseModel):
    is_active: bool
