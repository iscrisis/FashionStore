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


@router_ciudades.delete("/{ciudad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ciudad(
    ciudad_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> None:
    try:
        CiudadesService(db).eliminar(ciudad_id)
    except CiudadNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ciudad no encontrada.") from exc


@router_sucursales.get("", response_model=list[SucursalAdminView])
def listar_sucursales(
    search: str | None = Query(default=None),
    ciudad_id: int | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_admin),
) -> list[SucursalAdminView]:
    is_active = {"active": True, "inactive": False}.get(estado)
    return SucursalesService(db).listar(usuario=actor, search=search, ciudad_id=ciudad_id, is_active=is_active)


@router_sucursales.get("/{sucursal_id}", response_model=SucursalAdminView)
def obtener_sucursal(
    sucursal_id: int, db: Session = Depends(get_db), actor: Usuario = Depends(require_admin)
) -> SucursalAdminView:
    try:
        return SucursalesService(db).obtener(usuario=actor, sucursal_id=sucursal_id)
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.") from exc


@router_sucursales.post("", response_model=SucursalAdminView, status_code=status.HTTP_201_CREATED)
def crear_sucursal(
    payload: SucursalCrear, db: Session = Depends(get_db), actor: Usuario = Depends(require_admin)
) -> SucursalAdminView:
    try:
        return SucursalesService(db).crear(usuario=actor, datos=payload)
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
    actor: Usuario = Depends(require_admin),
) -> SucursalAdminView:
    try:
        return SucursalesService(db).actualizar(usuario=actor, sucursal_id=sucursal_id, datos=payload)
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
    actor: Usuario = Depends(require_admin),
) -> SucursalAdminView:
    try:
        return SucursalesService(db).cambiar_estado(usuario=actor, sucursal_id=sucursal_id, activo=payload.is_active)
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.") from exc


@router_sucursales.delete("/{sucursal_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sucursal(
    sucursal_id: int, db: Session = Depends(get_db), actor: Usuario = Depends(require_admin)
) -> None:
    try:
        SucursalesService(db).eliminar(usuario=actor, sucursal_id=sucursal_id)
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.") from exc


@router_sucursales.get("/_diag/orm-relation")
def diagnose_orm_relation(db: Session = Depends(get_db), _: Usuario = Depends(require_admin)):
    """TEMPORAL: Diagnóstico de relación Sucursal.ciudad"""
    from sqlalchemy import inspect, select, and_
    from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad

    result = {"stages": []}

    try:
        rel = inspect(Sucursal).relationships.get('ciudad')
        if rel:
            result["stages"].append({
                "stage": "Mapper",
                "lazy": rel.lazy,
                "viewonly": rel.viewonly,
                "foreign_keys_count": len(rel.foreign_keys)
            })

        sucursal = db.execute(select(Sucursal).limit(1)).scalar_one_or_none()
        if not sucursal:
            result["stages"].append({"stage": "No sucursales"})
            return result

        result["stages"].append({
            "stage": "Sucursal",
            "id": sucursal.id,
            "empresa_id": sucursal.empresa_id,
            "ciudad_id": sucursal.ciudad_id
        })

        ciudad_orm = sucursal.ciudad
        result["stages"].append({
            "stage": "ORM Access",
            "ciudad_orm_is_none": ciudad_orm is None
        })

        ciudad_manual = db.query(Ciudad).filter(
            (Ciudad.id == sucursal.ciudad_id) &
            (Ciudad.empresa_id == sucursal.empresa_id)
        ).first()

        result["stages"].append({
            "stage": "Manual Query",
            "ciudad_found": ciudad_manual is not None
        })

        result_join = db.execute(
            select(Sucursal).outerjoin(
                Ciudad,
                and_(
                    Sucursal.ciudad_id == Ciudad.id,
                    Sucursal.empresa_id == Ciudad.empresa_id
                )
            ).where(Sucursal.id == sucursal.id)
        ).unique().scalar_one()

        result["stages"].append({
            "stage": "After JOIN",
            "ciudad_is_none": result_join.ciudad is None
        })

        result["conclusion"] = {
            "orm_works": ciudad_orm is not None,
            "manual_works": ciudad_manual is not None,
            "join_works": result_join.ciudad is not None
        }

    except Exception as e:
        result["error"] = str(e)

    return result
