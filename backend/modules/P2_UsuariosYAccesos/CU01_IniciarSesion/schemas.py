"""Contratos de entrada/salida de CU01 — Iniciar sesión."""

from pydantic import BaseModel, ConfigDict

from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario


class UsuarioPublico(BaseModel):
    """Representación pública de Usuario. Nunca incluye password ni password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    rol: RolUsuario


class LoginRequest(BaseModel):
    correo: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioPublico
