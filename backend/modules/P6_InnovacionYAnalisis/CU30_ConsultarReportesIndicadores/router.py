"""Endpoints de CU30 -- Consultar reportes e indicadores (Administrador).

SOLO ADMINISTRADOR -- nunca expuesto a Cliente/Cajero/Proveedor/Encargado
(el Encargado tendrá su propio resumen operativo más adelante, fuera de este
alcance, ver __init__.py). Puramente consultivo: ningún endpoint de este
router modifica nada (ver service.py).

fecha_desde/fecha_hasta/sucursal_id son query params opcionales en todos los
endpoints salvo /inventario (que ignora las fechas por diseño -- stock es
una foto del estado actual, sin dimensión temporal en el modelo, ver
service.py). Fechas SIEMPRE inclusivas en ambos extremos, se pueden combinar
libremente (solo una, ambas, o ninguna) -- mismo criterio que CU27.

/consulta-inteligente (CU30, segunda parte) -- mismo actor (SOLO
ADMINISTRADOR), mismo criterio de "puramente consultivo": interpreta texto/
voz con Gemini y reutiliza EXACTAMENTE los Services de arriba (ver
consulta_inteligente_service.py), nunca ejecuta una consulta nueva ni dejar
que Gemini toque PostgreSQL. El try/except de ese endpoint es la última red
de seguridad -- cualquier fallo interno (Gemini caído, excepción
inesperada) SIEMPRE responde 200 con un mensaje amigable, nunca un 500 con
detalle técnico, para que el dashboard base (filtros manuales) nunca se
vea afectado.
"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .consulta_inteligente_service import ConsultaInteligenteService
from .schemas import (
    ConsultaInteligenteRequest,
    ConsultaInteligenteResponse,
    InventarioReporteOut,
    ProductosMasVendidosReporteOut,
    ReservasReporteOut,
    ResumenReporteOut,
    VentasReporteOut,
)
from .service import RangoFechaInvalidoError, ReportesService, SucursalInvalidaError

logger = logging.getLogger(__name__)

require_administrador = require_roles(RolUsuario.ADMINISTRADOR)

_RESPUESTA_FALLBACK_INESPERADA = ConsultaInteligenteResponse(
    exito=False,
    intencion=None,
    filtros=None,
    resumen="La consulta inteligente no está disponible en este momento. Puedes utilizar los filtros manuales.",
    datos=None,
)

router = APIRouter(prefix="/reportes", tags=["CU30 - Consultar reportes e indicadores"])

_MSG_RANGO_INVALIDO = 'La fecha "Desde" no puede ser posterior a "Hasta".'
_MSG_SUCURSAL_INVALIDA = "La sucursal indicada no existe o no está activa."


@router.get("/resumen", response_model=ResumenReporteOut)
def obtener_resumen(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    sucursal_id: int | None = Query(None),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_administrador),
) -> ResumenReporteOut:
    try:
        return ReportesService(db).resumen(fecha_desde, fecha_hasta, sucursal_id)
    except RangoFechaInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_RANGO_INVALIDO) from exc
    except SucursalInvalidaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SUCURSAL_INVALIDA) from exc


@router.get("/ventas", response_model=VentasReporteOut)
def obtener_ventas(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    sucursal_id: int | None = Query(None),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_administrador),
) -> VentasReporteOut:
    try:
        return ReportesService(db).ventas(fecha_desde, fecha_hasta, sucursal_id)
    except RangoFechaInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_RANGO_INVALIDO) from exc
    except SucursalInvalidaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SUCURSAL_INVALIDA) from exc


@router.get("/inventario", response_model=InventarioReporteOut)
def obtener_inventario(
    sucursal_id: int | None = Query(None),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_administrador),
) -> InventarioReporteOut:
    try:
        return ReportesService(db).inventario(sucursal_id)
    except SucursalInvalidaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SUCURSAL_INVALIDA) from exc


@router.get("/reservas", response_model=ReservasReporteOut)
def obtener_reservas(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    sucursal_id: int | None = Query(None),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_administrador),
) -> ReservasReporteOut:
    try:
        return ReportesService(db).reservas(fecha_desde, fecha_hasta, sucursal_id)
    except RangoFechaInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_RANGO_INVALIDO) from exc
    except SucursalInvalidaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SUCURSAL_INVALIDA) from exc


@router.get("/productos-mas-vendidos", response_model=ProductosMasVendidosReporteOut)
def obtener_productos_mas_vendidos(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    sucursal_id: int | None = Query(None),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_administrador),
) -> ProductosMasVendidosReporteOut:
    try:
        return ReportesService(db).productos_mas_vendidos(fecha_desde, fecha_hasta, sucursal_id)
    except RangoFechaInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_RANGO_INVALIDO) from exc
    except SucursalInvalidaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SUCURSAL_INVALIDA) from exc


@router.post("/consulta-inteligente", response_model=ConsultaInteligenteResponse)
def consulta_inteligente(
    payload: ConsultaInteligenteRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_administrador),
) -> ConsultaInteligenteResponse:
    try:
        return ConsultaInteligenteService(db).consultar(payload)
    except Exception:
        # Última red de seguridad (ver docstring del módulo) -- ni una
        # excepción inesperada aquí debe tumbar el dashboard base.
        logger.exception("CU30 -- fallo inesperado en la consulta inteligente.")
        return _RESPUESTA_FALLBACK_INESPERADA
