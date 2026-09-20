"""Consulta inteligente de CU30 (segunda parte) -- texto/voz del
Administrador -> Gemini interpreta intención y criterios -> FastAPI los
valida/resuelve -> reutiliza ReportesService (primera parte, NUNCA una
consulta nueva) -> Gemini redacta un resumen SOLO a partir de esos datos
reales.

Flujo, siempre en este orden (nunca al revés -- ver gemini_client.py):
  1. INTERPRETAR -- gemini_client.interpretar_consulta_reporte devuelve
     intención + sucursal/periodo en texto libre. Si Gemini no está
     disponible, se responde con el mensaje de fallback -- el dashboard
     base (filtros manuales) sigue funcionando igual.
  2. VALIDAR/RESOLVER -- FastAPI, NUNCA Gemini:
       - la intención debe estar en gemini_client.INTENCIONES_VALIDAS;
       - el nombre de sucursal se resuelve contra PostgreSQL
         (SucursalLecturaRepository.buscar_por_nombre) -- si no la
         menciona, se mantiene la ya aplicada en el dashboard
         (`sucursal_id_actual` del request);
       - las fechas se calculan SIEMPRE en Python a partir de la expresión
         temporal (ver _resolver_periodo) -- un rango exacto que Gemini
         haya escrito solo se usa si además es un ISO-8601 válido; si no
         mencionó ningún periodo, se mantiene el ya aplicado en el
         dashboard (`fecha_desde_actual`/`fecha_hasta_actual`).
  3. CONSULTAR -- llama al método de ReportesService que YA existe para
     esa intención (ver _obtener_datos) -- nunca una query nueva.
  4. REDACTAR -- con los datos reales ya obtenidos, arma un "Reporte" de
     texto y pide a Gemini un resumen (generar_resumen_reporte). Si esta
     llamada falla, se usa una redacción propia por plantilla (_resumen_
     plantilla) -- los datos nunca se pierden por esto.

`datos` en la respuesta SIEMPRE sale del paso 3 -- Gemini jamás decide qué
datos se devuelven, solo interpretación de la consulta y redacción final.
"""

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from .gemini_client import (
    INTENCIONES_VALIDAS,
    GeminiNoDisponibleError,
    generar_resumen_reporte,
    interpretar_consulta_reporte,
)
from .repository import SucursalLecturaRepository
from .schemas import (
    ConsultaInteligenteRequest,
    ConsultaInteligenteResponse,
    FiltrosResueltosOut,
    InventarioReporteOut,
    ProductosMasVendidosReporteOut,
    ReservasReporteOut,
    ResumenReporteOut,
    VentasReporteOut,
)
from .service import RangoFechaInvalidoError, ReportesService, SucursalInvalidaError

logger = logging.getLogger(__name__)


class SucursalMencionadaNoEncontradaError(Exception):
    """El nombre de sucursal que interpretó Gemini no coincide con ninguna
    sucursal activa real -- distinto de "no mencionó ninguna" (ese caso
    simplemente mantiene la sucursal ya aplicada en el dashboard, ver
    _resolver_sucursal)."""


_MSG_IA_NO_DISPONIBLE = (
    "La consulta inteligente no está disponible en este momento. Puedes utilizar los filtros manuales."
)
_MSG_INTENCION_NO_RECONOCIDA = (
    "No pude identificar ese reporte. Puedes consultar ventas, inventario, reservas, "
    "productos más vendidos o devoluciones."
)
_MSG_SUCURSAL_NO_ENCONTRADA = "No encontré una sucursal con ese nombre."
_MSG_SIN_DATOS = "No hay información para el periodo seleccionado."

_MESES_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def _parsear_fecha_iso(valor) -> date | None:
    if not isinstance(valor, str) or not valor.strip():
        return None
    try:
        return date.fromisoformat(valor.strip())
    except ValueError:
        return None


