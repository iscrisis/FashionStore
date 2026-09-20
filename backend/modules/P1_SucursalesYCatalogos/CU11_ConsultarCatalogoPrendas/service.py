"""Reglas de negocio de CU11 -- Consultar catálogo de prendas (público).

Sin autenticación: cualquier Invitado o Cliente puede consultarlo. Solo lee
lo que CU08/CU09/CU10 ya publicaron como activo -- no administra nada.

precio_base/precio_final/en_promocion/porcentaje_descuento (CU32) se
calculan SIEMPRE con `precio_efectivo.py` -- este módulo nunca implementa su
propia fórmula de descuento (ver docstring de ese archivo).
"""

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P6_InnovacionYAnalisis.CU32_GestionarPromociones.precio_efectivo import (
    obtener_precio_efectivo,
    obtener_precios_efectivos,
)

from .repository import CatalogoPublicoRepository
from .schemas import (
    CategoriaOut,
    ColeccionOut,
    ColorOut,
    ProductoImagenOut,
    ProductoOut,
    TallaOut,
    TemporadaOut,
)


class ProductoNoEncontradoError(Exception):
    pass


class CatalogoPublicoService:
    def __init__(self, db: Session):
        self._db = db
        self._repo = CatalogoPublicoRepository(db)

    def listar_categorias(self) -> list[Categoria]:
        return self._repo.listar_categorias_activas()

    def listar_colecciones(self, temporada_id: int | None = None) -> list[Coleccion]:
        return self._repo.listar_colecciones_activas(temporada_id)

    def listar_tallas(self) -> list[Talla]:
        return self._repo.listar_tallas_activas()

    def listar_colores(self) -> list[Color]:
        return self._repo.listar_colores_activos()

    def listar_productos(
        self,
        search: str | None = None,
        categoria_id: int | None = None,
        coleccion_id: int | None = None,
        talla_id: int | None = None,
        color_id: int | None = None,
    ) -> list[ProductoOut]:
        productos = self._repo.listar_productos(
            search=search,
            categoria_id=categoria_id,
            coleccion_id=coleccion_id,
            talla_id=talla_id,
            color_id=color_id,
        )
        precios = obtener_precios_efectivos(self._db, productos)
        return [_producto_a_salida(p, precios[p.id]) for p in productos]

    def obtener_producto(self, producto_id: int) -> ProductoOut:
        producto = self._repo.obtener_producto_activo(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError
        precio = obtener_precio_efectivo(self._db, producto)
        return _producto_a_salida(producto, precio)


def _producto_a_salida(producto: Producto, precio) -> ProductoOut:
    return ProductoOut(
        id=producto.id,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio_venta=producto.precio_venta,
        precio_base=precio.precio_base,
        precio_final=precio.precio_final,
        en_promocion=precio.en_promocion,
        porcentaje_descuento=precio.porcentaje_descuento,
        imagen_principal_url=producto.imagen_principal_url,
        imagenes=[ProductoImagenOut.model_validate(i) for i in producto.imagenes],
        categoria=CategoriaOut.model_validate(producto.categoria),
        temporada=TemporadaOut.model_validate(producto.temporada),
        coleccion=ColeccionOut.model_validate(producto.coleccion),
        tallas=[TallaOut.model_validate(t) for t in producto.tallas],
        colores=[ColorOut.model_validate(c) for c in producto.colores],
    )
