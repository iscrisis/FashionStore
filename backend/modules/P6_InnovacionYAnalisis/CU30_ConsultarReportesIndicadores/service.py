"""Reglas de negocio de CU30 -- Consultar reportes e indicadores (Administrador).

Puramente consultivo -- ningún método de este servicio escribe en la base de
datos. Toda fecha es INCLUSIVA en ambos extremos (desde <= fecha <= hasta);
cuando ninguna de las dos se especifica, la consulta queda abierta a todo el
histórico -- el default "mes actual" lo aplica Angular al cargar la pantalla
(ver reportes.ts), nunca este servicio, para que un futuro consumidor
(comando de voz/IA, Flutter) pueda seguir pidiendo un rango explícito sin
depender de un default oculto aquí.

Reservas: las 4 métricas (creadas/atendidas/canceladas/vencidas) usan
SIEMPRE `Reserva.fecha_reserva` (la fecha de la visita agendada) -- es el
único campo de fecha con sentido uniforme para las 4 (`estado_general` no
tiene su propio timestamp de transición, así que no hay forma real de saber
"cuándo" pasó a atendida/cancelada/vencida por separado de cuándo se agendó
la visita). "Creadas" = todas las reservas cuya visita cae en el rango, sin
importar su estado final.

Inventario/stock bajo: son una FOTO del estado actual de StockSucursal, sin
dimensión temporal en el modelo -- por diseño ignoran fecha_desde/
fecha_hasta (ver router.py, que ni siquiera los acepta en ese endpoint) y
solo respetan el filtro de sucursal.

Promociones: no existe en el modelo actual ninguna relación que permita
saber, de forma histórica y confiable, qué VentaDetalle se vendió con una
promoción vigente en ese momento -- el precio queda congelado en
VentaDetalle.precio_unitario sin esa marca (ver CU32/precio_efectivo.py).
Por eso esta primera parte de CU30 NO reporta ninguna métrica de
promociones, en vez de inferirla o modificar CU32 solo para fabricarla.

Preparado para voz/IA (fase futura, NO implementada aún): esa fase deberá
llamar a estos MISMOS métodos de ReportesService, nunca duplicar esta
lógica de agregación.
"""

from datetime import date

from sqlalchemy.orm import Session

from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva
from modules.P5_ComprasVentasYPagos.Models.devolucion import TipoOperacionDevolucion

from .repository import (
    DevolucionesReporteRepository,
    InventarioReporteRepository,
    ReservasReporteRepository,
    SucursalLecturaRepository,
    VentasReporteRepository,
)
from .schemas import (
    InventarioReporteOut,
    ProductoMasVendidoOut,
    ProductosMasVendidosReporteOut,
    ReservasReporteOut,
    ResumenReporteOut,
    StockBajoItemOut,
    VentaPeriodoOut,
    VentaPorMetodoPagoOut,
    VentaPorSucursalOut,
    VentaPorTipoOut,
    VentasReporteOut,
)

# Umbral centralizado de "stock bajo" -- no existía uno previo en el
# proyecto (ver instrucciones de CU30). Cambiarlo acá afecta a la vez el KPI
# del resumen y la lista detallada, en un solo lugar -- nunca hardcodeado en
# Angular.
UMBRAL_STOCK_BAJO = 3
_LIMITE_STOCK_BAJO = 20
_LIMITE_TOP_PRODUCTOS = 5
# Con un rango más ancho que esto, agrupar "por día" produciría demasiados
# puntos para que el gráfico de tendencia siga siendo útil -- se pasa a
# agrupar por mes (ver _granularidad).
_DIAS_MAXIMOS_GRANULARIDAD_DIARIA = 62


class RangoFechaInvalidoError(Exception):
    """`desde` es posterior a `hasta` -- rango vacío por definición."""


class SucursalInvalidaError(Exception):
    """`sucursal_id` no existe o no está activa."""


