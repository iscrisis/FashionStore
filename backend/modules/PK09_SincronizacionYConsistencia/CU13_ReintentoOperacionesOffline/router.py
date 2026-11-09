"""Router para CU13 — Endpoints de reintentos."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.dependencies import get_db, get_current_user
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .service import ReintentoService
from .schemas import ReintentoRequest, ReintentoResultado

router = APIRouter(
    prefix="/reintentar",
    tags=["CU13 — Reintentar sincronización fallida"],
)


@router.post("/ventas/{uuid}")
def reintentar_venta(
    uuid: str,
    request: ReintentoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReintentoResultado:
    """Reintentar sincronización de una venta fallida.

    - Valida que el usuario esté autenticado (CAJERO/ADMINISTRADOR)
    - Verifica elegibilidad (intentos, backoff)
    - Consulta CU12 para evitar duplicados
    - Llama CU11 para reintentar
    - Registra en auditoría
    """
    try:
        service = ReintentoService(db)
        resultado = service.reintentar_venta(usuario, uuid, request)
        return resultado
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reintentar venta: {str(e)}")


@router.post("/reservas/{uuid}")
def reintentar_reserva(
    uuid: str,
    request: ReintentoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReintentoResultado:
    """Reintentar sincronización de una reserva fallida.

    - Valida que el usuario esté autenticado (CLIENTE/CAJERO/ADMINISTRADOR)
    - CLIENTE solo puede reintentar reservas propias
    - Verifica elegibilidad
    - Consulta CU12 para evitar duplicados
    - Llama CU11 para reintentar
    - Registra en auditoría
    """
    try:
        service = ReintentoService(db)
        resultado = service.reintentar_reserva(usuario, uuid, request)
        return resultado
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reintentar reserva: {str(e)}")
