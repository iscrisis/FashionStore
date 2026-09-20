"""Dependencias FastAPI transversales para resolver y autorizar al usuario autenticado.

Completa la infraestructura de seguridad que CU01 (iniciar sesión) inició: CU01 solo
emite el token; estas dependencias son las que un endpoint protegido usa para
validarlo. Vive en app/core porque, igual que security.py, no pertenece a ningún
caso de uso específico — CU05 es su primer consumidor, pero cualquier CU futuro que
proteja un endpoint la reutilizará.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.repository import UsuarioRepository
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_usuario(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado.")

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado.") from exc

    usuario_id = payload.get("sub")
    usuario = UsuarioRepository(db).get_by_id(int(usuario_id)) if usuario_id else None
    if usuario is None or not usuario.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no válido.")

    return usuario


def get_current_usuario_opcional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario | None:
    """Igual que get_current_usuario, pero nunca exige sesión -- para
    endpoints públicos que, SI existe un token válido, personalizan la
    respuesta (primer consumidor: CU29, el asistente funciona igual para
    Invitado y Cliente). Sin token, con un token inválido/expirado, o con un
    usuario inactivo, devuelve None en vez de un 401 -- nunca bloquea el
    endpoint."""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        return None
    usuario_id = payload.get("sub")
    usuario = UsuarioRepository(db).get_by_id(int(usuario_id)) if usuario_id else None
    if usuario is None or not usuario.is_active:
        return None
    return usuario


def require_roles(*roles: RolUsuario):
    """Dependencia factory: exige sesión válida Y uno de los roles indicados."""

    def _dependency(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "No tienes permisos para realizar esta acción.",
            )
        return usuario

    return _dependency
