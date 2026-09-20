"""Endpoints de CU24 -- Registrar venta presencial (Cajero).

Requiere un CAJERO autenticado. Reutiliza get_current_usuario/require_roles
ya existentes (app.core.deps). La sucursal autorizada se deriva SIEMPRE de
`actor.sucursal_id` (mismo helper `_sucursal_id_del_actor` que ya define
cada router de CU14/CU15/CU16/CU20 -- se repite aquí en vez de importarlo,
mismo criterio ya documentado en esos módulos: no acoplar routers por una
función de una línea), nunca de un sucursal_id que Angular pueda enviar.

Rutas REST bajo "/ventas-presenciales", prefijo propio -- no reutiliza
"/compra-digital" (CU22, exclusivo de Cliente) ni "/reservas" (CU17-20):
CU24 es un recurso distinto (Cajero, no Cliente), aunque reutilice el mismo
modelo Venta/VentaDetalle.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import CrearVentaDirectaRequest, ProductoBusquedaOut, VentaPresencialOut
from .service import (
    ReservaNoEncontradaError,
    ReservaOtraSucursalError,
    ReservaSinPrendasParaCajaError,
    StockInsuficienteError,
    SucursalCajeroNoDefinidaError,
    VarianteNoEncontradaError,
    VentaPresencialService,
)

require_cajero = require_roles(RolUsuario.CAJERO)

router = APIRouter(prefix="/ventas-presenciales", tags=["CU24 - Registrar venta presencial"])

_MSG_SIN_SUCURSAL = "Tu usuario no está vinculado a ninguna sucursal."


@router.get("/productos", response_model=list[ProductoBusquedaOut])
def buscar_productos(
    nombre: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cajero),
) -> list[ProductoBusquedaOut]:
    try:
        return VentaPresencialService(db).buscar_productos(actor, nombre)
    except SucursalCajeroNoDefinidaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _MSG_SIN_SUCURSAL) from exc


@router.post("/directa", response_model=VentaPresencialOut, status_code=status.HTTP_201_CREATED)
def crear_venta_directa(
    payload: CrearVentaDirectaRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cajero),
) -> VentaPresencialOut:
    try:
        return VentaPresencialService(db).crear_venta_directa(actor, payload)
    except SucursalCajeroNoDefinidaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _MSG_SIN_SUCURSAL) from exc
    except VarianteNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Alguna de las variantes indicadas no existe o no está disponible.",
        ) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "No hay disponibilidad suficiente para alguna de las prendas.",
        ) from exc


@router.post("/desde-reserva/{reserva_id}", response_model=VentaPresencialOut, status_code=status.HTTP_201_CREATED)
def crear_venta_desde_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cajero),
) -> VentaPresencialOut:
    try:
        return VentaPresencialService(db).crear_venta_desde_reserva(actor, reserva_id)
    except SucursalCajeroNoDefinidaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _MSG_SIN_SUCURSAL) from exc
    except ReservaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada.") from exc
    except ReservaOtraSucursalError as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Esa reserva pertenece a otra sucursal."
        ) from exc
    except ReservaSinPrendasParaCajaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Esa reserva no tiene prendas listas para caja.",
        ) from exc