class ReportesService:
    def __init__(self, db: Session):
        self._sucursales = SucursalLecturaRepository(db)
        self._ventas = VentasReporteRepository(db)
        self._inventario = InventarioReporteRepository(db)
        self._reservas = ReservasReporteRepository(db)
        self._devoluciones = DevolucionesReporteRepository(db)

    def _validar(self, desde: date | None, hasta: date | None, sucursal_id: int | None) -> None:
        if desde is not None and hasta is not None and desde > hasta:
            raise RangoFechaInvalidoError
        if sucursal_id is not None and self._sucursales.get_activa(sucursal_id) is None:
            raise SucursalInvalidaError

    def resumen(self, desde: date | None, hasta: date | None, sucursal_id: int | None) -> ResumenReporteOut:
        self._validar(desde, hasta, sucursal_id)

        ingresos, ventas_realizadas = self._ventas.totales(desde, hasta, sucursal_id)
        productos_vendidos = self._ventas.productos_vendidos(desde, hasta, sucursal_id)

        reservas = self._reservas.conteos_por_estado(desde, hasta, sucursal_id)
        atendidas = reservas.get(EstadoReserva.ATENDIDA.value, 0)

        devoluciones_por_tipo = self._devoluciones.conteos_por_tipo(desde, hasta, sucursal_id)
        devoluciones = devoluciones_por_tipo.get(TipoOperacionDevolucion.DEVOLUCION.value, 0)
        cambios = devoluciones_por_tipo.get(TipoOperacionDevolucion.CAMBIO.value, 0)

        stock_bajo = self._inventario.contar_stock_bajo(sucursal_id, UMBRAL_STOCK_BAJO)

        return ResumenReporteOut(
            ingresos=float(ingresos),
            ventas_realizadas=ventas_realizadas,
            productos_vendidos=productos_vendidos,
            reservas_atendidas=atendidas,
            devoluciones_cambios=devoluciones + cambios,
            devoluciones=devoluciones,
            cambios=cambios,
            stock_bajo=stock_bajo,
        )

    def ventas(self, desde: date | None, hasta: date | None, sucursal_id: int | None) -> VentasReporteOut:
        self._validar(desde, hasta, sucursal_id)

        ingresos_totales, ventas_totales = self._ventas.totales(desde, hasta, sucursal_id)
        granularidad = self._granularidad(desde, hasta)

        por_periodo = [
            VentaPeriodoOut(periodo=periodo, ingresos=float(ingresos), ventas=ventas)
            for periodo, ingresos, ventas in self._ventas.por_periodo(desde, hasta, sucursal_id, granularidad)
        ]
        por_tipo = [
            VentaPorTipoOut(tipo=tipo, ventas=ventas, ingresos=float(ingresos))
            for tipo, ventas, ingresos in self._ventas.por_tipo(desde, hasta, sucursal_id)
        ]
        por_metodo_pago = [
            VentaPorMetodoPagoOut(metodo=metodo, ventas=ventas, ingresos=float(ingresos))
            for metodo, ventas, ingresos in self._ventas.por_metodo_pago(desde, hasta, sucursal_id)
        ]
        # Comparar sucursales contra sí misma no aporta nada -- solo se arma
        # cuando el filtro es "Todas" (ver docstring del módulo).
        por_sucursal = (
            [
                VentaPorSucursalOut(sucursal_id=sid, sucursal=nombre, ventas=ventas, ingresos=float(ingresos))
                for sid, nombre, ventas, ingresos in self._ventas.por_sucursal(desde, hasta)
            ]
            if sucursal_id is None
            else []
        )

        return VentasReporteOut(
            ingresos_totales=float(ingresos_totales),
            ventas_totales=ventas_totales,
            granularidad=granularidad,
            por_periodo=por_periodo,
            por_tipo=por_tipo,
            por_metodo_pago=por_metodo_pago,
            por_sucursal=por_sucursal,
        )

    @staticmethod
    def _granularidad(desde: date | None, hasta: date | None) -> str:
        if desde is not None and hasta is not None:
            if (hasta - desde).days > _DIAS_MAXIMOS_GRANULARIDAD_DIARIA:
                return "mes"
        return "dia"

    def inventario(self, sucursal_id: int | None) -> InventarioReporteOut:
        if sucursal_id is not None and self._sucursales.get_activa(sucursal_id) is None:
            raise SucursalInvalidaError

        fisico, reservado = self._inventario.totales(sucursal_id)
        disponible = max(0, fisico - reservado)

        filas = self._inventario.stock_bajo(sucursal_id, UMBRAL_STOCK_BAJO, _LIMITE_STOCK_BAJO)
        stock_bajo = [
            StockBajoItemOut(
                producto_variante_id=variante_id,
                producto=producto,
                color=color,
                talla=talla,
                sucursal=sucursal,
                disponible=int(disponible_item),
            )
            for variante_id, producto, color, talla, sucursal, disponible_item in filas
        ]

        return InventarioReporteOut(
            stock_fisico_total=fisico,
            stock_reservado_total=reservado,
            stock_disponible_total=disponible,
            umbral_stock_bajo=UMBRAL_STOCK_BAJO,
            stock_bajo=stock_bajo,
        )

    def reservas(self, desde: date | None, hasta: date | None, sucursal_id: int | None) -> ReservasReporteOut:
        self._validar(desde, hasta, sucursal_id)

        conteos = self._reservas.conteos_por_estado(desde, hasta, sucursal_id)
        return ReservasReporteOut(
            creadas=sum(conteos.values()),
            atendidas=conteos.get(EstadoReserva.ATENDIDA.value, 0),
            canceladas=conteos.get(EstadoReserva.CANCELADA.value, 0),
            vencidas=conteos.get(EstadoReserva.VENCIDA.value, 0),
        )

    def productos_mas_vendidos(
        self, desde: date | None, hasta: date | None, sucursal_id: int | None
    ) -> ProductosMasVendidosReporteOut:
        self._validar(desde, hasta, sucursal_id)

        filas = self._ventas.top_productos(desde, hasta, sucursal_id, _LIMITE_TOP_PRODUCTOS)
        return ProductosMasVendidosReporteOut(
            productos=[
                ProductoMasVendidoOut(producto_id=pid, nombre=nombre, unidades=unidades, ingresos=float(ingresos))
                for pid, nombre, unidades, ingresos in filas
            ]
        )
