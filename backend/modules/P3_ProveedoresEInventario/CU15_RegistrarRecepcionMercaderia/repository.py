"""Acceso a datos de CU15 -- Registrar recepción de mercadería (Panel del Encargado).

Reutiliza Proveedor (CU13) y Producto/ProductoVariante (CU08) tal cual
existen, en solo lectura. Las únicas tablas nuevas de este módulo son
RecepcionMercaderia y DetalleRecepcionMercaderia.

El incremento de StockSucursal vive en SU PROPIO repositorio (más abajo) en
lugar de reutilizar el de CU14: CU14 expone un upsert que FIJA la cantidad
(uso: corrección manual de inventario); CU15 siempre SUMA la cantidad
recibida, una operación distinta que no debe alterar el contrato de CU14.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.recepcion_mercaderia import RecepcionMercaderia
from modules.P1_SucursalesYCatalogos.Models.detalle_recepcion_mercaderia import (
    DetalleRecepcionMercaderia,
)
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal


class ProveedorLecturaRepository:
    """Solo lectura de Proveedor (CU13) para el panel del Encargado."""

    def __init__(self, db: Session):
        self.db = db

    def listar_activos(self) -> list[Proveedor]:
        stmt = select(Proveedor).where(Proveedor.is_active.is_(True)).order_by(Proveedor.razon_social)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, proveedor_id: int) -> Proveedor | None:
        return self.db.get(Proveedor, proveedor_id)


class ProductoLecturaRepository:
    """Solo lectura de Producto/ProductoVariante (CU08) para el panel del Encargado."""

    def __init__(self, db: Session):
        self.db = db

    def listar_por_proveedor(self, proveedor_id: int) -> list[Producto]:
        stmt = (
            select(Producto)
            .where(Producto.proveedor_id == proveedor_id, Producto.is_active.is_(True))
            .order_by(Producto.nombre)
        )
        return list(self.db.execute(stmt).scalars().unique().all())

    def get_by_id(self, producto_id: int) -> Producto | None:
        return self.db.get(Producto, producto_id)

    def get_variante_by_id(self, variante_id: int) -> ProductoVariante | None:
        return self.db.get(ProductoVariante, variante_id)


class StockSucursalIncrementoRepository:
    """Escritura de StockSucursal propia de CU15: siempre SUMA, nunca reemplaza."""

    def __init__(self, db: Session):
        self.db = db

    def _get(self, sucursal_id: int, variante_id: int) -> StockSucursal | None:
        stmt = select(StockSucursal).where(
            StockSucursal.sucursal_id == sucursal_id,
            StockSucursal.producto_variante_id == variante_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def incrementar(self, sucursal_id: int, variante_id: int, cantidad: int) -> StockSucursal:
        stock = self._get(sucursal_id, variante_id)
        if stock is None:
            stock = StockSucursal(
                sucursal_id=sucursal_id, producto_variante_id=variante_id, cantidad=cantidad
            )
            self.db.add(stock)
        else:
            stock.cantidad = stock.cantidad + cantidad
        return stock


class RecepcionMercaderiaRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, recepcion: RecepcionMercaderia) -> RecepcionMercaderia:
        self.db.add(recepcion)
        self.db.flush()
        return recepcion

    def agregar_detalle(self, detalle: DetalleRecepcionMercaderia) -> None:
        self.db.add(detalle)

    def confirmar(self) -> None:
        self.db.commit()

    def descartar(self) -> None:
        self.db.rollback()
