"""Endpoints de CU09 — Gestionar categorías, tallas y colores.

Todos requieren un ADMINISTRADOR autenticado. Reutiliza get_current_usuario /
require_roles ya existentes (app.core.deps) — no crea un JWT ni un AuthService
nuevo. La API es JSON puro: no devuelve rutas Angular ni depende del frontend,
para que Flutter pueda consumirla igual más adelante.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.image_storage import MAX_TAMANO_BYTES, ImagenDemasiadoGrandeError, ImagenInvalidaError
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import (
    CambiarEstadoRequest,
    CategoriaOut,
    ItemCatalogoActualizar,
    ItemCatalogoCrear,
    ItemCatalogoOut,
)
from .service import (
    CategoriasService,
    ColoresService,
    NombreDuplicadoError,
    RegistroNoEncontradoError,
    TallasService,
)

require_admin = require_roles(RolUsuario.ADMINISTRADOR)

router_categorias = APIRouter(
    prefix="/categorias", tags=["CU09 - Gestionar categorías, tallas y colores"]
)
router_tallas = APIRouter(prefix="/tallas", tags=["CU09 - Gestionar categorías, tallas y colores"])
router_colores = APIRouter(prefix="/colores", tags=["CU09 - Gestionar categorías, tallas y colores"])


def _estado_a_bool(estado: str | None) -> bool | None:
    return {"active": True, "inactive": False}.get(estado)


# --------------------------------------------------------------------------
# Categorías
# --------------------------------------------------------------------------


@router_categorias.get("", response_model=list[CategoriaOut])
def listar_categorias(
    search: str | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[CategoriaOut]:
    return CategoriasService(db).listar(search=search, is_active=_estado_a_bool(estado))


@router_categorias.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    payload: ItemCatalogoCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> CategoriaOut:
    try:
        return CategoriasService(db).crear(payload)
    except NombreDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoría con ese nombre.") from exc


@router_categorias.put("/{categoria_id}", response_model=CategoriaOut)
def actualizar_categoria(
    categoria_id: int,
    payload: ItemCatalogoActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> CategoriaOut:
    try:
        return CategoriasService(db).actualizar(categoria_id, payload)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada.") from exc
    except NombreDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoría con ese nombre.") from exc


@router_categorias.patch("/{categoria_id}/estado", response_model=CategoriaOut)
def cambiar_estado_categoria(
    categoria_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> CategoriaOut:
    try:
        return CategoriasService(db).cambiar_estado(categoria_id, payload.is_active)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada.") from exc


@router_categorias.post("/{categoria_id}/imagen", response_model=CategoriaOut)
async def establecer_imagen_categoria(
    categoria_id: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> CategoriaOut:
    contenido = await archivo.read()
    try:
        return CategoriasService(db).establecer_imagen(categoria_id, archivo, contenido)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada.") from exc
    except ImagenInvalidaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "La imagen debe ser un archivo JPG, JPEG, PNG o WEBP.",
        ) from exc
    except ImagenDemasiadoGrandeError as exc:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"La imagen no puede superar los {MAX_TAMANO_BYTES // (1024 * 1024)} MB.",
        ) from exc


@router_categorias.delete("/{categoria_id}/imagen", response_model=CategoriaOut)
def eliminar_imagen_categoria(
    categoria_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> CategoriaOut:
    try:
        return CategoriasService(db).eliminar_imagen(categoria_id)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada.") from exc


# --------------------------------------------------------------------------
# Tallas
# --------------------------------------------------------------------------


@router_tallas.get("", response_model=list[ItemCatalogoOut])
def listar_tallas(
    search: str | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[ItemCatalogoOut]:
    return TallasService(db).listar(search=search, is_active=_estado_a_bool(estado))


@router_tallas.post("", response_model=ItemCatalogoOut, status_code=status.HTTP_201_CREATED)
def crear_talla(
    payload: ItemCatalogoCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> ItemCatalogoOut:
    try:
        return TallasService(db).crear(payload)
    except NombreDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una talla con ese nombre.") from exc


@router_tallas.put("/{talla_id}", response_model=ItemCatalogoOut)
def actualizar_talla(
    talla_id: int,
    payload: ItemCatalogoActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ItemCatalogoOut:
    try:
        return TallasService(db).actualizar(talla_id, payload)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Talla no encontrada.") from exc
    except NombreDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una talla con ese nombre.") from exc


@router_tallas.patch("/{talla_id}/estado", response_model=ItemCatalogoOut)
def cambiar_estado_talla(
    talla_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ItemCatalogoOut:
    try:
        return TallasService(db).cambiar_estado(talla_id, payload.is_active)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Talla no encontrada.") from exc


# --------------------------------------------------------------------------
# Colores
# --------------------------------------------------------------------------


@router_colores.get("", response_model=list[ItemCatalogoOut])
def listar_colores(
    search: str | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[ItemCatalogoOut]:
    return ColoresService(db).listar(search=search, is_active=_estado_a_bool(estado))


@router_colores.post("", response_model=ItemCatalogoOut, status_code=status.HTTP_201_CREATED)
def crear_color(
    payload: ItemCatalogoCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> ItemCatalogoOut:
    try:
        return ColoresService(db).crear(payload)
    except NombreDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un color con ese nombre.") from exc


@router_colores.put("/{color_id}", response_model=ItemCatalogoOut)
def actualizar_color(
    color_id: int,
    payload: ItemCatalogoActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ItemCatalogoOut:
    try:
        return ColoresService(db).actualizar(color_id, payload)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Color no encontrado.") from exc
    except NombreDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un color con ese nombre.") from exc


@router_colores.patch("/{color_id}/estado", response_model=ItemCatalogoOut)
def cambiar_estado_color(
    color_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ItemCatalogoOut:
    try:
        return ColoresService(db).cambiar_estado(color_id, payload.is_active)
    except RegistroNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Color no encontrado.") from exc
