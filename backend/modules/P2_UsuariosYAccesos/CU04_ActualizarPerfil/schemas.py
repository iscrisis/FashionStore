"""Contratos de entrada/salida de CU04 -- Actualizar perfil (cliente autenticado).

Reutiliza UsuarioPublico de CU01 (id/nombre/correo/rol) en vez de duplicar
esos campos -- mismo criterio que ya usa UsuarioAdminView en CU05. Los
patrones de validación de nombre/correo/telefono son los mismos que ya exige
CU02 al registrarse (ver CU02_RegistrarCliente/schemas.py): CU04 no inventa
una política distinta para los mismos campos.
"""

import re

from pydantic import BaseModel, field_validator

from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.schemas import UsuarioPublico

_CORREO_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TELEFONO_PATTERN = re.compile(r"^[0-9+\-\s()]{6,20}$")


class MiPerfilResponse(UsuarioPublico):
    """Vista del propio perfil: UsuarioPublico + telefono. Nunca incluye
    password_hash, ni campos internos (sucursal_id, proveedor_id, is_active)."""

    telefono: str | None


class ActualizarPerfilRequest(BaseModel):
    """Deliberadamente SOLO nombre/correo/telefono -- no tiene campos `rol`,
    `sucursal_id`, `proveedor_id` ni `is_active`, así un cliente no puede
    escalar privilegios enviándolos de más en el body (Pydantic ignora
    cualquier campo no declarado aquí)."""

    nombre: str
    correo: str
    telefono: str

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
