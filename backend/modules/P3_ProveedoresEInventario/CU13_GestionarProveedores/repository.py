"""Acceso a datos de Proveedor necesario para Gestión de Proveedores.

Consulta el mismo modelo que expone modules/P1_SucursalesYCatalogos/Models;
no crea una tabla ni un modelo paralelo.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_proveedor import ProductoProveedor
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor


class ProveedoresRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, search: str | None = None, is_active: bool | None = None) -> list[Proveedor]:
        stmt = select(Proveedor)
        if search:
            patron = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                func.lower(Proveedor.razon_social).like(patron)
                | func.lower(Proveedor.nombre_contacto).like(patron)
                | func.lower(Proveedor.correo).like(patron)
            )
        if is_active is not None:
            stmt = stmt.where(Proveedor.is_active == is_active)
        stmt = stmt.order_by(Proveedor.razon_social)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, proveedor_id: int) -> Proveedor | None:
        return self.db.get(Proveedor, proveedor_id)

    def existe_razon_social(self, razon_social: str, excluyendo_id: int | None = None) -> bool:
        stmt = select(func.count()).select_from(Proveedor).where(
            func.lower(Proveedor.razon_social) == razon_social.strip().lower()
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Proveedor.id != excluyendo_id)
        return self.db.execute(stmt).scalar_one() > 0

    def crear(self, proveedor: Proveedor) -> Proveedor:
        self.db.add(proveedor)
        self.db.commit()
        self.db.refresh(proveedor)
        return proveedor

    def guardar(self, proveedor: Proveedor) -> Proveedor:
        self.db.commit()
        self.db.refresh(proveedor)
        return proveedor


class ProductosProveedorRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_por_proveedor(self, proveedor_id: int) -> list[ProductoProveedor]:
        stmt = (
            select(ProductoProveedor)
            .where(ProductoProveedor.proveedor_id == proveedor_id)
            .order_by(ProductoProveedor.nombre)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, producto_id: int) -> ProductoProveedor | None:
        return self.db.get(ProductoProveedor, producto_id)

    def crear(self, producto: ProductoProveedor) -> ProductoProveedor:
        self.db.add(producto)
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def guardar(self, producto: ProductoProveedor) -> ProductoProveedor:
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def get_producto_vinculado(self, producto_proveedor_id: int) -> Producto | None:
        """Producto real (CU08) ya convertido a partir de esta propuesta, si
        existe -- es la base para derivar estado PENDIENTE/APROBADO sin
        crear una máquina de estados nueva (ver PanelProveedorService)."""
        stmt = select(Producto).where(Producto.producto_proveedor_id == producto_proveedor_id)
        return self.db.execute(stmt).scalar_one_or_none()
