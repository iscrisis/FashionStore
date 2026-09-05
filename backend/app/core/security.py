"""Primitivas de seguridad genéricas (hashing de contraseñas y JWT).

No pertenece a ningún caso de uso específico: CU01 (iniciar sesión) es su primer
consumidor, pero CU02 (registro), CU03 (recuperar contraseña) y CU05 (gestionar
usuarios y roles) reutilizarán estas mismas funciones.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expires_at, **(extra_claims or {})}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Lanza jwt.PyJWTError (o subclases) si el token es inválido o expiró."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
