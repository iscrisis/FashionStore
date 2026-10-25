"""Contratos de entrada/salida de CU01 — Registrar empresa contratante."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, EmailStr


class EmpresaOut(BaseModel):
    """Respuesta: Empresa registrada exitosamente."""

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


class UsuarioAdministradorOut(BaseModel):
    """Respuesta: Datos del usuario administrador creado."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    rol: str
    is_active: bool
    created_at: datetime


class RegistroEmpresaOut(BaseModel):
    """Respuesta: Empresa + Administrador registrados exitosamente."""

    empresa: EmpresaOut
    administrador: UsuarioAdministradorOut


class EmpresaCrear(BaseModel):
    """Solicitud: Datos para registrar una nueva empresa + administrador."""

    nombre: str
    slug: str
    razon_social: str
    correo: EmailStr
    telefono: str
    nombre_admin: str
    correo_admin: EmailStr
    password: str

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, valor: str) -> str:
        """Validar nombre: 2-150 caracteres, no vacío."""
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        if len(limpio) > 150:
            raise ValueError("El nombre no puede exceder 150 caracteres.")
        return limpio

    @field_validator("slug")
    @classmethod
    def validar_slug(cls, valor: str) -> str:
        """Validar slug: 2-100 caracteres, minúsculas, guiones y números."""
        limpio = valor.strip().lower()
        if len(limpio) < 2:
            raise ValueError("El slug debe tener al menos 2 caracteres.")
        if len(limpio) > 100:
            raise ValueError("El slug no puede exceder 100 caracteres.")
        if not re.match(r"^[a-z0-9\-]+$", limpio):
            raise ValueError("El slug solo puede contener letras minúsculas, números y guiones.")
        if limpio.startswith("-") or limpio.endswith("-"):
            raise ValueError("El slug no puede empezar o terminar con guion.")
        return limpio

    @field_validator("razon_social")
    @classmethod
    def validar_razon_social(cls, valor: str) -> str:
        """Validar razón social: 2-200 caracteres."""
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("La razón social debe tener al menos 2 caracteres.")
        if len(limpio) > 200:
            raise ValueError("La razón social no puede exceder 200 caracteres.")
        return limpio

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, valor: str) -> str:
        """Validar teléfono: formato válido."""
        limpio = valor.strip()
        if len(limpio) < 6:
            raise ValueError("El teléfono debe tener al menos 6 caracteres.")
        if len(limpio) > 30:
            raise ValueError("El teléfono no puede exceder 30 caracteres.")
        if not re.match(r"^[\d\s\+\-\(\)]+$", limpio):
            raise ValueError("El teléfono contiene caracteres inválidos.")
        return limpio

    @field_validator("nombre_admin")
    @classmethod
    def validar_nombre_admin(cls, valor: str) -> str:
        """Validar nombre del administrador: mínimo 2 caracteres."""
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre del administrador debe tener al menos 2 caracteres.")
        return limpio

    @field_validator("password")
    @classmethod
    def validar_password(cls, valor: str) -> str:
        """Validar contraseña: mínimo 6 caracteres."""
        if len(valor) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        return valor
