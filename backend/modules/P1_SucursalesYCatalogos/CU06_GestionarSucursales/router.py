"""Endpoints de CU06 — Gestionar sucursales.

Todos requieren un ADMINISTRADOR autenticado. Reutiliza get_current_usuario /
require_roles ya existentes (app.core.deps) — no crea un JWT ni un AuthService
nuevo.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import (
    CambiarEstadoRequest,
    CiudadCrear,
    CiudadOut,
    SucursalActualizar,
    SucursalAdminView,
    SucursalCrear,
)
from .service import (
    CiudadesService,
    CiudadNoEncontradaError,
    CiudadNombreDuplicadoError,
    NombreDuplicadoError,
    SucursalesService,
    SucursalNoEncontradaError,
)

require_admin = require_roles(RolUsuario.ADMINISTRADOR)

router_ciudades = APIRouter(prefix="/ciudades", tags=["CU06 - Gestionar sucursales"])
router_sucursales = APIRouter(prefix="/sucursales", tags=["CU06 - Gestionar sucursales"])


@router_ciudades.get("", response_model=list[CiudadOut])
def listar_ciudades(
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[CiudadOut]:
    is_active = {"active": True, "inactive": False}.get(estado)
    return CiudadesService(db).listar(is_active=is_active)


@router_ciudades.post("", response_model=CiudadOut, status_code=status.HTTP_201_CREATED)
def crear_ciudad(
    payload: CiudadCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> CiudadOut:
    try:
        return CiudadesService(db).crear(payload)
    except CiudadNombreDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una ciudad con ese nombre.") from exc


@router_ciudades.patch("/{ciudad_id}/estado", response_model=CiudadOut)
def cambiar_estado_ciudad(
    ciudad_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> CiudadOut:
    try:
        return CiudadesService(db).cambiar_estado(ciudad_id, payload.is_active)
    except CiudadNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ciudad no encontrada.") from exc


@router_sucursales.get("", response_model=list[SucursalAdminView])
def listar_sucursales(
    search: str | None = Query(default=None),
    ciudad_id: int | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[SucursalAdminView]:
    is_active = {"active": True, "inactive": False}.get(estado)
    return SucursalesService(db).listar(search=search, ciudad_id=ciudad_id, is_active=is_active)


@router_sucursales.get("/{sucursal_id}", response_model=SucursalAdminView)
def obtener_sucursal(
    sucursal_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> SucursalAdminView:
    try:
        return SucursalesService(db).obtener(sucursal_id)
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.") from exc


@router_sucursales.post("", response_model=SucursalAdminView, status_code=status.HTTP_201_CREATED)
def crear_sucursal(
    payload: SucursalCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> SucursalAdminView:
    try:
        return SucursalesService(db).crear(payload)
    except CiudadNoEncontradaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La ciudad indicada no existe.") from exc
    except NombreDuplicadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe una sucursal con ese nombre en esa ciudad."
        ) from exc


@router_sucursales.put("/{sucursal_id}", response_model=SucursalAdminView)
def actualizar_sucursal(
    sucursal_id: int,
    payload: SucursalActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> SucursalAdminView:
    try:
        return SucursalesService(db).actualizar(sucursal_id, payload)
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.") from exc
    except CiudadNoEncontradaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La ciudad indicada no existe.") from exc
    except NombreDuplicadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe una sucursal con ese nombre en esa ciudad."
        ) from exc


@router_sucursales.patch("/{sucursal_id}/estado", response_model=SucursalAdminView)
def cambiar_estado(
    sucursal_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> SucursalAdminView:
    try:
        return SucursalesService(db).cambiar_estado(sucursal_id, payload.is_active)
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.") from exc
