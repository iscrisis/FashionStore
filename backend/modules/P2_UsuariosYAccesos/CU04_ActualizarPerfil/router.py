"""Endpoints de CU04 -- Actualizar perfil.

Requiere sesión (Depends(get_current_usuario), la misma dependencia que ya
usa CU05 para proteger sus endpoints -- ver app/core/deps.py): el usuario a
consultar/editar es siempre "quien sea que el JWT identifique", nunca un id
que el cliente pueda enviar. No existe ningún parámetro `usuario_id` en estas
rutas -- por diseño, no por validación adicional.

Vive bajo el mismo prefix "/auth" que CU01-CU03 (el caso de uso queda
identificado por la ubicación del código y el tag de OpenAPI, no por la URL
-- mismo criterio que en esos routers).

Respuestas JSON neutras (sin HTML): Angular hoy y Flutter más adelante
consumen exactamente el mismo contrato REST (mismo criterio que CU01-CU03).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import ActualizarPerfilRequest, MiPerfilResponse
from .service import ActualizarPerfilService, CorreoYaRegistradoError

router = APIRouter(prefix="/auth", tags=["CU04 - Actualizar perfil"])


@router.get("/me", response_model=MiPerfilResponse)
def obtener_mi_perfil(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
    return usuario


@router.put("/me", response_model=MiPerfilResponse)
def actualizar_mi_perfil(
    payload: ActualizarPerfilRequest,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
) -> Usuario:
    try:
        return ActualizarPerfilService(db).actualizar(usuario, payload)
    except CorreoYaRegistradoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe una cuenta registrada con ese correo."
        ) from exc
