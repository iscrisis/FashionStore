"""Endpoints de CU02 -- Registrar cliente.

Público: NO requiere sesión, JWT ni rol -- cualquier visitante puede crear su
cuenta. Vive bajo el mismo prefix "/auth" que CU01 porque, igual que el
login, es parte del flujo público de autenticación -- el caso de uso queda
identificado por la ubicación del código y el tag de OpenAPI, no por la URL
(mismo criterio ya usado en CU01/router.py).

NO emite JWT ni inicia sesión automáticamente: el cliente recién registrado
inicia sesión llamando a CU01 (POST /auth/login) por separado -- así no se
duplica la emisión de tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.schemas import UsuarioPublico

from .schemas import RegistroClienteRequest
from .service import CorreoYaRegistradoError, RegistroClienteService

router = APIRouter(prefix="/auth", tags=["CU02 - Registrar cliente"])


@router.post("/register", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED)
def registrar_cliente(
    payload: RegistroClienteRequest, db: Session = Depends(get_db)
) -> UsuarioPublico:
    try:
        usuario = RegistroClienteService(db).registrar(payload)
    except CorreoYaRegistradoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe una cuenta registrada con ese correo."
        ) from exc
    return UsuarioPublico.model_validate(usuario)
