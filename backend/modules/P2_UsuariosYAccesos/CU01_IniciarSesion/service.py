"""Reglas de negocio de CU01 — Iniciar sesión.

Flujo: correo + contraseña -> buscar usuario -> verificar credenciales ->
verificar que el usuario esté habilitado -> obtener rol -> generar token ->
devolver usuario autenticado.
"""

from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .repository import UsuarioRepository


class CredencialesInvalidasError(Exception):
    """Correo o contraseña incorrectos."""


class UsuarioInactivoError(Exception):
    """Las credenciales son correctas pero el usuario está deshabilitado."""


class LoginService:
    def __init__(self, db: Session):
        self._repository = UsuarioRepository(db)

    def autenticar(self, correo: str, password: str) -> tuple[Usuario, str]:
        usuario = self._repository.get_by_correo(correo)
        if usuario is None or not verify_password(password, usuario.password_hash):
            raise CredencialesInvalidasError

        if not usuario.is_active:
            raise UsuarioInactivoError

        token = create_access_token(subject=str(usuario.id), extra_claims={"rol": usuario.rol.value})
        return usuario, token
