"""Endpoints de CU27 -- Consultar historial de compras (Cliente/Cajero).

Dos rutas separadas, cada una con su propio rol -- nunca una sola ruta que
decida internamente según el rol del actor (mismo criterio que CU18/CU20
usan `/reservas/mias` vs `/reservas/pendientes-cajero`): la semántica de
"mis compras" (Cliente) y "las de mi sucursal" (Cajero) son suficientemente
distintas como para no mezclarlas en un único endpoint.

Filtros de fecha (`desde`/`hasta`) y `codigo_venta` son query params
opcionales -- se pueden combinar libremente (solo uno, ambos, o ninguno).
Nunca reciben `cliente_id`/`sucursal_id`: ambos se resuelven SIEMPRE del
actor autenticado (ver app.core.deps).
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import VentaHistorialOut
from .service import HistorialComprasService, RangoFechaInvalidoError, SucursalCajeroNoDefinidaError

require_cliente = require_roles(RolUsuario.CLIENTE)
require_cajero = require_roles(RolUsuario.CAJERO)

router = APIRouter(prefix="/historial-compras", tags=["CU27 - Consultar historial de compras"])

_MSG_SIN_SUCURSAL = "Tu usuario no está vinculado a ninguna sucursal."
_MSG_RANGO_INVALIDO = 'La fecha "Desde" no puede ser posterior a "Hasta".'


@router.get("/mias", response_model=list[VentaHistorialOut])
def listar_mis_compras(
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    codigo_venta: str | None = Query(None, min_length=1),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> list[VentaHistorialOut]:
    try:
        return HistorialComprasService(db).listar_mias(actor, desde, hasta, codigo_venta)
    except RangoFechaInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_RANGO_INVALIDO) from exc


@router.get("/sucursal", response_model=list[VentaHistorialOut])
def listar_historial_sucursal(
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    codigo_venta: str | None = Query(None, min_length=1),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cajero),
) -> list[VentaHistorialOut]:
    try:
        return HistorialComprasService(db).listar_sucursal(actor, desde, hasta, codigo_venta)
    except SucursalCajeroNoDefinidaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _MSG_SIN_SUCURSAL) from exc
    except RangoFechaInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_RANGO_INVALIDO) from exc
