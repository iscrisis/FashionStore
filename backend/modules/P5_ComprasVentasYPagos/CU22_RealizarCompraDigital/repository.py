"""Acceso a datos de CU22 -- Realizar compra digital (Cliente).

Reutiliza Carrito/CarritoItem (CU21, en SOLO LECTURA -- CU22 nunca escribe
en el carrito, ver service.py), Sucursal (CU06/CU07), ProductoVariante/
Producto (CU08) y StockSucursal (CU14/15/16, también en SOLO LECTURA -- CU22
solo valida disponibilidad, nunca reserva ni descuenta stock). La única
tabla propia de este módulo es Venta (cabecera) + VentaDetalle.

`disponible_por_sucursales` trae, en UNA sola consulta, el disponible
(`cantidad - stock_reservado`) de cada combinación sucursal+variante que
importa -- evita una consulta por sucursal al armar la lista de "elige tu
sucursal de retiro" (mismo criterio de UNA sola consulta ya aplicado en
CU21_UsarCarritoCompras/repository.py:get_activos_by_ids tras corregir su
N+1 original).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P5_ComprasVentasYPagos.Models.carrito import Carrito, CarritoItem
from modules.P5_ComprasVentasYPagos.Models.venta import Venta


class CarritoLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_cliente(self, cliente_id: int) -> Carrito | None:
        """Solo lectura -- CU22 nunca crea, bloquea (FOR UPDATE) ni muta el
        carrito: los items comprados siguen intactos hasta que CU23 decida
        retirarlos (ver docstring del paquete)."""
        stmt = (
            select(Carrito)
            .where(Carrito.cliente_id == cliente_id)
            .options(selectinload(Carrito.items).selectinload(CarritoItem.producto_variante))
        )
        return self.db.execute(stmt).scalar_one_or_none()


class ProductoLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_activos_by_ids(self, producto_ids: set[int]) -> dict[int, Producto]:
        if not producto_ids:
            return {}
        stmt = select(Producto).where(Producto.id.in_(producto_ids), Producto.is_active.is_(True))
        return {p.id: p for p in self.db.execute(stmt).scalars()}


class SucursalLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_activas_por_ciudad(self, ciudad_id: int) -> list[Sucursal]:
        stmt = (
            select(Sucursal)
            .where(Sucursal.ciudad_id == ciudad_id, Sucursal.is_active.is_(True))
            .order_by(Sucursal.nombre)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_activa_by_id(self, sucursal_id: int) -> Sucursal | None:
        stmt = select(Sucursal).where(Sucursal.id == sucursal_id, Sucursal.is_active.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def disponible_por_sucursales(
        self, sucursal_ids: list[int], variante_ids: list[int]
    ) -> dict[int, dict[int, int]]:
        """{sucursal_id: {producto_variante_id: disponible}} -- SELECT puro,
        sin FOR UPDATE: CU22 nunca escribe stock, solo lo lee para decidir
        qué sucursal(es) pueden cubrir TODA la compra (ver
        CompraDigitalService.sucursales_disponibles y .confirmar, que vuelve
        a llamar esto mismo justo antes de crear la Venta para no confiar en
        información vieja del frontend)."""
        if not sucursal_ids or not variante_ids:
            return {}
        stmt = select(
            StockSucursal.sucursal_id,
            StockSucursal.producto_variante_id,
            (StockSucursal.cantidad - StockSucursal.stock_reservado),
        ).where(
            StockSucursal.sucursal_id.in_(sucursal_ids),
            StockSucursal.producto_variante_id.in_(variante_ids),
        )
        resultado: dict[int, dict[int, int]] = {}
        for sucursal_id, variante_id, disponible in self.db.execute(stmt).all():
            resultado.setdefault(sucursal_id, {})[variante_id] = disponible
        return resultado


class VentaRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, venta: Venta) -> Venta:
        """Mismo patrón ya usado por ReservaRepository.crear (CU17): genera
        el `codigo_venta` a partir del id definitivo, con un placeholder
        único mientras tanto (NOT NULL en la base, se reemplaza antes de
        confirmar -- nadie llega a ver ese valor temporal). Un único commit
        deja cabecera + detalles + código definitivo consistentes."""
        venta.codigo_venta = uuid.uuid4().hex[:20]
        self.db.add(venta)
        self.db.flush()
        venta.codigo_venta = f"VT-{venta.id:05d}"
        self.db.commit()
        self.db.refresh(venta)
        return venta
