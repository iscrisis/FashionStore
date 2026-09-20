"""Endpoints de CU20 -- Atender reserva de prendas (Encargado de Sucursal,
más la integración mínima de solo lectura para Cajero).

La mayoría requiere un ENCARGADO_SUCURSAL autenticado; GET /cajero/pendientes
requiere CAJERO. Reutiliza require_roles ya existente (app.core.deps, mismo
patrón que CU14/15/16/17/19) -- no crea un JWT ni un AuthService nuevo. La
sucursal autorizada se deriva SIEMPRE de `actor.sucursal_id` (mismo helper
`_sucursal_id_del_actor` que ya define cada router de CU14/CU15/CU16 -- se
repite aquí en vez de importarlo, mismo criterio ya documentado en esos
módulos: no acoplar routers por una función de una línea), nunca de un
sucursal_id que Angular pueda enviar: así ni un Encargado ni un Cajero pueden
leer o modificar reservas de otra sucursal.

Dos niveles de rutas, nunca mezclados (ver service.py para la regla
completa):
  - `/reservas/{reserva_id}/confirmar-llegada` y
    `/reservas/{reserva_id}/finalizar-atencion` -- UN solo botón por
    reserva, cambian `estado_general` de la CABECERA.
  - `/reservas/detalles/{detalle_id}/preparar` |
    `/detalles/{detalle_id}/no-la-compra` |
    `/detalles/{detalle_id}/enviar-a-caja` -- por PRENDA, cambian solo el
    `estado` de ESE detalle.
`/reservas/panel` sigue devolviendo la vista agrupada: una entrada por
reserva (cabecera), con todas sus prendas anidadas en `detalles`.

Comparte el prefijo "/reservas" con CU17/CU18/CU19 (router propio, registrado
aparte en app/main.py -- mismo patrón ya usado por esos tres). Las rutas de
cabecera de CU20 (`/reservas/{reserva_id}/confirmar-llegada` y
`/finalizar-atencion`) conviven sin ambigüedad con las de CU19
(`/reservas/{reserva_id}/cancelar`, POST /reservas de CU17,
`/reservas/{reserva_id}/detalles`): mismo prefijo de profundidad, pero un
segmento final distinto en cada una.

GET /cajero/pendientes es SOLO CONSULTA: devuelve cabeceras completas cuyo
estado_general YA es LISTA_PARA_CAJA -- nunca una reserva todavía
EN_ATENCION, aunque alguna de sus prendas ya tenga esa decisión tomada (ver
AtenderReservaService.listar_pendientes_cajero). No crea venta, no crea
pago, no descuenta stock -- eso es CU24/CU25, todavía fuera de alcance.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import ReservaDetallePanelOut, ReservaPanelOut
from .service import (
    AtenderReservaService,
    DecisionesPendientesError,
    ReservaNoEncontradaError,
    ReservaVencidaError,
    TransicionInvalidaError,
)

require_encargado = require_roles(RolUsuario.ENCARGADO_SUCURSAL)
require_cajero = require_roles(RolUsuario.CAJERO)

router = APIRouter(prefix="/reservas", tags=["CU20 - Atender reserva de prendas"])


def _sucursal_id_del_actor(actor: Usuario) -> int:
    if actor.sucursal_id is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Esta cuenta no está vinculada a ninguna sucursal."
        )
    return actor.sucursal_id


def _manejar_vencida(exc: ReservaVencidaError) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "La reserva venció (el bloque horario ya terminó sin que el cliente llegara) y ya no "
        "puede atenderse.",
    )


@router.get("/panel", response_model=list[ReservaPanelOut])
def listar_panel(
    db: Session = Depends(get_db), actor: Usuario = Depends(require_encargado)
) -> list[ReservaPanelOut]:
    return AtenderReservaService(db).listar_panel(_sucursal_id_del_actor(actor))


@router.get("/cajero/pendientes", response_model=list[ReservaPanelOut])
def listar_pendientes_cajero(
    db: Session = Depends(get_db), actor: Usuario = Depends(require_cajero)
) -> list[ReservaPanelOut]:
    """Integración mínima de CU20 con el rol Cajero -- "Reservas pendientes
    de atención": cabeceras completas (agrupadas, con sus prendas
    LISTA_PARA_CAJA anidadas) cuyo estado_general YA es LISTA_PARA_CAJA, de
    SU sucursal (resuelta del token). Sigue siendo consulta pura: no crea
    venta ni pago (CU24/CU25)."""
    return AtenderReservaService(db).listar_pendientes_cajero(_sucursal_id_del_actor(actor))


@router.patch("/{reserva_id}/confirmar-llegada", response_model=ReservaPanelOut)
def confirmar_llegada_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> ReservaPanelOut:
    """UN solo botón por reserva -- "el cliente llegó a la sucursal para
    esta reserva". Cambia estado_general a EN_ATENCION; NUNCA toca el
    estado individual de ningún detalle."""
    try:
        return AtenderReservaService(db).confirmar_llegada_reserva(_sucursal_id_del_actor(actor), reserva_id)
    except ReservaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada.") from exc
    except ReservaVencidaError as exc:
        raise _manejar_vencida(exc) from exc
    except TransicionInvalidaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Solo se puede confirmar la llegada de una reserva pendiente o ya preparada.",
        ) from exc


@router.patch("/{reserva_id}/finalizar-atencion", response_model=ReservaPanelOut)
def finalizar_atencion(
    reserva_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> ReservaPanelOut:
    """UN solo botón por reserva -- cierra la atención completa. Requiere
    que NINGÚN detalle activo siga PENDIENTE/PREPARADA (todos con decisión
    tomada). Libera stock_reservado de las prendas "no la compra" y deja la
    cabecera en LISTA_PARA_CAJA (si hay al menos una prenda para caja) o
    ATENDIDA (si ninguna) -- recién en este momento el Cajero puede verla."""
    try:
        return AtenderReservaService(db).finalizar_atencion(_sucursal_id_del_actor(actor), reserva_id)
    except ReservaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada.") from exc
    except TransicionInvalidaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Solo se puede finalizar la atención de una reserva en atención.",
        ) from exc
    except DecisionesPendientesError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Todavía hay prendas sin una decisión (\"no la compra\" o \"enviar a caja\").",
        ) from exc


@router.patch("/detalles/{detalle_id}/preparar", response_model=ReservaDetallePanelOut)
def preparar_detalle(
    detalle_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> ReservaDetallePanelOut:
    try:
        return AtenderReservaService(db).preparar(_sucursal_id_del_actor(actor), detalle_id)
    except ReservaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada.") from exc
    except ReservaVencidaError as exc:
        raise _manejar_vencida(exc) from exc
    except TransicionInvalidaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Solo se puede preparar una prenda pendiente."
        ) from exc


@router.patch("/detalles/{detalle_id}/no-la-compra", response_model=ReservaDetallePanelOut)
def decidir_no_comprar(
    detalle_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> ReservaDetallePanelOut:
    """Decisión por prenda (reserva ya EN_ATENCION, detalle PREPARADA): el
    Cliente no se la lleva. NO libera stock todavía -- eso ocurre recién al
    "Finalizar atención" de toda la reserva."""
    try:
        return AtenderReservaService(db).decidir_no_comprar(_sucursal_id_del_actor(actor), detalle_id)
    except ReservaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada.") from exc
    except TransicionInvalidaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Solo se puede decidir sobre una prenda preparada, con la reserva en atención.",
        ) from exc


@router.patch("/detalles/{detalle_id}/enviar-a-caja", response_model=ReservaDetallePanelOut)
def decidir_enviar_a_caja(
    detalle_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> ReservaDetallePanelOut:
    """Decisión por prenda (reserva ya EN_ATENCION, detalle PREPARADA): el
    Cliente sí se la lleva. Marcador persistente únicamente -- todavía no
    llega al Cajero hasta "Finalizar atención" de toda la reserva."""
    try:
        return AtenderReservaService(db).decidir_enviar_a_caja(_sucursal_id_del_actor(actor), detalle_id)
    except ReservaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada.") from exc
    except TransicionInvalidaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Solo se puede decidir sobre una prenda preparada, con la reserva en atención.",
        ) from exc
