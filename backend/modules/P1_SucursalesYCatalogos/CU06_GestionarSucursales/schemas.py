"""Contratos de entrada/salida de CU06 — Gestionar sucursales."""

import re

from pydantic import BaseModel, ConfigDict, field_validator

_TELEFONO_PATTERN = re.compile(r"^[0-9+\-\s()]{6,20}$")


class CiudadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    departamento: str
    is_active: bool


class CiudadCrear(BaseModel):
    nombre: str
    departamento: str
    is_active: bool = True

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre de la ciudad debe tener al menos 2 caracteres.")
        return limpio

    @field_validator("departamento")
    @classmethod
    def _validar_departamento(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El departamento debe tener al menos 2 caracteres.")
        return limpio


class SucursalAdminView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    direccion: str
    telefono: str
    is_active: bool
    ciudad: CiudadOut


class _SucursalDatosBase(BaseModel):
    nombre: str
    ciudad_id: int
    direccion: str
    telefono: str

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre de la sucursal debe tener al menos 2 caracteres.")
        return limpio

    @field_validator("direccion")
    @classmethod
    def _validar_direccion(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 5:
            raise ValueError("La dirección debe tener al menos 5 caracteres.")
        return limpio

    @field_validator("telefono")
    @classmethod
    def _validar_telefono(cls, valor: str) -> str:
        limpio = valor.strip()
        if not _TELEFONO_PATTERN.match(limpio):
            raise ValueError(
                "El teléfono solo puede contener dígitos, espacios y los símbolos + - ( )."
            )
        return limpio


class SucursalCrear(_SucursalDatosBase):
    is_active: bool = True


class SucursalActualizar(_SucursalDatosBase):
    pass


class CambiarEstadoRequest(BaseModel):
    is_active: bool
