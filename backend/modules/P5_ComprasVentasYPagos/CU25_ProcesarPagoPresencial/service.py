"""Reglas de negocio de CU25 -- Procesar pago presencial (Cajero).

sucursal_id llega SIEMPRE resuelto desde `actor.sucursal_id` (el Cajero
autenticado) -- nunca desde un valor que Angular pueda enviar. Tampoco se
confía en `cajero_id`, `estado` ni `total` que Angular envíe: el Cajero sale
del token, el estado se vuelve a leer de la Venta bloqueada, y el total se
recalcula desde los propios VentaDetalle (frozen por CU24, nunca desde
Angular ni desde el precio ACTUAL del producto -- ver más abajo).

confirmar_pago() hace, en una única transacción:
  1. Bloquea la Venta (FOR UPDATE) y verifica que sea de esta sucursal, sea
     PRESENCIAL y siga PENDIENTE_PAGO -- una Venta ya PAGADA se rechaza
     explícitamente (nunca se cobra dos veces).
  2. Recalcula el total desde los VentaDetalle YA guardados por CU24 (nunca
     desde el precio actual del producto: ese precio quedó congelado al
     armar la venta, cambiar el precio del producto después NO debe afectar
     una venta que el Cajero ya le mostró al Cliente) -- es una verificación
     de integridad, no un recálculo de precios.
  3. Bloquea las filas de StockSucursal involucradas y valida disponibilidad
     según el ORIGEN de la Venta:
       - DIRECTA: `cantidad <= stock_actual - stock_reservado` (nunca puede
         consumir unidades reservadas por otro Cliente).
       - RESERVA: esas unidades YA están en `stock_reservado` desde que se
         creó la reserva (CU17) -- se valida que siga habiendo esa cantidad
         reservada (y física) antes de tocar nada, pero no se exige
         `disponible` libre para ellas.
  4. Valida los datos propios del método (EFECTIVO: monto_recibido >=
     total; TARJETA/QR: nada obligatorio más allá del tipo).
  5. Recién ahí muta: descuenta stock_actual (y, si es RESERVA, también
     stock_reservado), marca la Venta PAGADA, crea el Pago ya PAGADO, y si
     la Venta vino de una Reserva, marca sus detalles LISTA_PARA_CAJA como
     ATENDIDA y recalcula `estado_general` (mismo método que ya usa CU19/
     CU20, nunca se asigna a mano) -- SOLO ahora, nunca antes de confirmar
     el pago.

Si el Cajero cierra el modal sin pagar, o cualquier validación falla, no se
ejecuta ninguna mutación: la Venta queda exactamente como CU24 la dejó
(PENDIENTE_PAGO), lista para reintentarse sin duplicar nada.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva
from modules.P5_ComprasVentasYPagos.Models.pago import EstadoPago, Pago, ProveedorPago, TipoTarjeta
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta, OrigenVenta, TipoVenta, Venta

from .repository import PagoRepository, ReservaRepository, StockSucursalRepository, VentaRepository
from .schemas import (
    ConfirmarPagoEfectivoRequest,
    ConfirmarPagoQrRequest,
    ConfirmarPagoRequest,
    ConfirmarPagoTarjetaRequest,
    PagoConfirmadoOut,
)


class SucursalCajeroNoDefinidaError(Exception):
    """El Cajero autenticado no tiene sucursal_id."""


class VentaNoEncontradaError(Exception):
    """No existe, o no pertenece a la sucursal del Cajero autenticado (mismo
    mensaje: no revela la existencia de ventas de otra sucursal)."""


class VentaNoPagableError(Exception):
    """No es PRESENCIAL, o el total no coincide con sus VentaDetalle
    (integridad) -- nunca debería ocurrir, defensa adicional."""


class VentaYaPagadaError(Exception):
    """Esa Venta ya está PAGADA -- no se cobra dos veces."""


class StockInsuficienteError(Exception):
    """DIRECTA: la cantidad supera `stock_actual - stock_reservado`.
    RESERVA: la cantidad supera lo realmente reservado (o el stock físico
    disponible) -- caso extremo, defensa adicional."""


class MontoRecibidoInsuficienteError(Exception):
    """EFECTIVO: monto_recibido < total."""


class PagoPresencialService:
    def __init__(self, db: Session):
        self._db = db
        self._ventas = VentaRepository(db)
        self._stock = StockSucursalRepository(db)
        self._reservas = ReservaRepository(db)
        self._pagos = PagoRepository(db)

    @staticmethod
    def _sucursal_de(cajero: Usuario) -> int:
        if cajero.sucursal_id is None:
            raise SucursalCajeroNoDefinidaError
        return cajero.sucursal_id

    @staticmethod
    def _requerido_por_variante(venta: Venta) -> dict[int, int]:
        requerido: dict[int, int] = {}
        for detalle in venta.detalles:
            requerido[detalle.producto_variante_id] = requerido.get(detalle.producto_variante_id, 0) + detalle.cantidad
        return requerido

    def confirmar_pago(self, cajero: Usuario, venta_id: int, datos: ConfirmarPagoRequest) -> PagoConfirmadoOut:
        sucursal_id = self._sucursal_de(cajero)

        venta = self._ventas.bloquear_por_id(venta_id)
        if venta is None or venta.sucursal_id != sucursal_id:
            raise VentaNoEncontradaError
        if venta.tipo != TipoVenta.PRESENCIAL:
            raise VentaNoPagableError
        if venta.estado == EstadoVenta.PAGADA:
            raise VentaYaPagadaError
        if venta.estado != EstadoVenta.PENDIENTE_PAGO:
            raise VentaNoPagableError

        # Integridad: el total SIEMPRE sale de los VentaDetalle ya
        # congelados por CU24 -- nunca del precio actual del producto ni de
        # nada que envíe Angular.
        total = sum((detalle.subtotal for detalle in venta.detalles), Decimal("0"))
        if total != venta.total or total <= 0:
            raise VentaNoPagableError

        requerido = self._requerido_por_variante(venta)
        stock_bloqueado = self._stock.bloquear_filas(sucursal_id, list(requerido.keys()))

        for variante_id, cantidad in requerido.items():
            fila = stock_bloqueado.get(variante_id)
            if venta.origen == OrigenVenta.DIRECTA:
                disponible = (fila.cantidad - fila.stock_reservado) if fila is not None else 0
                if cantidad > disponible:
                    raise StockInsuficienteError
            else:
                # RESERVA: esas unidades ya están comprometidas en
                # stock_reservado desde CU17 -- se valida que sigan estando
                # (nunca se exige "disponible" libre para ellas), y que el
                # físico alcance, para no dejar ninguna columna negativa.
                reservado_actual = fila.stock_reservado if fila is not None else 0
                fisico_actual = fila.cantidad if fila is not None else 0
                if cantidad > reservado_actual or cantidad > fisico_actual:
                    raise StockInsuficienteError

        pago = self._construir_pago(venta.id, total, cajero.id, datos)

        for variante_id, cantidad in requerido.items():
            fila = stock_bloqueado[variante_id]
            fila.cantidad -= cantidad
            if venta.origen == OrigenVenta.RESERVA:
                fila.stock_reservado -= cantidad

        venta.estado = EstadoVenta.PAGADA

        if venta.origen == OrigenVenta.RESERVA and venta.reserva_id is not None:
            reserva = self._reservas.bloquear_por_id(venta.reserva_id)
            if reserva is not None:
                for detalle in reserva.detalles:
                    if detalle.estado == EstadoReserva.LISTA_PARA_CAJA:
                        detalle.estado = EstadoReserva.ATENDIDA
                # Nunca se asigna estado_general a mano -- se recalcula
                # desde los detalles ya actualizados (mismo método que
                # CU19/CU20).
                reserva.recalcular_estado_general()

        self._pagos.crear(pago)
        self._ventas.refrescar(venta)

        return self._a_salida(venta, pago)

    def _construir_pago(
        self, venta_id: int, total: Decimal, cajero_id: int, datos: ConfirmarPagoRequest
    ) -> Pago:
        ahora = _ahora()
        if isinstance(datos, ConfirmarPagoEfectivoRequest):
            monto_recibido = Decimal(str(datos.monto_recibido))
            if monto_recibido < total:
                raise MontoRecibidoInsuficienteError
            cambio = monto_recibido - total
            return Pago(
                venta_id=venta_id,
                proveedor=ProveedorPago.EFECTIVO,
                monto=total,
                estado=EstadoPago.PAGADO,
                fecha_confirmacion=ahora,
                cajero_id=cajero_id,
                monto_recibido=monto_recibido,
                cambio=cambio,
            )
        if isinstance(datos, ConfirmarPagoTarjetaRequest):
            return Pago(
                venta_id=venta_id,
                proveedor=ProveedorPago.TARJETA,
                monto=total,
                estado=EstadoPago.PAGADO,
                fecha_confirmacion=ahora,
                cajero_id=cajero_id,
                tipo_tarjeta=TipoTarjeta(datos.tipo_tarjeta),
                referencia=datos.referencia,
            )
        if isinstance(datos, ConfirmarPagoQrRequest):
            return Pago(
                venta_id=venta_id,
                proveedor=ProveedorPago.QR,
                monto=total,
                estado=EstadoPago.PAGADO,
                fecha_confirmacion=ahora,
                cajero_id=cajero_id,
                referencia=datos.referencia,
            )
        raise VentaNoPagableError  # pragma: no cover -- discriminador ya lo impide a nivel de schema

    @staticmethod
    def _a_salida(venta: Venta, pago: Pago) -> PagoConfirmadoOut:
        return PagoConfirmadoOut(
            codigo_venta=venta.codigo_venta,
            total=venta.total,
            metodo_pago=pago.proveedor.value,
            monto_recibido=pago.monto_recibido,
            cambio=pago.cambio,
        )


def _ahora() -> datetime:
    return datetime.now(timezone.utc)
