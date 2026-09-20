"""Acceso de solo lectura para CU12 -- Consultar disponibilidad por sucursal.

Lee Producto/ProductoVariante (CU08) y Sucursal (CU06) tal cual existen, y
StockSucursal -- la misma tabla que ya escribe el Encargado (ver
CU14_ConsultarInventario) -- como fuente real de cantidades. No crea ninguna
tabla ni duplica stock.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal


class DisponibilidadLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_producto_activo(self, producto_id: int) -> Producto | None:
        stmt = select(Producto).where(Producto.id == producto_id, Producto.is_active.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()

    def listar_sucursales_activas(self, ciudad_id: int | None) -> list[Sucursal]:
        stmt = select(Sucursal).where(Sucursal.is_active.is_(True))
        if ciudad_id is not None:
            stmt = stmt.where(Sucursal.ciudad_id == ciudad_id)
        stmt = stmt.order_by(Sucursal.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def cantidades_por_variantes(self, variante_ids: list[int]) -> dict[tuple[int, int], int]:
        """{(sucursal_id, producto_variante_id): disponible} para las variantes
        dadas. "Disponible" es SIEMPRE cantidad - stock_reservado (nunca el
        stock físico crudo): stock_reservado lo escribe CU17 al crear una
        reserva PENDIENTE (ver Models/stock_sucursal.py) -- una unidad
        reservada no debe seguir apareciendo como disponible para reservar de
        nuevo, aunque el físico no haya cambiado. Se aplica max(0, ...) por
        higiene defensiva: si el Encargado (CU14) redujera `cantidad` por
        debajo de lo ya reservado, esto nunca debe mostrarse como negativo."""
        if not variante_ids:
            return {}
        stmt = select(StockSucursal).where(StockSucursal.producto_variante_id.in_(variante_ids))
        filas = self.db.execute(stmt).scalars().all()
        return {
            (fila.sucursal_id, fila.producto_variante_id): max(0, fila.cantidad - fila.stock_reservado)
            for fila in filas
        }
