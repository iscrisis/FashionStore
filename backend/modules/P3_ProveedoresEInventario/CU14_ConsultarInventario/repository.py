"""Acceso a datos de CU14 -- Consultar inventario (Gestión de Stock por Sucursal).

Reutiliza Producto/ProductoVariante (CU08) y Sucursal (CU06) tal cual existen;
la única tabla nueva de este módulo es StockSucursal.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal


class SucursalLecturaRepository:
    """Solo lectura de Sucursal (CU06) para el panel del Encargado."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, sucursal_id: int) -> Sucursal | None:
        return self.db.get(Sucursal, sucursal_id)


class ProductoLecturaRepository:
    """Solo lectura de Producto/ProductoVariante (CU08) para el panel del Encargado."""

    def __init__(self, db: Session):
        self.db = db

    def listar_activos(self, search: str | None = None) -> list[Producto]:
        stmt = select(Producto).where(Producto.is_active.is_(True))
        if search:
            patron = f"%{search.strip().lower()}%"
            stmt = stmt.where(func.lower(Producto.nombre).like(patron))
        stmt = stmt.order_by(Producto.nombre)
        return list(self.db.execute(stmt).scalars().unique().all())

    def get_variante_by_id(self, variante_id: int) -> ProductoVariante | None:
        return self.db.get(ProductoVariante, variante_id)


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_por_sucursal(self, sucursal_id: int) -> dict[int, int]:
        stmt = select(StockSucursal).where(StockSucursal.sucursal_id == sucursal_id)
        filas = self.db.execute(stmt).scalars().all()
        return {fila.producto_variante_id: fila.cantidad for fila in filas}

    def get_by_sucursal_y_variante(
        self, sucursal_id: int, variante_id: int
    ) -> StockSucursal | None:
        stmt = select(StockSucursal).where(
            StockSucursal.sucursal_id == sucursal_id,
            StockSucursal.producto_variante_id == variante_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert(self, sucursal_id: int, variante_id: int, cantidad: int) -> StockSucursal:
        stock = self.get_by_sucursal_y_variante(sucursal_id, variante_id)
        if stock is None:
            stock = StockSucursal(
                sucursal_id=sucursal_id, producto_variante_id=variante_id, cantidad=cantidad
            )
            self.db.add(stock)
        else:
            stock.cantidad = cantidad
        return stock

    def guardar_todo(self) -> None:
        self.db.commit()
