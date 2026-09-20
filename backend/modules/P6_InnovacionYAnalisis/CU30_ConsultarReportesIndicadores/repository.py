"""Acceso a datos de CU30 -- Consultar reportes e indicadores (Administrador).

Solo lectura -- reutiliza Venta/VentaDetalle/Pago (CU22-CU25), StockSucursal
(CU08/CU14/CU17), Reserva (CU17-CU20), DevolucionCambio (CU26) y Sucursal
(CU06) tal cual existen. Ninguna tabla propia, ninguna escritura.

Toda agregación (sumas, conteos, agrupaciones, rankings) se hace aquí, en
SQL -- nunca se traen filas sueltas a Python para sumarlas ahí (salvo el
ranking de productos y la lista de stock bajo, que ya vienen acotados por
LIMIT en la propia consulta).
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import Date, and_, cast, func, select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P4_ReservasYAtencion.Models.reserva import Reserva
from modules.P5_ComprasVentasYPagos.Models.devolucion import DevolucionCambio
from modules.P5_ComprasVentasYPagos.Models.pago import EstadoPago, Pago
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta, Venta, VentaDetalle


def _inicio_del_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min, tzinfo=timezone.utc)


def _inicio_del_dia_siguiente(dia: date) -> datetime:
    return _inicio_del_dia(dia) + timedelta(days=1)


class SucursalLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_activas(self) -> list[Sucursal]:
        stmt = select(Sucursal).where(Sucursal.is_active.is_(True)).order_by(Sucursal.nombre)
        return list(self.db.execute(stmt).scalars().all())

    def get_activa(self, sucursal_id: int) -> Sucursal | None:
        stmt = select(Sucursal).where(Sucursal.id == sucursal_id, Sucursal.is_active.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()

    def buscar_por_nombre(self, nombre: str) -> Sucursal | None:
        """Resuelve el nombre libre que devuelve Gemini (CU30, segunda
        parte -- consulta inteligente) contra las sucursales REALES activas
        -- coincidencia exacta primero, luego por contención en cualquier
        sentido (mismo criterio ya usado en CU29 para categoría/color/
        talla/colección). Nunca inventa un id que no exista."""
        objetivo = nombre.strip().lower()
        if not objetivo:
            return None
        activas = self.listar_activas()
        for sucursal in activas:
            if sucursal.nombre.strip().lower() == objetivo:
                return sucursal
        for sucursal in activas:
            comparado = sucursal.nombre.strip().lower()
            if objetivo in comparado or comparado in objetivo:
                return sucursal
        return None


class VentasReporteRepository:
    """Solo ventas Venta.estado == PAGADA -- nunca PENDIENTE_PAGO (no existe
    un estado "fallida"/"cancelada" separado en este modelo: un pago
    fallido/cancelado simplemente deja la Venta en PENDIENTE_PAGO, ver
    Models/venta.py -- filtrar por PAGADA ya excluye todo lo demás)."""

    def __init__(self, db: Session):
        self.db = db

    def _filtros(self, stmt, desde: date | None, hasta: date | None, sucursal_id: int | None):
        stmt = stmt.where(Venta.estado == EstadoVenta.PAGADA)
        if desde is not None:
            stmt = stmt.where(Venta.fecha_creacion >= _inicio_del_dia(desde))
        if hasta is not None:
            stmt = stmt.where(Venta.fecha_creacion < _inicio_del_dia_siguiente(hasta))
        if sucursal_id is not None:
            stmt = stmt.where(Venta.sucursal_id == sucursal_id)
        return stmt

    def totales(self, desde: date | None, hasta: date | None, sucursal_id: int | None) -> tuple[Decimal, int]:
        stmt = self._filtros(
            select(func.coalesce(func.sum(Venta.total), 0), func.count(Venta.id)), desde, hasta, sucursal_id
        )
        ingresos, conteo = self.db.execute(stmt).one()
        return Decimal(ingresos), int(conteo)

    def productos_vendidos(self, desde: date | None, hasta: date | None, sucursal_id: int | None) -> int:
        stmt = (
            select(func.coalesce(func.sum(VentaDetalle.cantidad), 0))
            .select_from(VentaDetalle)
            .join(Venta, Venta.id == VentaDetalle.venta_id)
        )
        stmt = self._filtros(stmt, desde, hasta, sucursal_id)
        return int(self.db.execute(stmt).scalar_one())

    def por_periodo(
        self, desde: date | None, hasta: date | None, sucursal_id: int | None, granularidad: str
    ) -> list[tuple[str, Decimal, int]]:
        columna = (
            func.to_char(Venta.fecha_creacion, "YYYY-MM")
            if granularidad == "mes"
            else cast(Venta.fecha_creacion, Date)
        )
        columna = columna.label("periodo")
        stmt = self._filtros(
            select(columna, func.sum(Venta.total), func.count(Venta.id)), desde, hasta, sucursal_id
        )
        stmt = stmt.group_by(columna).order_by(columna)
        filas = self.db.execute(stmt).all()
        return [(str(periodo), Decimal(ingresos), int(conteo)) for periodo, ingresos, conteo in filas]

    def por_tipo(
        self, desde: date | None, hasta: date | None, sucursal_id: int | None
    ) -> list[tuple[str, int, Decimal]]:
        stmt = self._filtros(
            select(Venta.tipo, func.count(Venta.id), func.sum(Venta.total)), desde, hasta, sucursal_id
        )
        stmt = stmt.group_by(Venta.tipo).order_by(Venta.tipo)
        filas = self.db.execute(stmt).all()
        return [(tipo.value, int(conteo), Decimal(ingresos)) for tipo, conteo, ingresos in filas]

    def por_metodo_pago(
        self, desde: date | None, hasta: date | None, sucursal_id: int | None
    ) -> list[tuple[str, int, Decimal]]:
        """Un único Pago PAGADO por Venta (ver Models/pago.py) -- join
        directo, sin riesgo de duplicar una venta por tener varios intentos
        de pago (los fallidos/cancelados nunca llegan a PAGADO)."""
        stmt = (
            select(Pago.proveedor, func.count(Venta.id), func.sum(Venta.total))
            .select_from(Venta)
            .join(Pago, (Pago.venta_id == Venta.id) & (Pago.estado == EstadoPago.PAGADO))
        )
        stmt = self._filtros(stmt, desde, hasta, sucursal_id)
        stmt = stmt.group_by(Pago.proveedor).order_by(Pago.proveedor)
        filas = self.db.execute(stmt).all()
        return [(proveedor.value, int(conteo), Decimal(ingresos)) for proveedor, conteo, ingresos in filas]

    def por_sucursal(self, desde: date | None, hasta: date | None) -> list[tuple[int, str, int, Decimal]]:
        """Todas las sucursales ACTIVAS, incluso con 0 ventas en el periodo
        (LEFT JOIN con los filtros de fecha/estado en el ON, no en el WHERE
        -- así una sucursal sin ventas sigue apareciendo en la comparación
        en vez de desaparecer de la lista). Solo se llama cuando el filtro
        del reporte es "Todas las sucursales" (ver service.py)."""
        condiciones = [Venta.sucursal_id == Sucursal.id, Venta.estado == EstadoVenta.PAGADA]
        if desde is not None:
            condiciones.append(Venta.fecha_creacion >= _inicio_del_dia(desde))
        if hasta is not None:
            condiciones.append(Venta.fecha_creacion < _inicio_del_dia_siguiente(hasta))
        stmt = (
            select(Sucursal.id, Sucursal.nombre, func.count(Venta.id), func.coalesce(func.sum(Venta.total), 0))
            .select_from(Sucursal)
            .join(Venta, and_(*condiciones), isouter=True)
            .where(Sucursal.is_active.is_(True))
            .group_by(Sucursal.id, Sucursal.nombre)
            .order_by(func.coalesce(func.sum(Venta.total), 0).desc())
        )
        filas = self.db.execute(stmt).all()
        return [(sid, nombre, int(conteo), Decimal(ingresos)) for sid, nombre, conteo, ingresos in filas]

    def top_productos(
        self, desde: date | None, hasta: date | None, sucursal_id: int | None, limite: int
    ) -> list[tuple[int, str, int, Decimal]]:
        """Unidades/ingresos históricos de VentaDetalle (precio congelado al
        momento de la venta, ver Models/venta.py) -- NUNCA el precio_venta
        actual del catálogo."""
        stmt = (
            select(
                Producto.id,
                Producto.nombre,
                func.sum(VentaDetalle.cantidad),
                func.sum(VentaDetalle.subtotal),
            )
            .select_from(VentaDetalle)
            .join(Venta, Venta.id == VentaDetalle.venta_id)
            .join(ProductoVariante, ProductoVariante.id == VentaDetalle.producto_variante_id)
            .join(Producto, Producto.id == ProductoVariante.producto_id)
        )
        stmt = self._filtros(stmt, desde, hasta, sucursal_id)
        stmt = (
            stmt.group_by(Producto.id, Producto.nombre)
            .order_by(func.sum(VentaDetalle.cantidad).desc())
            .limit(limite)
        )
        filas = self.db.execute(stmt).all()
        return [(pid, nombre, int(unidades), Decimal(ingresos)) for pid, nombre, unidades, ingresos in filas]


class InventarioReporteRepository:
    """StockSucursal -- misma fuente y misma fórmula que CU12/CU14
    ("disponible" SIEMPRE cantidad - stock_reservado, nunca el físico
    crudo, clampeado a 0 con GREATEST para nunca mostrar un negativo)."""

    def __init__(self, db: Session):
        self.db = db

    def totales(self, sucursal_id: int | None) -> tuple[int, int]:
        stmt = select(
            func.coalesce(func.sum(StockSucursal.cantidad), 0),
            func.coalesce(func.sum(StockSucursal.stock_reservado), 0),
        )
        if sucursal_id is not None:
            stmt = stmt.where(StockSucursal.sucursal_id == sucursal_id)
        fisico, reservado = self.db.execute(stmt).one()
        return int(fisico), int(reservado)

    def _disponible(self):
        return func.greatest(StockSucursal.cantidad - StockSucursal.stock_reservado, 0)

    def contar_stock_bajo(self, sucursal_id: int | None, umbral: int) -> int:
        stmt = self._stmt_base_stock_bajo(sucursal_id, umbral, select(func.count()).select_from(StockSucursal))
        return int(self.db.execute(stmt).scalar_one())

    def stock_bajo(self, sucursal_id: int | None, umbral: int, limite: int) -> list[tuple]:
        disponible = self._disponible().label("disponible")
        columnas = select(
            ProductoVariante.id,
            Producto.nombre,
            Color.nombre,
            Talla.nombre,
            Sucursal.nombre,
            disponible,
        )
        stmt = self._stmt_base_stock_bajo(sucursal_id, umbral, columnas)
        stmt = stmt.order_by(disponible.asc()).limit(limite)
        return self.db.execute(stmt).all()

    def _stmt_base_stock_bajo(self, sucursal_id: int | None, umbral: int, stmt):
        disponible = self._disponible()
        stmt = (
            stmt.select_from(StockSucursal)
            .join(ProductoVariante, ProductoVariante.id == StockSucursal.producto_variante_id)
            .join(Producto, Producto.id == ProductoVariante.producto_id)
            .join(Color, Color.id == ProductoVariante.color_id)
            .join(Talla, Talla.id == ProductoVariante.talla_id)
            .join(Sucursal, Sucursal.id == StockSucursal.sucursal_id)
            .where(
                disponible <= umbral,
                Producto.is_active.is_(True),
                ProductoVariante.is_active.is_(True),
                Sucursal.is_active.is_(True),
            )
        )
        if sucursal_id is not None:
            stmt = stmt.where(StockSucursal.sucursal_id == sucursal_id)
        return stmt


class ReservasReporteRepository:
    """Reserva.estado_general (resumen ya calculado por CU17-CU20, ver
    Models/reserva.py) -- CU30 nunca inventa un estado nuevo, solo cuenta
    los reales."""

    def __init__(self, db: Session):
        self.db = db

    def conteos_por_estado(
        self, desde: date | None, hasta: date | None, sucursal_id: int | None
    ) -> dict[str, int]:
        stmt = select(Reserva.estado_general, func.count(Reserva.id))
        if desde is not None:
            stmt = stmt.where(Reserva.fecha_reserva >= desde)
        if hasta is not None:
            stmt = stmt.where(Reserva.fecha_reserva <= hasta)
        if sucursal_id is not None:
            stmt = stmt.where(Reserva.sucursal_id == sucursal_id)
        stmt = stmt.group_by(Reserva.estado_general)
        filas = self.db.execute(stmt).all()
        return {estado.value: int(conteo) for estado, conteo in filas}


class DevolucionesReporteRepository:
    """DevolucionCambio (CU26) -- solo lectura, nunca se escribe desde CU30."""

    def __init__(self, db: Session):
        self.db = db

    def conteos_por_tipo(
        self, desde: date | None, hasta: date | None, sucursal_id: int | None
    ) -> dict[str, int]:
        stmt = select(DevolucionCambio.tipo, func.count(DevolucionCambio.id))
        if desde is not None:
            stmt = stmt.where(DevolucionCambio.fecha_creacion >= _inicio_del_dia(desde))
        if hasta is not None:
            stmt = stmt.where(DevolucionCambio.fecha_creacion < _inicio_del_dia_siguiente(hasta))
        if sucursal_id is not None:
            stmt = stmt.where(DevolucionCambio.sucursal_id == sucursal_id)
        stmt = stmt.group_by(DevolucionCambio.tipo)
        filas = self.db.execute(stmt).all()
        return {tipo.value: int(conteo) for tipo, conteo in filas}
