"""Endpoints de CU17 -- Crear reserva de prendas (Cliente).

Requiere un CLIENTE autenticado. Reutiliza get_current_usuario / require_roles
ya existentes (app.core.deps) -- no crea un JWT ni un AuthService nuevo.

A diferencia de CU14/CU15/CU16 (donde la sucursal SIEMPRE sale de
usuario.sucursal_id, nunca del cliente HTTP), aquí el Cliente no tiene una
sucursal propia: sucursal_id es un dato que el propio Cliente elige y envía
en el body, y el backend lo valida (existe y está activa) en vez de
derivarlo del actor. cliente_id, en cambio, sigue el mismo patrón que los
demás CU: se resuelve SIEMPRE del usuario autenticado, nunca de un id
recibido del cliente -- así un Cliente no puede crear ni consultar reservas
a nombre de otro usuario manipulando la URL, el body o cualquier parámetro.

La API es JSON puro -- preparada para que Flutter la use más adelante,
aunque este flujo es solo para Angular Web por ahora.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import AgregarDetalleRequest, CrearReservaRequest, ReservaOut
from .service import (
    CrearReservaService,
    FechaFueraDeRangoError,
    HorarioInvalidoError,
    ReservaNoCompatibleError,
    ReservaNoEncontradaError,
    StockInsuficienteError,
    SucursalNoEncontradaError,
    VarianteNoEncontradaError,
)

require_cliente = require_roles(RolUsuario.CLIENTE)

router = APIRouter(prefix="/reservas", tags=["CU17 - Crear reserva de prendas"])


@router.post("", response_model=ReservaOut, status_code=status.HTTP_201_CREATED)
def crear_reserva(
    payload: CrearReservaRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> ReservaOut:
    try:
        return CrearReservaService(db).crear(actor, payload)
    except FechaFueraDeRangoError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "La fecha debe ser entre hoy y los próximos 7 días.",
        ) from exc
    except HorarioInvalidoError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "El horario elegido está fuera de atención o no respeta la anticipación mínima de 1 hora.",
        ) from exc
    except SucursalNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La sucursal indicada no existe o no está activa."
        ) from exc
    except VarianteNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "La variante indicada no existe o no está disponible.",
        ) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "No hay stock suficiente en esa sucursal para reservar esa cantidad.",
        ) from exc


@router.get("/mias", response_model=list[ReservaOut], tags=["CU18 - Consultar reserva"])
def listar_mis_reservas(
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> list[ReservaOut]:
    """Endpoint de CU18 -- Consultar reserva (Cliente).

    Se quedó registrado aquí, junto al POST de CU17, porque ya existía
    cuando se implementó CU18 y expone exactamente lo que CU18 necesita: no
    tiene sentido duplicarlo en un router nuevo. cliente_id sale SIEMPRE de
    `actor` (el usuario autenticado), nunca de la URL o de un parámetro --
    así un Cliente jamás puede leer reservas de otro. ReservaOut ya trae la
    cabecera (código, sucursal+ciudad, fecha, hora_inicio/hora_fin, estado
    agregado) con TODAS sus prendas anidadas en `detalles` (producto+imagen,
    variante talla/color, cantidad, estado individual) -- una tarjeta por
    reserva, no una por prenda -- ver CU18_ConsultarReserva/__init__.py.
    """
    return CrearReservaService(db).listar_mias(actor.id)


@router.get("/compatibles", response_model=list[ReservaOut])
def listar_reservas_compatibles(
    sucursal_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> list[ReservaOut]:
    """Antes de mostrar el modal de fecha/hora, producto-detalle consulta
    esto para ofrecer "agregar a esta reserva" en vez de programar una visita
    nueva: reservas PROPIAS en `sucursal_id` con estado_general PENDIENTE
    (ninguna prenda de la reserva empezó a atenderse todavía, ver
    Models/reserva.py:calcular_estado_general) -- una reserva PREPARADA,
    EN_ATENCION, LISTA_PARA_CAJA, ATENDIDA, CANCELADA o VENCIDA nunca
    aparece aquí. Puede devolver una lista vacía (no hay ninguna reserva
    compatible: el Cliente sigue directo al modal de fecha/hora)."""
    return CrearReservaService(db).listar_compatibles(actor.id, sucursal_id)


@router.post("/{reserva_id}/detalles", response_model=ReservaOut, status_code=status.HTTP_201_CREATED)
def agregar_detalle(
    reserva_id: int,
    payload: AgregarDetalleRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> ReservaOut:
    """"Agregar a esta reserva" del modal de compatibles -- crea SOLO un
    ReservaDetalle nuevo (o incrementa uno existente para la misma variante,
    ver CrearReservaService.agregar_detalle), nunca una cabecera Reserva
    nueva. cliente_id se resuelve SIEMPRE de `actor`, nunca del body: un
    Cliente no puede agregar una prenda a una reserva ajena manipulando
    `reserva_id`."""
    try:
        return CrearReservaService(db).agregar_detalle(actor, reserva_id, payload)
    except ReservaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada.") from exc
    except ReservaNoCompatibleError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Esa reserva ya no admite más prendas -- solo se puede agregar mientras sigue pendiente.",
        ) from exc
    except VarianteNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "La variante indicada no existe o no está disponible.",
        ) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "No hay stock suficiente en esa sucursal para agregar esa prenda.",
        ) from exc
