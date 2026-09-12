"""Contratos de entrada/salida de CU03 -- Recuperar contraseña (público)."""

import re

from pydantic import BaseModel, field_validator, model_validator

_CORREO_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ForgotPasswordRequest(BaseModel):
    correo: str

    @field_validator("correo")
    @classmethod
    def _validar_correo(cls, valor: str) -> str:
        limpio = valor.strip().lower()
        if not _CORREO_PATTERN.match(limpio):
            raise ValueError("Ingresa un correo válido.")
        return limpio


class MensajeGenericoResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirmar_password: str

    @field_validator("token")
    @classmethod
    def _validar_token(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio:
            raise ValueError("Token inválido.")
        return limpio

    @field_validator("new_password")
    @classmethod
    def _validar_password(cls, valor: str) -> str:
        # Misma regla que ya exigen CU02 (registro) y CU05 (alta de cuentas internas).
        if len(valor) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return valor

    @model_validator(mode="after")
    def _validar_confirmacion(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden.")
        return self
