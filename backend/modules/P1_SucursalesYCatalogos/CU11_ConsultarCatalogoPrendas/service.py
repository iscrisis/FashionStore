"""Reglas de negocio de CU11 -- Consultar catálogo de prendas (público).

Sin autenticación: cualquier Invitado o Cliente puede consultarlo. Solo lee
lo que CU08/CU09/CU10 ya publicaron como activo -- no administra nada.
"""

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.talla import Talla

from .repository import CatalogoPublicoRepository


class ProductoNoEncontradoError(Exception):
    pass


class CatalogoPublicoService:
    def __init__(self, db: Session):
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
    ) -> list[Producto]:
        return self._repo.listar_productos(
            search=search,
            categoria_id=categoria_id,
            coleccion_id=coleccion_id,
            talla_id=talla_id,
            color_id=color_id,
        )

    def obtener_producto(self, producto_id: int) -> Producto:
        producto = self._repo.obtener_producto_activo(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError
        return producto
