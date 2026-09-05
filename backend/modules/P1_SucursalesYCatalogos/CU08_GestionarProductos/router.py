"""Endpoints de CU08 -- Gestionar productos.

Todos requieren un ADMINISTRADOR autenticado. Reutiliza get_current_usuario /
require_roles ya existentes (app.core.deps) -- no crea un JWT ni un
AuthService nuevo. La API es JSON puro: no devuelve rutas Angular ni depende
del frontend, para que Flutter (Cliente) pueda consumir el mismo catálogo más
adelante.
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
    ProductoActualizar,
    ProductoCrear,
    ProductoOut,
    PropuestaProveedorOut,
)
from .service import (
    CategoriaNoEncontradaError,
    ColeccionNoEncontradaError,
    ColeccionNoPerteneceATemporadaError,
    ColorInvalidoError,
    ImagenNoEncontradaError,
    ProductoNoEncontradoError,
    ProductosService,
    PropuestaNoEncontradaError,
    PropuestaNoPerteneceAProveedorError,
    PropuestaYaConvertidaError,
    ProveedorNoEncontradoError,
    TallaInvalidaError,
    TemporadaNoEncontradaError,
)

require_admin = require_roles(RolUsuario.ADMINISTRADOR)

router = APIRouter(prefix="/productos", tags=["CU08 - Gestionar productos"])


def _estado_a_bool(estado: str | None) -> bool | None:
    return {"active": True, "inactive": False}.get(estado)


@router.get("", response_model=list[ProductoOut])
def listar_productos(
    search: str | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    temporada_id: int | None = Query(default=None),
    coleccion_id: int | None = Query(default=None),
    proveedor_id: int | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[ProductoOut]:
    return ProductosService(db).listar(
        search=search,
        categoria_id=categoria_id,
        temporada_id=temporada_id,
        coleccion_id=coleccion_id,
        proveedor_id=proveedor_id,
        is_active=_estado_a_bool(estado),
    )


@router.get("/propuestas", response_model=list[PropuestaProveedorOut])
def listar_propuestas_disponibles(
    proveedor_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[PropuestaProveedorOut]:
    """Propuestas de proveedor (ProductoProveedor) activas y todavía no
    convertidas en un producto -- para que el Administrador elija una y
    reutilice sus datos al registrar el producto."""
    return ProductosService(db).listar_propuestas(proveedor_id=proveedor_id)


@router.get("/{producto_id}", response_model=ProductoOut)
def obtener_producto(
    producto_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> ProductoOut:
    try:
        return ProductosService(db).obtener(producto_id)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc


@router.post("", response_model=ProductoOut, status_code=status.HTTP_201_CREATED)
def crear_producto(
    payload: ProductoCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> ProductoOut:
    try:
        return ProductosService(db).crear(payload)
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "El proveedor indicado no existe."
        ) from exc
    except CategoriaNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La categoría indicada no existe."
        ) from exc
    except TemporadaNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La temporada indicada no existe."
        ) from exc
    except ColeccionNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La colección indicada no existe."
        ) from exc
    except ColeccionNoPerteneceATemporadaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La colección no pertenece a la temporada indicada."
        ) from exc
    except TallaInvalidaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Alguna talla indicada no existe.") from exc
    except ColorInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Algún color indicado no existe.") from exc
    except PropuestaNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La propuesta indicada no existe."
        ) from exc
    except PropuestaNoPerteneceAProveedorError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La propuesta no pertenece al proveedor indicado."
        ) from exc
    except PropuestaYaConvertidaError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Esa propuesta ya fue convertida en un producto."
        ) from exc


@router.put("/{producto_id}", response_model=ProductoOut)
def actualizar_producto(
    producto_id: int,
    payload: ProductoActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ProductoOut:
    try:
        return ProductosService(db).actualizar(producto_id, payload)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "El proveedor indicado no existe."
        ) from exc
    except CategoriaNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La categoría indicada no existe."
        ) from exc
    except TemporadaNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La temporada indicada no existe."
        ) from exc
    except ColeccionNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La colección indicada no existe."
        ) from exc
    except ColeccionNoPerteneceATemporadaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La colección no pertenece a la temporada indicada."
        ) from exc
    except TallaInvalidaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Alguna talla indicada no existe.") from exc
    except ColorInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Algún color indicado no existe.") from exc
    except PropuestaNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La propuesta indicada no existe."
        ) from exc
    except PropuestaNoPerteneceAProveedorError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La propuesta no pertenece al proveedor indicado."
        ) from exc
    except PropuestaYaConvertidaError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Esa propuesta ya fue convertida en un producto."
        ) from exc


@router.patch("/{producto_id}/estado", response_model=ProductoOut)
def cambiar_estado_producto(
    producto_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ProductoOut:
    try:
        return ProductosService(db).cambiar_estado(producto_id, payload.is_active)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc


# --------------------------------------------------------------------------
# Imágenes -- imagen principal (obligatoria) e imágenes adicionales
# (opcionales). Se suben por separado del resto del producto: ver
# app/core/image_storage.py.
# --------------------------------------------------------------------------


@router.post("/{producto_id}/imagen-principal", response_model=ProductoOut)
async def establecer_imagen_principal(
    producto_id: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ProductoOut:
    contenido = await archivo.read()
    try:
        return ProductosService(db).establecer_imagen_principal(producto_id, archivo, contenido)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc
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


@router.post("/{producto_id}/imagenes", response_model=ProductoOut, status_code=status.HTTP_201_CREATED)
async def agregar_imagen_producto(
    producto_id: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ProductoOut:
    contenido = await archivo.read()
    try:
        return ProductosService(db).agregar_imagen(producto_id, archivo, contenido)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc
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


@router.delete("/{producto_id}/imagenes/{imagen_id}", response_model=ProductoOut)
def eliminar_imagen_producto(
    producto_id: int,
    imagen_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ProductoOut:
    try:
        return ProductosService(db).eliminar_imagen(producto_id, imagen_id)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc
    except ImagenNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imagen no encontrada.") from exc
