"""Acceso a datos de CU26 -- Registrar devolución o cambio (Cajero).

Reutiliza Venta/VentaDetalle (CU22/CU24), Pago (CU23/CU25), ProductoVariante
(CU08) y StockSucursal (CU14/15/16) tal cual existen -- ESCRIBE en
StockSucursal (a diferencia de CU24, que solo la leía) porque registrar una
devolución/cambio es, precisamente, el momento en que se materializa el
reingreso/traspaso de stock. La única tabla propia de este módulo es
DevolucionCambio.

Todos los `bloquear_*` usan SELECT ... FOR UPDATE -- mismo criterio ya usado
en CU17/CU22/CU23/CU25: la Venta y el VentaDetalle se bloquean PRIMERO
(cabecera/línea antes que stock), así dos operaciones concurrentes sobre la
MISMA línea (doble clic, doble pestaña) nunca devuelven/cambian más unidades
de las realmente disponibles (ver `DevolucionCambioService`, que recalcula
`cantidad_operada_por_detalle` recién DESPUÉS de bloquear la línea).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P5_ComprasVentasYPagos.Models.devolucion import DevolucionCambio
from modules.P5_ComprasVentasYPagos.Models.pago import EstadoPago, Pago
from modules.P5_ComprasVentasYPagos.Models.venta import Venta, VentaDetalle


class VentaRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_codigo(self, codigo_venta: str) -> Venta | None:
        """Solo lectura -- para el paso "Buscar venta" (buscar_venta), antes
        de decidir ninguna operación. Nunca bloquea."""
        stmt = (
            select(Venta)
            .where(Venta.codigo_venta == codigo_venta)
            .options(selectinload(Venta.detalles).selectinload(VentaDetalle.producto_variante))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def obtener_por_id(self, venta_id: int) -> Venta | None:
        """Solo lectura -- para validaciones previas a abrir un modal (ej.
        opciones_cambio) que no van a mutar nada por sí mismas."""
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


class VentaDetalleRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_por_id(self, venta_detalle_id: int) -> VentaDetalle | None:
        stmt = (
            select(VentaDetalle)
            .where(VentaDetalle.id == venta_detalle_id)
            .with_for_update(of=VentaDetalle)
        )
        return self.db.execute(stmt).scalar_one_or_none()


class DevolucionCambioRepository:
    def __init__(self, db: Session):
        self.db = db

    def cantidad_operada_por_detalle(self, venta_detalle_id: int) -> int:
        """Suma TODAS las unidades ya devueltas o cambiadas de esa línea --
        sin importar el `tipo`, ambas operaciones consumen de la misma
        cantidad comprada (ver Models/devolucion.py). Se llama SIEMPRE
        después de bloquear el VentaDetalle (ver service.py) para que sea
        consistente frente a otra operación concurrente sobre la misma
        línea."""
        stmt = select(func.coalesce(func.sum(DevolucionCambio.cantidad), 0)).where(
            DevolucionCambio.venta_detalle_id == venta_detalle_id
        )
        return int(self.db.execute(stmt).scalar_one())

    def crear(self, registro: DevolucionCambio) -> DevolucionCambio:
        """Único commit: DevolucionCambio + stock (y, si aplica, el estado
        del reembolso) quedan consistentes juntos, o nada de eso se aplica
        -- ver DevolucionCambioService."""
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro


class PagoRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_pagado_por_venta(self, venta_id: int) -> Pago | None:
        """Solo lectura -- el Pago PAGADO de una Venta ya PAGADA nunca vuelve
        a mutar en este flujo, así que no hace falta bloquearlo."""
        stmt = (
            select(Pago)
            .where(Pago.venta_id == venta_id, Pago.estado == EstadoPago.PAGADO)
            .order_by(Pago.id.desc())
        )
        return self.db.execute(stmt).scalars().first()


class ProductoVarianteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_activa_by_id(self, variante_id: int) -> ProductoVariante | None:
        stmt = select(ProductoVariante).where(
            ProductoVariante.id == variante_id, ProductoVariante.is_active.is_(True)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def listar_activas_por_producto(self, producto_id: int, excluir_id: int) -> list[ProductoVariante]:
        stmt = (
            select(ProductoVariante)
            .join(Producto, ProductoVariante.producto_id == Producto.id)
            .where(
                ProductoVariante.producto_id == producto_id,
                ProductoVariante.id != excluir_id,
                ProductoVariante.is_active.is_(True),
                Producto.is_active.is_(True),
            )
        )
        return list(self.db.execute(stmt).scalars().all())


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def disponible_por_variantes(self, sucursal_id: int, variante_ids: list[int]) -> dict[int, int]:
        """SELECT puro, sin FOR UPDATE -- para listar opciones de cambio
        (solo informativo hasta que se confirme, ver service.py)."""
        if not variante_ids:
            return {}
        stmt = select(
            StockSucursal.producto_variante_id, (StockSucursal.cantidad - StockSucursal.stock_reservado)
        ).where(
            StockSucursal.sucursal_id == sucursal_id,
            StockSucursal.producto_variante_id.in_(variante_ids),
        )
        return dict(self.db.execute(stmt).all())

    def bloquear_filas(self, sucursal_id: int, variante_ids: list[int]) -> dict[int, StockSucursal]:
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


class ProductoLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_ids(self, producto_ids: set[int]) -> dict[int, Producto]:
        """Sin filtrar por `is_active` -- a diferencia de CU24 (que arma
        ventas nuevas), CU26 muestra prendas de una compra YA REALIZADA: un
        producto desactivado después de venderse sigue debiendo poder
        devolverse/cambiarse."""
        if not producto_ids:
            return {}
        stmt = select(Producto).where(Producto.id.in_(producto_ids))
        return {p.id: p for p in self.db.execute(stmt).scalars()}


class UsuarioLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)