def _resolver_periodo(
    periodo: object, mes_nombre: object, fecha_desde_ia: object, fecha_hasta_ia: object
) -> tuple[date | None, date | None]:
    """SIEMPRE calculado por Python -- nunca confía en una fecha que Gemini
    haya escrito, salvo un rango explícito de días que además sea un
    ISO-8601 válido (ver docstring del módulo)."""
    hoy = date.today()

    if periodo == "hoy":
        return hoy, hoy
    if periodo == "ayer":
        ayer = hoy - timedelta(days=1)
        return ayer, ayer
    if periodo == "esta_semana":
        return hoy - timedelta(days=hoy.weekday()), hoy
    if periodo == "este_mes":
        return hoy.replace(day=1), hoy
    if periodo == "mes_pasado":
        primer_dia_mes_actual = hoy.replace(day=1)
        ultimo_dia_mes_pasado = primer_dia_mes_actual - timedelta(days=1)
        return ultimo_dia_mes_pasado.replace(day=1), ultimo_dia_mes_pasado
    if periodo == "este_anio":
        return hoy.replace(month=1, day=1), hoy

    if isinstance(mes_nombre, str) and mes_nombre.strip():
        numero_mes = _MESES_ES.get(mes_nombre.strip().lower())
        if numero_mes is not None:
            primer_dia = date(hoy.year, numero_mes, 1)
            # Truco estándar: día 28 + 4 días siempre cae en el mes
            # siguiente; volver al día 1 de ESE mes y restar un día da el
            # último día real del mes buscado (28/29/30/31).
            ultimo_dia = (date(hoy.year, numero_mes, 28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            return primer_dia, ultimo_dia

    desde_valida = _parsear_fecha_iso(fecha_desde_ia)
    hasta_valida = _parsear_fecha_iso(fecha_hasta_ia)
    if desde_valida is not None or hasta_valida is not None:
        if desde_valida is not None and hasta_valida is not None and desde_valida > hasta_valida:
            return hasta_valida, desde_valida
        return desde_valida, hasta_valida

    return None, None


def _encabezado_contexto(desde: date | None, hasta: date | None, sucursal_nombre: str | None) -> str:
    if desde and hasta:
        periodo = f"{desde.isoformat()} a {hasta.isoformat()}"
    elif desde:
        periodo = f"desde {desde.isoformat()}"
    elif hasta:
        periodo = f"hasta {hasta.isoformat()}"
    else:
        periodo = "todo el histórico"
    sucursal = sucursal_nombre or "todas las sucursales"
    return f"Periodo: {periodo}\nSucursal: {sucursal}\n"


class ConsultaInteligenteService:
    def __init__(self, db: Session):
        self._reportes = ReportesService(db)
        self._sucursales = SucursalLecturaRepository(db)

    def consultar(self, payload: ConsultaInteligenteRequest) -> ConsultaInteligenteResponse:
        try:
            interpretado = interpretar_consulta_reporte(payload.consulta)
        except GeminiNoDisponibleError:
            return self._respuesta_fallback(_MSG_IA_NO_DISPONIBLE)

        intencion = interpretado.get("intencion")
        if intencion not in INTENCIONES_VALIDAS:
            return self._respuesta_fallback(_MSG_INTENCION_NO_RECONOCIDA)

        try:
            sucursal_id, sucursal_nombre = self._resolver_sucursal(
                interpretado.get("sucursal"), payload.sucursal_id_actual
            )
        except SucursalMencionadaNoEncontradaError:
            return self._respuesta_fallback(_MSG_SUCURSAL_NO_ENCONTRADA)

        desde, hasta = _resolver_periodo(
            interpretado.get("periodo"),
            interpretado.get("mes_nombre"),
            interpretado.get("fecha_desde"),
            interpretado.get("fecha_hasta"),
        )
        if desde is None and hasta is None:
            desde, hasta = payload.fecha_desde_actual, payload.fecha_hasta_actual

        filtros = FiltrosResueltosOut(
            sucursal_id=sucursal_id, sucursal_nombre=sucursal_nombre, fecha_desde=desde, fecha_hasta=hasta
        )

        try:
            datos, contexto, hay_datos = self._obtener_datos(intencion, desde, hasta, sucursal_id, sucursal_nombre)
        except (RangoFechaInvalidoError, SucursalInvalidaError):
            # Defensivo -- no debería ocurrir (sucursal_id ya viene resuelto
            # y activo, y _resolver_periodo nunca invierte un rango), pero
            # ante cualquier caso raro se degrada al mismo fallback amigable
            # en vez de romper el dashboard.
            return self._respuesta_fallback(_MSG_IA_NO_DISPONIBLE)

        if not hay_datos:
            return ConsultaInteligenteResponse(
                exito=True, intencion=intencion, filtros=filtros, resumen=_MSG_SIN_DATOS, datos=datos
            )

        try:
            resumen = generar_resumen_reporte(contexto)
        except GeminiNoDisponibleError:
            resumen = self._resumen_plantilla(datos)

        return ConsultaInteligenteResponse(exito=True, intencion=intencion, filtros=filtros, resumen=resumen, datos=datos)

    def _resolver_sucursal(self, nombre_mencionado: object, sucursal_id_actual: int | None):
        """Devuelve (sucursal_id, sucursal_nombre) -- ambos None cuando no
        aplica ningún filtro de sucursal. Lanza
        SucursalMencionadaNoEncontradaError cuando SÍ mencionó un nombre
        pero no coincide con ninguna sucursal activa real."""
        if isinstance(nombre_mencionado, str) and nombre_mencionado.strip():
            sucursal = self._sucursales.buscar_por_nombre(nombre_mencionado)
            if sucursal is None:
                raise SucursalMencionadaNoEncontradaError
            return sucursal.id, sucursal.nombre

        if sucursal_id_actual is not None:
            sucursal = self._sucursales.get_activa(sucursal_id_actual)
            if sucursal is not None:
                return sucursal.id, sucursal.nombre

        return None, None

    def _obtener_datos(
        self, intencion: str, desde: date | None, hasta: date | None, sucursal_id: int | None, sucursal_nombre: str | None
    ):
        encabezado = _encabezado_contexto(desde, hasta, sucursal_nombre)

        if intencion in ("resumen_general", "devoluciones_cambios"):
            datos = self._reportes.resumen(desde, hasta, sucursal_id)
            contexto = (
                f"{encabezado}"
                f"Ingresos: Bs {datos.ingresos:.2f}\n"
                f"Ventas realizadas: {datos.ventas_realizadas}\n"
                f"Productos vendidos: {datos.productos_vendidos}\n"
                f"Reservas atendidas: {datos.reservas_atendidas}\n"
                f"Devoluciones: {datos.devoluciones}\n"
                f"Cambios: {datos.cambios}\n"
                f"Variantes con stock bajo: {datos.stock_bajo}"
            )
            if intencion == "devoluciones_cambios":
                hay_datos = datos.devoluciones > 0 or datos.cambios > 0
            else:
                hay_datos = (
                    datos.ventas_realizadas > 0
                    or datos.reservas_atendidas > 0
                    or datos.devoluciones > 0
                    or datos.cambios > 0
                )
            return datos, contexto, hay_datos

        if intencion in ("ventas", "ingresos", "ventas_por_sucursal", "ventas_por_metodo_pago", "ventas_por_tipo"):
            datos = self._reportes.ventas(desde, hasta, sucursal_id)
            lineas = [
                encabezado,
                f"Ingresos totales: Bs {datos.ingresos_totales:.2f}",
                f"Ventas totales: {datos.ventas_totales}",
            ]
            if datos.por_tipo:
                lineas.append(
                    "Por tipo: " + ", ".join(f"{p.tipo} {p.ventas} (Bs {p.ingresos:.2f})" for p in datos.por_tipo)
                )
            if datos.por_metodo_pago:
                lineas.append(
                    "Por método de pago: "
                    + ", ".join(f"{p.metodo} {p.ventas} (Bs {p.ingresos:.2f})" for p in datos.por_metodo_pago)
                )
            if datos.por_sucursal:
                lineas.append(
                    "Por sucursal: " + ", ".join(f"{p.sucursal} Bs {p.ingresos:.2f}" for p in datos.por_sucursal)
                )
            return datos, "\n".join(lineas), datos.ventas_totales > 0

        if intencion == "productos_mas_vendidos":
            datos = self._reportes.productos_mas_vendidos(desde, hasta, sucursal_id)
            if datos.productos:
                contexto = encabezado + "Productos más vendidos:\n" + "\n".join(
                    f"- {p.nombre}: {p.unidades} unidades, Bs {p.ingresos:.2f}" for p in datos.productos
                )
            else:
                contexto = encabezado + "Sin productos vendidos en el periodo."
            return datos, contexto, len(datos.productos) > 0

        if intencion in ("inventario", "stock_bajo"):
            datos = self._reportes.inventario(sucursal_id)
            lineas = [
                f"Sucursal: {sucursal_nombre or 'todas las sucursales'}",
                f"Stock físico total: {datos.stock_fisico_total}",
                f"Stock reservado: {datos.stock_reservado_total}",
                f"Stock disponible: {datos.stock_disponible_total}",
                f"Umbral de stock bajo: {datos.umbral_stock_bajo}",
            ]
            if datos.stock_bajo:
                lineas.append(
                    "Variantes con stock bajo: "
                    + ", ".join(
                        f"{i.producto} ({i.color}/{i.talla}) en {i.sucursal}: {i.disponible}"
                        for i in datos.stock_bajo
                    )
                )
            else:
                lineas.append("Sin variantes con stock bajo.")
            contexto = "\n".join(lineas)
            hay_datos = datos.stock_fisico_total > 0 if intencion == "inventario" else len(datos.stock_bajo) > 0
            return datos, contexto, hay_datos

        if intencion == "reservas":
            datos = self._reportes.reservas(desde, hasta, sucursal_id)
            contexto = (
                f"{encabezado}"
                f"Reservas creadas: {datos.creadas}\n"
                f"Atendidas: {datos.atendidas}\n"
                f"Canceladas: {datos.canceladas}\n"
                f"Vencidas: {datos.vencidas}"
            )
            return datos, contexto, datos.creadas > 0

        # No debería llegar acá -- `intencion` ya se validó contra la lista
        # cerrada (gemini_client.INTENCIONES_VALIDAS) antes de este método.
        raise AssertionError(f"CU30 -- intención sin manejar: {intencion!r}")

    @staticmethod
    def _resumen_plantilla(datos) -> str:
        if isinstance(datos, ResumenReporteOut):
            return f"Ingresos: Bs {datos.ingresos:.2f}. Ventas realizadas: {datos.ventas_realizadas}."
        if isinstance(datos, VentasReporteOut):
            return f"Ingresos totales: Bs {datos.ingresos_totales:.2f} en {datos.ventas_totales} ventas."
        if isinstance(datos, ProductosMasVendidosReporteOut):
            principal = datos.productos[0]
            return f"El producto más vendido fue {principal.nombre}, con {principal.unidades} unidades."
        if isinstance(datos, InventarioReporteOut):
            return (
                f"Stock disponible: {datos.stock_disponible_total} unidades. "
                f"{len(datos.stock_bajo)} variante(s) con stock bajo."
            )
        if isinstance(datos, ReservasReporteOut):
            return f"Reservas creadas: {datos.creadas}, atendidas: {datos.atendidas}."
        return "Datos obtenidos correctamente."  # pragma: no cover - defensivo

    @staticmethod
    def _respuesta_fallback(mensaje: str) -> ConsultaInteligenteResponse:
        return ConsultaInteligenteResponse(exito=False, intencion=None, filtros=None, resumen=mensaje, datos=None)
