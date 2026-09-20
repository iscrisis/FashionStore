"""Reglas de negocio de CU19 -- Cancelar reserva (Cliente).

cliente_id llega SIEMPRE ya resuelto desde el usuario autenticado (ver
router.py) -- nunca desde un id que el cliente pueda manipular, así un
Cliente no puede cancelar una reserva de otro. ReservaNoEncontradaError se
usa tanto si la reserva/detalle no existe COMO si pertenece a otro cliente
(mismo mensaje en el router) -- mismo patrón ya usado en CU13
(ProductoNoEncontradoError): no revela la existencia de reservas ajenas.

Dos formas de cancelar, ambas sobre reservas que aún no llegaron a la
sucursal (PENDIENTE o PREPARADA -- desde EN_ATENCION en adelante el
Encargado ya empezó a atenderla, ver CU20):

  - `cancelar_detalle`: cancela UNA prenda dentro de una reserva (ej. el
    Cliente ya no quiere la camisa, pero sigue queriendo la chaqueta y el
    pantalón) -- libera únicamente el stock_reservado de ESE detalle.
  - `cancelar_reserva`: cancela la visita ENTERA -- todos los detalles que
    todavía estén PENDIENTE o PREPARADA pasan a CANCELADA, liberando el
    stock_reservado de cada uno; un detalle que ya avanzó más allá de eso
    (EN_ATENCION, LISTA_PARA_CAJA, ATENDIDA) queda intacto -- cancelar la
    reserva no reversa lo que el Encargado ya hizo con otras prendas.

En ambos casos, `estado_general` de la cabecera se recalcula al final a
partir del `estado` real de cada detalle (ver
Models/reserva.py:calcular_estado_general) -- nunca se fuerza a CANCELADA a
mano: si algún detalle no era cancelable, el agregado lo refleja. Ese
recálculo SOLO ocurre si la cabecera todavía está en la fase previa a la
llegada (PENDIENTE/PREPARADA, mismos estados que _ESTADOS_CANCELABLES): una
vez que el Encargado confirmó la llegada (CU20 -- estado_general pasa a
EN_ATENCION de forma EXPLÍCITA, ya no gobernada por este cálculo agregado),
cancelar un detalle que todavía seguía PENDIENTE/PREPARADA nunca debe volver
a recalcular la cabecera -- haría que el agregado la "regresara" a PREPARADA
o similar, pisando el EN_ATENCION que puso CU20.

Todo (relectura de estado ya bloqueada, liberar stock_reservado, cambiar
estado, recalcular estado_general) se confirma en un único commit por
operación -- nunca puede quedar una cancelación a medias; si algo falla
antes del commit, no se escribe nada (rollback implícito de la sesión, ver
app/db/session.py get_db).
"""

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P4_ReservasYAtencion.CU17_CrearReservaPrendas.schemas import (
    ColorResumen,
    ProductoResumen,
    ReservaDetalleOut,
    ReservaOut,
    TallaResumen,
    VarianteResumen,
)
from modules.P4_ReservasYAtencion.CU17_CrearReservaPrendas.service import reserva_a_salida
from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva, Reserva, ReservaDetalle

from .repository import ProductoLecturaRepository, ReservaDetalleRepository, ReservaRepository, StockSucursalRepository

_ESTADOS_CANCELABLES = (EstadoReserva.PENDIENTE, EstadoReserva.PREPARADA)


class ReservaNoEncontradaError(Exception):
    """No existe, o no pertenece al cliente autenticado (mismo mensaje: no
    revela la existencia de reservas de otro cliente)."""


class ReservaNoCancelableError(Exception):
    """No hay nada cancelable -- CU19 solo cancela detalles PENDIENTE o
    PREPARADA (el Cliente todavía no llegó a la sucursal por esa prenda).
    Desde EN_ATENCION en adelante (ver CU20) el Encargado ya empezó a
    atenderla y cancelar dejaría de tener sentido."""


