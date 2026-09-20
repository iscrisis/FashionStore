"""Acceso a datos de CU23 -- Procesar pago electrónico (Cliente).

Reutiliza Venta/VentaDetalle (CU22) y StockSucursal (CU14/15/16) tal cual
existen. La única tabla propia de este módulo es Pago.

`bloquear_venta_por_id` usa SELECT ... FOR UPDATE sobre la fila Venta misma
a propósito: verificar_pago siempre bloquea PRIMERO la cabecera (mismo orden
que CU17/CU22 -- cabecera antes que stock) antes de descontar
StockSucursal.cantidad o marcarla PAGADA, así dos verificaciones
concurrentes de la MISMA Venta (doble pestaña, el navegador reintentando el
mismo request) nunca descuentan stock dos veces ni duplican la eliminación
de items del carrito (ver CompraElectronicaService.verificar_pago).
"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P5_ComprasVentasYPagos.Models.carrito import CarritoItem
from modules.P5_ComprasVentasYPagos.Models.pago import Pago
from modules.P5_ComprasVentasYPagos.Models.venta import Venta, VentaDetalle


class VentaLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, venta_id: int) -> Venta | None:
        stmt = (
            select(Venta)
            .where(Venta.id == venta_id)
            .options(selectinload(Venta.detalles).selectinload(VentaDetalle.producto_variante))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def bloquear_por_id(self, venta_id: int) -> Venta | None:
        stmt = (
            select(Venta)
            .where(Venta.id == venta_id)
            .options(selectinload(Venta.detalles).selectinload(VentaDetalle.producto_variante))
            .with_for_update(of=Venta)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def refrescar(self, venta: Venta) -> None:
        self.db.refresh(venta)


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def disponible_por_variantes(self, sucursal_id: int, variante_ids: list[int]) -> dict[int, int]:
        """SELECT puro (sin FOR UPDATE) -- para la validación temprana en
        crear_checkout, antes de tocar Stripe. La validación definitiva,
        justo antes de descontar, usa `bloquear_filas` (ver abajo)."""
        if not variante_ids:
            return {}
        stmt = select(StockSucursal.producto_variante_id, (StockSucursal.cantidad - StockSucursal.stock_reservado)).where(
            StockSucursal.sucursal_id == sucursal_id,
            StockSucursal.producto_variante_id.in_(variante_ids),
        )
        return dict(self.db.execute(stmt).all())

    def bloquear_filas(self, sucursal_id: int, variante_ids: list[int]) -> dict[int, StockSucursal]:
        """SELECT ... FOR UPDATE -- justo antes de descontar `cantidad`
        (stock físico) al confirmar un pago ya verificado contra Stripe."""
        if not variante_ids:
            return {}
        stmt = (
            select(StockSucursal)
            .where(
                StockSucursal.sucursal_id == sucursal_id,
                StockSucursal.producto_variante_id.in_(variante_ids),
            )
            .with_for_update(of=StockSucursal)
        )
        return {fila.producto_variante_id: fila for fila in self.db.execute(stmt).scalars()}


class PagoRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, pago: Pago) -> Pago:
        self.db.add(pago)
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def obtener_por_session_id(self, session_id: str) -> Pago | None:
        stmt = select(Pago).where(Pago.stripe_checkout_session_id == session_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def guardar(self) -> None:
        self.db.commit()


class CarritoItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def eliminar_por_ids(self, item_ids: list[int]) -> None:
        """Borra SOLO las filas indicadas -- las no seleccionadas, o
        cualquier unidad agregada después de confirmar la compra (CU22), no
        se tocan (ver Models/venta.py: VentaDetalle.carrito_item_id)."""
        if not item_ids:
            return
        self.db.execute(delete(CarritoItem).where(CarritoItem.id.in_(item_ids)))
