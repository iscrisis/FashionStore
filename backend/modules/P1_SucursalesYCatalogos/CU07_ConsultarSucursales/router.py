"""Endpoints de CU07 -- Consultar sucursales.

Públicos: NO requieren sesión ni rol -- Invitado o Cliente los consulta sin
iniciar sesión (a diferencia de CU06, que exige un ADMINISTRADOR). Son de
solo lectura -- crear/editar/eliminar sigue siendo exclusivo de CU06; CU07 no
lo duplica, solo lee lo que ya se publicó como activo.

El flujo público es únicamente Ciudad -> Sucursal: aunque Ciudad (CU06)
también guarda "departamento" para la gestión administrativa, CU07 no lo
expone -- la consulta pública no debe depender de él (ver schemas.py).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from .schemas import CiudadPublicaOut, SucursalPublicaOut
from .service import SucursalesPublicoService, SucursalNoEncontradaError

router = APIRouter(prefix="/sucursales-publicas", tags=["CU07 - Consultar sucursales"])


@router.get("/ciudades", response_model=list[CiudadPublicaOut])
def listar_ciudades(db: Session = Depends(get_db)) -> list[CiudadPublicaOut]:
    return SucursalesPublicoService(db).listar_ciudades()


@router.get("/sucursales", response_model=list[SucursalPublicaOut])
def listar_sucursales(
    ciudad_id: int | None = Query(default=None), db: Session = Depends(get_db)
) -> list[SucursalPublicaOut]:
    return SucursalesPublicoService(db).listar_sucursales(ciudad_id=ciudad_id)


@router.get("/sucursales/{sucursal_id}", response_model=SucursalPublicaOut)
def obtener_sucursal(sucursal_id: int, db: Session = Depends(get_db)) -> SucursalPublicaOut:
    try:
        return SucursalesPublicoService(db).obtener_sucursal(sucursal_id)
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.") from exc
