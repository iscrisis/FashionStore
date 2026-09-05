"""Acceso de solo lectura al catálogo público -- CU11.

Lee los mismos modelos que administran CU08 (Producto), CU09 (Categoria,
Talla, Color) y CU10 (Temporada, Coleccion); no los duplica ni los modifica.
Solo devuelve lo que el Administrador ya marcó como activo.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.talla import Talla


class CatalogoPublicoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_categorias_activas(self) -> list[Categoria]:
        stmt = select(Categoria).where(Categoria.is_active.is_(True)).order_by(Categoria.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def listar_colecciones_activas(self, temporada_id: int | None = None) -> list[Coleccion]:
        stmt = select(Coleccion).where(Coleccion.is_active.is_(True))
        if temporada_id is not None:
            stmt = stmt.where(Coleccion.temporada_id == temporada_id)
        stmt = stmt.order_by(Coleccion.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def listar_tallas_activas(self) -> list[Talla]:
        stmt = select(Talla).where(Talla.is_active.is_(True)).order_by(Talla.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def listar_colores_activos(self) -> list[Color]:
        stmt = select(Color).where(Color.is_active.is_(True)).order_by(Color.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def listar_productos(
        self,
        search: str | None = None,
        categoria_id: int | None = None,
        coleccion_id: int | None = None,
        talla_id: int | None = None,
        color_id: int | None = None,
    ) -> list[Producto]:
        stmt = select(Producto).where(Producto.is_active.is_(True))
        if search:
            stmt = stmt.where(func.lower(Producto.nombre).like(f"%{search.strip().lower()}%"))
        if categoria_id is not None:
            stmt = stmt.where(Producto.categoria_id == categoria_id)
        if coleccion_id is not None:
            stmt = stmt.where(Producto.coleccion_id == coleccion_id)
        if talla_id is not None:
            stmt = stmt.where(Producto.tallas.any(Talla.id == talla_id))
        if color_id is not None:
            stmt = stmt.where(Producto.colores.any(Color.id == color_id))
        stmt = stmt.order_by(Producto.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def obtener_producto_activo(self, producto_id: int) -> Producto | None:
        stmt = select(Producto).where(Producto.id == producto_id, Producto.is_active.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()
