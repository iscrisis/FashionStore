"""Contratos REST de CU30 -- Consultar reportes e indicadores (Administrador).

Todos los montos como float (nunca Decimal ni string) -- mismo criterio que
el resto del proyecto (ver CU11/CU32): se calculan internamente con Decimal
(ver repository.py/service.py) y solo se convierten a float al armar estos
schemas, para que Angular y un futuro Flutter los consuman como números
estables.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ResumenReporteOut(BaseModel):
    ingresos: float
    ventas_realizadas: int
    productos_vendidos: int
    reservas_atendidas: int
    # Total combinado (devoluciones + cambios) -- para la tarjeta KPI única
    # "Devoluciones/cambios". `devoluciones`/`cambios` abajo son el
    # desglose que pide la sección propia (ver __init__.py del paquete).
    devoluciones_cambios: int
    devoluciones: int
    cambios: int
    # Ignora fecha_desde/fecha_hasta por diseño -- es una foto del stock
    # ACTUAL, no tiene dimensión temporal en el modelo (ver service.py).
    stock_bajo: int


class VentaPeriodoOut(BaseModel):
    # "2026-09-19" (granularidad "dia") o "2026-09" (granularidad "mes") --
    # ver VentasReporteOut.granularidad.
    periodo: str
    ingresos: float
    ventas: int


class VentaPorTipoOut(BaseModel):
    tipo: str
    ventas: int
    ingresos: float


class VentaPorMetodoPagoOut(BaseModel):
    metodo: str
    ventas: int
    ingresos: float


class VentaPorSucursalOut(BaseModel):
    sucursal_id: int
    sucursal: str
    ventas: int
    ingresos: float


class VentasReporteOut(BaseModel):
    ingresos_totales: float
    ventas_totales: int
    granularidad: Literal["dia", "mes"]
    por_periodo: list[VentaPeriodoOut]
    por_tipo: list[VentaPorTipoOut]
    por_metodo_pago: list[VentaPorMetodoPagoOut]
    # SIEMPRE [] cuando se filtró una sucursal específica -- comparar una
    # sucursal contra sí misma no aporta nada (ver service.py).
    por_sucursal: list[VentaPorSucursalOut]


class StockBajoItemOut(BaseModel):
    producto_variante_id: int
    producto: str
    color: str
    talla: str
    sucursal: str
    disponible: int


class InventarioReporteOut(BaseModel):
    stock_fisico_total: int
    stock_reservado_total: int
    stock_disponible_total: int
    umbral_stock_bajo: int
    stock_bajo: list[StockBajoItemOut]


class ReservasReporteOut(BaseModel):
    creadas: int
    atendidas: int
    canceladas: int
    vencidas: int


class ProductoMasVendidoOut(BaseModel):
    producto_id: int
    nombre: str
    unidades: int
    ingresos: float


class ProductosMasVendidosReporteOut(BaseModel):
    productos: list[ProductoMasVendidoOut]


# ---------------------------------------------------------------------
# CU30 -- segunda parte: consulta inteligente (texto/voz + Gemini). Ver
# consulta_inteligente_service.py -- estos contratos son puramente de
# entrada/salida, nunca reemplazan a los de arriba (que siguen siendo la
# única fuente de los datos reales).
# ---------------------------------------------------------------------


class ConsultaInteligenteRequest(BaseModel):
    consulta: str = Field(min_length=1, max_length=300)
    # Estado YA aplicado en el dashboard (lo que el Administrador tiene en
    # pantalla) -- se usa como fallback cuando la consulta no menciona
    # sucursal/periodo explícitos ("mantener el periodo actual del
    # dashboard", ver consulta_inteligente_service.py). NUNCA se usa para
    # autorizar nada -- el rol se resuelve siempre del JWT (ver router.py).
    sucursal_id_actual: int | None = None
    fecha_desde_actual: date | None = None
    fecha_hasta_actual: date | None = None


class FiltrosResueltosOut(BaseModel):
    sucursal_id: int | None
    sucursal_nombre: str | None
    fecha_desde: date | None
    fecha_hasta: date | None


class ConsultaInteligenteResponse(BaseModel):
    # False cuando Gemini no está disponible, la intención no se reconoció,
    # o la sucursal mencionada no existe -- en esos casos `filtros`/`datos`
    # son None y `resumen` trae un mensaje amigable (nunca un detalle
    # técnico, ver consulta_inteligente_service.py). Angular SOLO debe
    # refrescar el dashboard cuando `exito` es true.
    exito: bool
    intencion: str | None
    filtros: FiltrosResueltosOut | None
    resumen: str
    datos: (
        ResumenReporteOut
        | VentasReporteOut
        | InventarioReporteOut
        | ReservasReporteOut
        | ProductosMasVendidosReporteOut
        | None
    )
