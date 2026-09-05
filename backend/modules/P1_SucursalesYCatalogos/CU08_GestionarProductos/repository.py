"""Acceso a datos de CU08 -- Gestionar productos.

Consulta el mismo modelo Producto que expone modules/P1_SucursalesYCatalogos/
Models; no crea una tabla ni un modelo paralelo. También lee (sin
administrar) Proveedor, Categoria, Temporada, Coleccion, Talla, Color y
ProductoProveedor -- entidades ya gobernadas por GestionProveedores, CU09 y
CU10 -- para validar y resolver las referencias del producto.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_proveedor import ProductoProveedor
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada


class ProductosRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(
        self,
        search: str | None = None,
        categoria_id: int | None = None,
        temporada_id: int | None = None,
        coleccion_id: int | None = None,
        proveedor_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[Producto]:
        stmt = select(Producto)
        if search:
            stmt = stmt.where(func.lower(Producto.nombre).like(f"%{search.strip().lower()}%"))
        if categoria_id is not None:
            stmt = stmt.where(Producto.categoria_id == categoria_id)
        if temporada_id is not None:
            stmt = stmt.where(Producto.temporada_id == temporada_id)
        if coleccion_id is not None:
            stmt = stmt.where(Producto.coleccion_id == coleccion_id)
        if proveedor_id is not None:
            stmt = stmt.where(Producto.proveedor_id == proveedor_id)
        if is_active is not None:
            stmt = stmt.where(Producto.is_active == is_active)
        stmt = stmt.order_by(Producto.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, producto_id: int) -> Producto | None:
        return self.db.get(Producto, producto_id)

    def existe_producto_proveedor_vinculado(
        self, producto_proveedor_id: int, excluyendo_id: int | None = None
    ) -> bool:
        stmt = select(func.count()).select_from(Producto).where(
            Producto.producto_proveedor_id == producto_proveedor_id
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Producto.id != excluyendo_id)
        return self.db.execute(stmt).scalar_one() > 0

    def crear(self, producto: Producto) -> Producto:
        self.db.add(producto)
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def guardar(self, producto: Producto) -> Producto:
        self.db.commit()
        self.db.refresh(producto)
        return producto


class CatalogoLecturaRepository:
    """Solo lectura de Proveedor, Categoria, Temporada, Coleccion, Talla y
    Color para validar y resolver las referencias del producto -- CU08 no
    administra ninguno de estos catálogos, eso ya lo hacen GestionProveedores,
    CU09 y CU10."""

    def __init__(self, db: Session):
        self.db = db

    def get_proveedor(self, proveedor_id: int) -> Proveedor | None:
        return self.db.get(Proveedor, proveedor_id)

    def get_categoria(self, categoria_id: int) -> Categoria | None:
        return self.db.get(Categoria, categoria_id)

    def get_temporada(self, temporada_id: int) -> Temporada | None:
        return self.db.get(Temporada, temporada_id)

    def get_coleccion(self, coleccion_id: int) -> Coleccion | None:
        return self.db.get(Coleccion, coleccion_id)

    def get_tallas_por_ids(self, talla_ids: list[int]) -> list[Talla]:
        if not talla_ids:
            return []
        stmt = select(Talla).where(Talla.id.in_(talla_ids))
        return list(self.db.execute(stmt).scalars().all())

    def get_colores_por_ids(self, color_ids: list[int]) -> list[Color]:
        if not color_ids:
            return []
        stmt = select(Color).where(Color.id.in_(color_ids))
        return list(self.db.execute(stmt).scalars().all())


class PropuestasProveedorRepository:
    """Solo lectura de ProductoProveedor (propuestas enviadas por
    proveedores) para que el Administrador las convierta en un producto de
    FashionStore -- no administra proveedores ni sus propuestas, eso sigue
    siendo responsabilidad de GestionProveedores."""

    def __init__(self, db: Session):
        self.db = db

    def listar_disponibles(
        self, proveedor_id: int | None = None
    ) -> list[tuple[ProductoProveedor, Proveedor]]:
        ya_convertida = select(Producto.producto_proveedor_id).where(
            Producto.producto_proveedor_id.is_not(None)
        )
        stmt = (
            select(ProductoProveedor, Proveedor)
            .join(Proveedor, Proveedor.id == ProductoProveedor.proveedor_id)
            .where(
                ProductoProveedor.is_active.is_(True),
                ProductoProveedor.id.not_in(ya_convertida),
            )
        )
        if proveedor_id is not None:
            stmt = stmt.where(ProductoProveedor.proveedor_id == proveedor_id)
        stmt = stmt.order_by(ProductoProveedor.nombre)
        return [tuple(fila) for fila in self.db.execute(stmt).all()]

    def get_by_id(self, producto_proveedor_id: int) -> ProductoProveedor | None:
        return self.db.get(ProductoProveedor, producto_proveedor_id)
