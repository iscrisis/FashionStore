"""Contratos de entrada/salida de CU02 — Gestionar administrador de empresa."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, EmailStr


class EmpresaOut(BaseModel):
    """Respuesta: Empresa consultada."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    slug: str
    razon_social: str
    correo: str
    telefono: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdministradorOut(BaseModel):
    """Respuesta: Datos del administrador de una empresa."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    rol: str
    is_active: bool
    empresa_id: int
    created_at: datetime


class ConsultarAdministradorOut(BaseModel):
    """Respuesta: Empresa + Administrador asociado."""

    empresa: EmpresaOut
    administrador: AdministradorOut


class AdministradorActualizar(BaseModel):
    """Solicitud: Datos permitidos para actualizar el administrador.

    Restricciones:
    - nombre: permitido actualizar
    - correo: permitido actualizar
    - is_active: permitido actualizar
    - rol: NO se permite cambiar desde CU02 (es ADMINISTRADOR, punto)
    - empresa_id: NO se permite cambiar bajo ninguna circunstancia
    """

    nombre: str
    correo: EmailStr
    is_active: bool = True

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, valor: str) -> str:
        """Validar nombre: mínimo 2 caracteres."""
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        return limpio
