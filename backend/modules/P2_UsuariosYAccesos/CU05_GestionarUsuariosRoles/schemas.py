"""Contratos de entrada/salida de CU05 — Gestionar usuarios y roles.

La vista administrativa extiende UsuarioPublico (de CU01) en lugar de duplicar
sus campos: reutiliza id/nombre/correo/rol y solo agrega lo que CU01 no necesita.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.schemas import UsuarioPublico
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario

# CU05 administra cuentas de empleados de tienda y de proveedor. CLIENTE se
# crea mediante CU02 (registro público) y ADMINISTRADOR GENERAL es una cuenta
# única de sistema (sembrada aparte) — ninguno de los dos se asigna/reasigna
# desde este caso de uso.
ROLES_INTERNOS = (RolUsuario.ENCARGADO_SUCURSAL, RolUsuario.CAJERO, RolUsuario.PROVEEDOR)

# Roles que trabajan en tienda: sucursal_id obligatorio, proveedor_id prohibido.
ROLES_CON_SUCURSAL = (RolUsuario.ENCARGADO_SUCURSAL, RolUsuario.CAJERO)
# PROVEEDOR: proveedor_id obligatorio (vincula la cuenta a SU proveedor), sin sucursal.
ROLES_CON_PROVEEDOR = (RolUsuario.PROVEEDOR,)


class RolDisponible(BaseModel):
    valor: RolUsuario
    etiqueta: str


class CiudadResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class SucursalResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    ciudad: CiudadResumen


class ProveedorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    razon_social: str


class UsuarioAdminView(UsuarioPublico):
    model_config = ConfigDict(from_attributes=True)

    is_active: bool
    created_at: datetime
    sucursal: SucursalResumen | None
    proveedor: ProveedorResumen | None


class UsuarioCrear(BaseModel):
    nombre: str
    correo: str
    password: str
    rol: RolUsuario
    sucursal_id: int | None = None
    proveedor_id: int | None = None
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def _validar_password(cls, valor: str) -> str:
        # Es la contraseña inicial que el Administrador define para la cuenta
        # (no hay contraseña temporal automática ni recuperación todavía);
        # misma regla que ya exige el formulario de Angular.
        if len(valor) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return valor

    @model_validator(mode="after")
    def _validar_vinculo_segun_rol(self) -> "UsuarioCrear":
        if self.rol in ROLES_CON_SUCURSAL:
            if self.sucursal_id is None:
                raise ValueError("Selecciona una sucursal para este rol.")
            if self.proveedor_id is not None:
                raise ValueError("Este rol no se vincula a un proveedor.")
        elif self.rol in ROLES_CON_PROVEEDOR:
            if self.proveedor_id is None:
                raise ValueError("Selecciona el proveedor al que pertenece esta cuenta.")
            if self.sucursal_id is not None:
                raise ValueError("Este rol no se vincula a una sucursal.")
        return self


class UsuarioActualizar(BaseModel):
    nombre: str
    correo: str
    sucursal_id: int | None = None
    proveedor_id: int | None = None


class CambiarRolRequest(BaseModel):
    rol: RolUsuario


class CambiarEstadoRequest(BaseModel):
    is_active: bool
