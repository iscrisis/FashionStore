"""Endpoints de CU10 — Gestionar temporadas y colecciones.

Todos requieren un ADMINISTRADOR autenticado. Reutiliza get_current_usuario /
require_roles ya existentes (app.core.deps) — no crea un JWT ni un AuthService
nuevo. La API es JSON puro: no devuelve rutas Angular ni depende del frontend,
para que Flutter pueda consumirla igual más adelante.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import (
    CambiarEstadoRequest,
    ColeccionActualizar,
    ColeccionCrear,
    ColeccionOut,
    TemporadaActualizar,
    TemporadaCrear,
    TemporadaOut,
)
from .service import (
    ColeccionesService,
    NombreDuplicadoError,
    RegistroNoEncontradoError,
    TemporadaNoEncontradaError,
    TemporadasService,
)

require_admin = require_roles(RolUsuario.ADMINISTRADOR)

router_temporadas = APIRouter(
    prefix="/temporadas", tags=["CU10 - Gestionar temporadas y colecciones"]
)
router_colecciones = APIRouter(
    prefix="/colecciones", tags=["CU10 - Gestionar temporadas y colecciones"]
)


def _estado_a_bool(estado: str | None) -> bool | None:
    return {"active": True, "inactive": False}.get(estado)


# --------------------------------------------------------------------------
# Temporadas
# --------------------------------------------------------------------------


@router_temporadas.get("", response_model=list[TemporadaOut])
def listar_temporadas(
    search: str | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[TemporadaOut]:
    return TemporadasService(db).listar(search=search, is_active=_estado_a_bool(estado))


@router_temporadas.post("", response_model=TemporadaOut, status_code=status.HTTP_201_CREATED)
def crear_temporada(
    payload: TemporadaCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> TemporadaOut:
    try:
        return TemporadasService(db).crear(payload)
    except NombreDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una temporada con ese nombre.") from exc


@router_temporadas.put("/{temporada_id}", response_model=TemporadaOut)
def actualizar_temporada(
    temporada_id: int,
    payload: TemporadaActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> TemporadaOut:
    try:
        return TemporadasService(db).actualizar(temporada_id, payload)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Temporada no encontrada.") from exc
    except NombreDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una temporada con ese nombre.") from exc


@router_temporadas.patch("/{temporada_id}/estado", response_model=TemporadaOut)
def cambiar_estado_temporada(
    temporada_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> TemporadaOut:
    try:
        return TemporadasService(db).cambiar_estado(temporada_id, payload.is_active)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Temporada no encontrada.") from exc


# --------------------------------------------------------------------------
# Colecciones
# --------------------------------------------------------------------------


@router_colecciones.get("", response_model=list[ColeccionOut])
def listar_colecciones(
    search: str | None = Query(default=None),
    temporada_id: int | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[ColeccionOut]:
    return ColeccionesService(db).listar(
        search=search, temporada_id=temporada_id, is_active=_estado_a_bool(estado)
    )


@router_colecciones.post("", response_model=ColeccionOut, status_code=status.HTTP_201_CREATED)
def crear_coleccion(
    payload: ColeccionCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> ColeccionOut:
    try:
        return ColeccionesService(db).crear(payload)
    except TemporadaNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La temporada indicada no existe."
        ) from exc
    except NombreDuplicadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe una colección con ese nombre en esa temporada."
        ) from exc


@router_colecciones.put("/{coleccion_id}", response_model=ColeccionOut)
def actualizar_coleccion(
    coleccion_id: int,
    payload: ColeccionActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ColeccionOut:
    try:
        return ColeccionesService(db).actualizar(coleccion_id, payload)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Colección no encontrada.") from exc
    except TemporadaNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La temporada indicada no existe."
        ) from exc
    except NombreDuplicadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe una colección con ese nombre en esa temporada."
        ) from exc


@router_colecciones.patch("/{coleccion_id}/estado", response_model=ColeccionOut)
def cambiar_estado_coleccion(
    coleccion_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ColeccionOut:
    try:
        return ColeccionesService(db).cambiar_estado(coleccion_id, payload.is_active)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Colección no encontrada.") from exc
