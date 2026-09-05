"""Endpoints de CU11 -- Consultar catálogo de prendas.

Públicos: NO requieren sesión ni rol -- Invitado o Cliente los consulta sin
iniciar sesión (a diferencia de CU06/CU08/CU09/CU10/GestionProveedores, que sí
exigen un ADMINISTRADOR). Son de solo lectura -- crear/editar/eliminar sigue
siendo exclusivo de esos casos de uso administrativos; CU11 no los duplica,
solo lee lo que ya publicaron como activo.

JSON neutral y estable (ids + nombres, precio numérico, URLs de imagen ya
resueltas por el backend): pensado para que Angular lo consuma hoy y Flutter
lo reutilice después sin cambiar esta lógica.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from .schemas import CategoriaOut, ColeccionOut, ColorOut, ProductoOut, TallaOut
from .service import CatalogoPublicoService, ProductoNoEncontradoError

router = APIRouter(prefix="/catalogo", tags=["CU11 - Consultar catálogo de prendas"])


@router.get("/categorias", response_model=list[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)) -> list[CategoriaOut]:
    return CatalogoPublicoService(db).listar_categorias()


@router.get("/colecciones", response_model=list[ColeccionOut])
def listar_colecciones(
    temporada_id: int | None = Query(default=None), db: Session = Depends(get_db)
) -> list[ColeccionOut]:
    return CatalogoPublicoService(db).listar_colecciones(temporada_id=temporada_id)


@router.get("/tallas", response_model=list[TallaOut])
def listar_tallas(db: Session = Depends(get_db)) -> list[TallaOut]:
    return CatalogoPublicoService(db).listar_tallas()


@router.get("/colores", response_model=list[ColorOut])
def listar_colores(db: Session = Depends(get_db)) -> list[ColorOut]:
    return CatalogoPublicoService(db).listar_colores()


@router.get("/productos", response_model=list[ProductoOut])
def listar_productos(
    search: str | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    coleccion_id: int | None = Query(default=None),
    talla_id: int | None = Query(default=None),
    color_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ProductoOut]:
    return CatalogoPublicoService(db).listar_productos(
        search=search,
        categoria_id=categoria_id,
        coleccion_id=coleccion_id,
        talla_id=talla_id,
        color_id=color_id,
    )


@router.get("/productos/{producto_id}", response_model=ProductoOut)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)) -> ProductoOut:
    try:
        return CatalogoPublicoService(db).obtener_producto(producto_id)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc
