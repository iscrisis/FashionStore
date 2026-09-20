"""Endpoints de CU19 -- Cancelar reserva (Cliente).

Requiere un CLIENTE autenticado. Reutiliza require_roles ya existente
(app.core.deps, mismo patrón que CU17/CU18) -- no crea un JWT ni un
AuthService nuevo. cliente_id sale SIEMPRE del usuario autenticado
(`actor.id`), nunca de la URL ni del body: un Cliente no puede cancelar una
reserva de otro manipulando `reserva_id`/`detalle_id`.

Dos endpoints, ambos bajo el mismo prefijo "/reservas" (router propio,
registrado aparte en app/main.py -- FastAPI permite varios APIRouter bajo el
mismo prefijo, igual que ya hace CU06 con router_ciudades/router_sucursales):
  - PATCH /reservas/{reserva_id}/cancelar -- cancela la reserva ENTERA (todos
    los detalles todavía cancelables).
  - PATCH /reservas/detalles/{detalle_id}/cancelar -- cancela UNA prenda
    dentro de una reserva, sin tocar el resto.
Las dos rutas tienen distinta profundidad ("/reservas/{id}/cancelar" vs
"/reservas/detalles/{id}/cancelar") así que FastAPI nunca las confunde.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P4_ReservasYAtencion.CU17_CrearReservaPrendas.schemas import ReservaDetalleOut, ReservaOut

from .service import CancelarReservaService, ReservaNoCancelableError, ReservaNoEncontradaError

require_cliente = require_roles(RolUsuario.CLIENTE)

router = APIRouter(prefix="/reservas", tags=["CU19 - Cancelar reserva"])


@router.patch("/{reserva_id}/cancelar", response_model=ReservaOut)
def cancelar_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> ReservaOut:
    try:
        return CancelarReservaService(db).cancelar_reserva(actor.id, reserva_id)
    except ReservaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada.") from exc
    except ReservaNoCancelableError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "No hay ninguna prenda pendiente o preparada en esta reserva -- solo se puede "
            "cancelar antes de que el cliente llegue a la sucursal.",
        ) from exc


@router.patch("/detalles/{detalle_id}/cancelar", response_model=ReservaDetalleOut)
def cancelar_detalle(
    detalle_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> ReservaDetalleOut:
    try:
        return CancelarReservaService(db).cancelar_detalle(actor.id, detalle_id)
    except ReservaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada.") from exc
    except ReservaNoCancelableError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Solo se puede cancelar una prenda pendiente o ya preparada, antes de que el "
            "cliente llegue a la sucursal.",
        ) from exc