class CancelarReservaService:
    def __init__(self, db: Session):
        self._db = db
        self._reservas = ReservaRepository(db)
        self._detalles = ReservaDetalleRepository(db)
        self._productos = ProductoLecturaRepository(db)
        self._stock = StockSucursalRepository(db)

    def cancelar_detalle(self, cliente_id: int, detalle_id: int) -> ReservaDetalleOut:
        detalle = self._detalles.bloquear_por_id(detalle_id)
        if detalle is None or detalle.reserva.cliente_id != cliente_id:
            raise ReservaNoEncontradaError
        if detalle.estado not in _ESTADOS_CANCELABLES:
            raise ReservaNoCancelableError

        self._liberar_y_cancelar(detalle)

        cabecera = self._reservas.bloquear_por_id(detalle.reserva_id)
        if cabecera.estado_general in _ESTADOS_CANCELABLES:
            cabecera.recalcular_estado_general()
        self._reservas.guardar()
        self._db.refresh(detalle)

        return self._detalle_a_salida(detalle)

    def cancelar_reserva(self, cliente_id: int, reserva_id: int) -> ReservaOut:
        cabecera = self._reservas.bloquear_por_id(reserva_id)
        if cabecera is None or cabecera.cliente_id != cliente_id:
            raise ReservaNoEncontradaError

        candidatos_ids = [d.id for d in cabecera.detalles if d.estado in _ESTADOS_CANCELABLES]
        if not candidatos_ids:
            raise ReservaNoCancelableError

        for detalle_id in candidatos_ids:
            detalle = self._detalles.bloquear_por_id(detalle_id)
            # Re-chequeo bajo lock: en el intervalo entre leer `cabecera.detalles`
            # (paso anterior, sin lock por detalle) y llegar aquí, otra
            # transacción podría haber cambiado este detalle -- si ya no es
            # cancelable, se deja tal cual, nunca se fuerza.
            if detalle is None or detalle.estado not in _ESTADOS_CANCELABLES:
                continue
            self._liberar_y_cancelar(detalle)

        if cabecera.estado_general in _ESTADOS_CANCELABLES:
            cabecera.recalcular_estado_general()
        self._reservas.guardar()
        self._reservas.refrescar(cabecera)

        productos_por_variante = self._productos_por_variante(cabecera)
        return reserva_a_salida(cabecera, productos_por_variante)

    def _liberar_y_cancelar(self, detalle: ReservaDetalle) -> None:
        stock = self._stock.bloquear_para_liberar(detalle.reserva.sucursal_id, detalle.producto_variante_id)
        if stock is not None:
            # max(0, ...) por seguridad: stock_reservado NUNCA debe quedar
            # negativo (también protegido por CheckConstraint en la base).
            stock.stock_reservado = max(0, stock.stock_reservado - detalle.cantidad)
        detalle.estado = EstadoReserva.CANCELADA

    def _productos_por_variante(self, cabecera: Reserva) -> dict[int, Producto]:
        productos: dict[int, Producto] = {}
        for detalle in cabecera.detalles:
            variante = detalle.producto_variante
            if variante.id in productos:
                continue
            producto = self._productos.get_by_id(variante.producto_id)
            if producto is not None:
                productos[variante.id] = producto
        return productos

    def _detalle_a_salida(self, detalle: ReservaDetalle) -> ReservaDetalleOut:
        variante = detalle.producto_variante
        producto = self._productos.get_by_id(variante.producto_id)
        return ReservaDetalleOut(
            id=detalle.id,
            producto=ProductoResumen(
                id=producto.id, nombre=producto.nombre, imagen_principal_url=producto.imagen_principal_url
            ),
            variante=VarianteResumen(
                id=variante.id,
                talla=TallaResumen.model_validate(variante.talla),
                color=ColorResumen.model_validate(variante.color),
            ),
            cantidad=detalle.cantidad,
            estado=detalle.estado.value,
        )
