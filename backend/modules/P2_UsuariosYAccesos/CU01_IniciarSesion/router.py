"""Endpoints de CU01 — Iniciar sesión.

La URL pública es genérica (/auth/login): el caso de uso queda identificado
internamente por la ubicación del código y el tag de OpenAPI, no por la URL.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from .schemas import LoginRequest, LoginResponse, UsuarioPublico
from .service import CredencialesInvalidasError, LoginService, UsuarioInactivoError

router = APIRouter(prefix="/auth", tags=["CU01 - Iniciar sesión"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    service = LoginService(db)
    try:
        usuario, token = service.autenticar(payload.correo, payload.password)
    except CredencialesInvalidasError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        ) from exc
    except UsuarioInactivoError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está inhabilitada. Contacta al administrador.",
        ) from exc

    return LoginResponse(access_token=token, usuario=UsuarioPublico.model_validate(usuario))
