"""Contratos de entrada de CU02 -- Registrar cliente (público).

Deliberadamente NO tiene un campo `rol`: el registro público solo puede
crear cuentas CLIENTE, y ese rol se fija en el service, nunca en lo que
envía el cliente (ver service.py). La respuesta reutiliza UsuarioPublico de
CU01 tal cual -- no se duplica.
"""

import re

from pydantic import BaseModel, field_validator, model_validator

_CORREO_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TELEFONO_PATTERN = re.compile(r"^[0-9+\-\s()]{6,20}$")


class RegistroClienteRequest(BaseModel):
    nombre: str
    correo: str
    telefono: str
    password: str
    confirmar_password: str

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        if len(limpio) > 120:
            raise ValueError("El nombre no puede superar los 120 caracteres.")
        return limpio

    @field_validator("correo")
    @classmethod
    def _validar_correo(cls, valor: str) -> str:
        limpio = valor.strip().lower()
        if not _CORREO_PATTERN.match(limpio):
            raise ValueError("Ingresa un correo válido.")
        return limpio

    @field_validator("telefono")
    @classmethod
    def _validar_telefono(cls, valor: str) -> str:
        limpio = valor.strip()
        if not _TELEFONO_PATTERN.match(limpio):
            raise ValueError(
                "El celular solo puede contener dígitos, espacios y los símbolos + - ( )."
            )
        return limpio

    @field_validator("password")
    @classmethod
    def _validar_password(cls, valor: str) -> str:
        # Misma regla que ya exige CU05 al crear cuentas internas.
        if len(valor) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return valor

    @model_validator(mode="after")
    def _validar_confirmacion(self) -> "RegistroClienteRequest":
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden.")
        return self
