"""Endpoints de Gestión de Proveedores.

Requiere un ADMINISTRADOR autenticado. Reutiliza get_current_usuario /
require_roles ya existentes (app.core.deps) — no crea un JWT ni un AuthService
nuevo. La API es JSON puro: no devuelve rutas Angular ni depende del frontend,
para que Flutter pueda consumirla igual más adelante (aunque el panel de
Proveedor en sí es un paso posterior).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import (
    CambiarEstadoRequest,
    ColeccionResumen,
    DisponibilidadRequest,
    ProductoProveedorActualizar,
    ProductoProveedorCrear,
    ProductoProveedorOut,
    ProveedorActualizar,
    ProveedorCrear,
    ProveedorOut,
    TemporadaResumen,
)
from .service import (
    ColeccionNoEncontradaError,
    ColeccionNoPerteneceATemporadaError,
    PanelProveedorService,
    ProductoNoEncontradoError,
    ProveedorNoEncontradoError,
    ProveedoresService,
    RazonSocialDuplicadaError,
    TemporadaNoEncontradaError,
)

require_admin = require_roles(RolUsuario.ADMINISTRADOR)
require_proveedor = require_roles(RolUsuario.PROVEEDOR)

router = APIRouter(prefix="/proveedores", tags=["Gestión de Proveedores"])
router_panel = APIRouter(prefix="/proveedores/panel", tags=["Panel del Proveedor"])


def _proveedor_id_del_actor(actor: Usuario) -> int:
    if actor.proveedor_id is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Esta cuenta no está vinculada a ningún proveedor."
        )
    return actor.proveedor_id


@router.get("", response_model=list[ProveedorOut])
def listar_proveedores(
    search: str | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[ProveedorOut]:
    is_active = {"active": True, "inactive": False}.get(estado)
    return ProveedoresService(db).listar(search=search, is_active=is_active)


@router.get("/{proveedor_id}", response_model=ProveedorOut)
def obtener_proveedor(
    proveedor_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> ProveedorOut:
    try:
        return ProveedoresService(db).obtener(proveedor_id)
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor no encontrado.") from exc


@router.post("", response_model=ProveedorOut, status_code=status.HTTP_201_CREATED)
def crear_proveedor(
    payload: ProveedorCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> ProveedorOut:
    try:
        return ProveedoresService(db).crear(payload)
    except RazonSocialDuplicadaError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un proveedor con esa razón social."
        ) from exc


@router.put("/{proveedor_id}", response_model=ProveedorOut)
def actualizar_proveedor(
    proveedor_id: int,
    payload: ProveedorActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ProveedorOut:
    try:
        return ProveedoresService(db).actualizar(proveedor_id, payload)
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor no encontrado.") from exc
    except RazonSocialDuplicadaError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un proveedor con esa razón social."
        ) from exc


@router.patch("/{proveedor_id}/estado", response_model=ProveedorOut)
def cambiar_estado_proveedor(
    proveedor_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ProveedorOut:
    try:
        return ProveedoresService(db).cambiar_estado(proveedor_id, payload.is_active)
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor no encontrado.") from exc


# --------------------------------------------------------------------------
# Panel del Proveedor — el proveedor_id SIEMPRE se deriva del usuario
# autenticado (actor.proveedor_id), nunca de un id recibido del cliente. Así
# un PROVEEDOR no puede ver ni modificar los datos de otro cambiando IDs.
# --------------------------------------------------------------------------


@router_panel.get("/perfil", response_model=ProveedorOut)
def obtener_mi_perfil(
    db: Session = Depends(get_db), actor: Usuario = Depends(require_proveedor)
) -> ProveedorOut:
    try:
        return PanelProveedorService(db).mi_perfil(_proveedor_id_del_actor(actor))
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor no encontrado.") from exc


@router_panel.put("/perfil", response_model=ProveedorOut)
def actualizar_mi_perfil(
    payload: ProveedorActualizar,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_proveedor),
) -> ProveedorOut:
    try:
        return PanelProveedorService(db).actualizar_mi_perfil(_proveedor_id_del_actor(actor), payload)
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor no encontrado.") from exc
    except RazonSocialDuplicadaError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un proveedor con esa razón social."
        ) from exc


@router_panel.get("/temporadas", response_model=list[TemporadaResumen])
def listar_temporadas_disponibles(
    db: Session = Depends(get_db), actor: Usuario = Depends(require_proveedor)
) -> list[TemporadaResumen]:
    _proveedor_id_del_actor(actor)
    return PanelProveedorService(db).temporadas_disponibles()


@router_panel.get("/colecciones", response_model=list[ColeccionResumen])
def listar_colecciones_disponibles(
    temporada_id: int = Query(...),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_proveedor),
) -> list[ColeccionResumen]:
    _proveedor_id_del_actor(actor)
    return PanelProveedorService(db).colecciones_disponibles(temporada_id)


@router_panel.get("/productos", response_model=list[ProductoProveedorOut])
def listar_mis_productos(
    db: Session = Depends(get_db), actor: Usuario = Depends(require_proveedor)
) -> list[ProductoProveedorOut]:
    return PanelProveedorService(db).listar_mis_productos(_proveedor_id_del_actor(actor))


@router_panel.get("/productos/{producto_id}", response_model=ProductoProveedorOut)
def obtener_mi_producto(
    producto_id: int, db: Session = Depends(get_db), actor: Usuario = Depends(require_proveedor)
) -> ProductoProveedorOut:
    try:
        return PanelProveedorService(db).obtener_mi_producto(
            _proveedor_id_del_actor(actor), producto_id
        )
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc


@router_panel.post(
    "/productos", response_model=ProductoProveedorOut, status_code=status.HTTP_201_CREATED
)
def enviar_producto(
    payload: ProductoProveedorCrear,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_proveedor),
) -> ProductoProveedorOut:
    try:
        return PanelProveedorService(db).crear_producto(_proveedor_id_del_actor(actor), payload)
    except TemporadaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La temporada indicada no existe.") from exc
    except ColeccionNoEncontradaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La colección indicada no existe.") from exc
    except ColeccionNoPerteneceATemporadaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La colección no pertenece a la temporada indicada."
        ) from exc


@router_panel.put("/productos/{producto_id}", response_model=ProductoProveedorOut)
def actualizar_mi_producto(
    producto_id: int,
    payload: ProductoProveedorActualizar,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_proveedor),
) -> ProductoProveedorOut:
    try:
        return PanelProveedorService(db).actualizar_producto(
            _proveedor_id_del_actor(actor), producto_id, payload
        )
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc
    except TemporadaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La temporada indicada no existe.") from exc
    except ColeccionNoEncontradaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La colección indicada no existe.") from exc
    except ColeccionNoPerteneceATemporadaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La colección no pertenece a la temporada indicada."
        ) from exc


@router_panel.patch("/productos/{producto_id}/disponibilidad", response_model=ProductoProveedorOut)
def cambiar_disponibilidad_producto(
    producto_id: int,
    payload: DisponibilidadRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_proveedor),
) -> ProductoProveedorOut:
    try:
        return PanelProveedorService(db).cambiar_disponibilidad(
            _proveedor_id_del_actor(actor), producto_id, payload.disponibilidad
        )
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc


@router_panel.patch("/productos/{producto_id}/estado", response_model=ProductoProveedorOut)
def cambiar_estado_producto(
    producto_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_proveedor),
) -> ProductoProveedorOut:
    try:
        return PanelProveedorService(db).cambiar_estado_producto(
            _proveedor_id_del_actor(actor), producto_id, payload.is_active
        )
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc
