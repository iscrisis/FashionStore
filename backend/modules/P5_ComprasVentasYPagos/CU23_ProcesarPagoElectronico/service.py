"""Reglas de negocio de CU23 -- Procesar pago electrónico (Cliente).

cliente_id llega SIEMPRE ya resuelto desde el usuario autenticado (ver
router.py) -- nunca desde un id que el cliente pueda manipular. Un Cliente
solo puede pagar (o verificar el pago de) SU PROPIA Venta: tanto
crear_checkout como verificar_pago comparan `venta.cliente_id` contra el
cliente autenticado y rechazan con el mismo error genérico si no coincide
(no revela si esa Venta existe a nombre de otro).

Angular JAMÁS decide que una Venta está pagada. El único momento en que este
módulo marca una Venta como PAGADA es dentro de verificar_pago, después de
llamar directamente a la API de Stripe (ver app/integrations/stripe_client.py)
y confirmar `payment_status == "paid"`. El monto que se cobra en Stripe
SIEMPRE sale de `Venta.total` (calculado por FastAPI en CU22), nunca de un
valor que Angular envíe.

IDEMPOTENCIA: verificar_pago puede llamarse varias veces para el mismo
session_id (el Cliente refresca la pantalla de resultado, o dos pestañas
abiertas) sin duplicar nada -- ver el corto-circuito al inicio (Pago ya
PAGADO) y el bloqueo de la Venta (FOR UPDATE) antes de descontar stock o
borrar items del carrito, que vuelve a corto-circuitar si otra verificación
concurrente ya la dejó PAGADA primero.

Ninguna operación de este módulo:
  - toca stock_reservado (nadie lo escribió al confirmar la compra en CU22,
    así que no hay nada que liberar aquí -- solo se descuenta `cantidad`, el
    stock físico, y solo cuando el pago YA se confirmó);
  - permite que una Venta quede PAGADA dos veces, ni que el stock se
    descuente dos veces por la misma Venta;
  - elimina items del carrito que no formaron parte de esta Venta (ver
    Models/venta.py: VentaDetalle.carrito_item_id).
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.stripe_client import crear_checkout_session, obtener_checkout_session
from modules.P5_ComprasVentasYPagos.Models.pago import EstadoPago, Pago, ProveedorPago
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta, TipoVenta, Venta

from .repository import CarritoItemRepository, PagoRepository, StockSucursalRepository, VentaLecturaRepository
from .schemas import SucursalVentaOut, VentaPagadaOut


class VentaNoEncontradaError(Exception):
    """No existe, o no pertenece al cliente autenticado (mismo mensaje: no
    revela la existencia de ventas de otro cliente)."""


class VentaNoPagableError(Exception):
    """No es DIGITAL, no está PENDIENTE_PAGO, o no tiene total/detalles
    válidos -- ya fue pagada, o nunca debió llegar a este punto."""


class StockInsuficienteError(Exception):
    """Alguna variante de la Venta ya no tiene disponibilidad suficiente en
    su sucursal -- puede pasar tanto al iniciar el Checkout como (en el caso
    extremo) justo al confirmar un pago ya cobrado por Stripe."""


class SesionPagoNoEncontradaError(Exception):
    """El session_id no corresponde a ningún Pago del cliente autenticado."""


class PagoNoCompletadoError(Exception):
    """Stripe confirma que esa sesión NO está pagada (cancelada, fallida, o
    todavía abierta) -- la Venta se queda en PENDIENTE_PAGO, lista para un
    nuevo intento."""


class PagoElectronicoService:
    def __init__(self, db: Session):
        self._db = db
        self._ventas = VentaLecturaRepository(db)
        self._stock = StockSucursalRepository(db)
        self._pagos = PagoRepository(db)
        self._carrito_items = CarritoItemRepository(db)

    @staticmethod
    def _requerido_por_variante(venta: Venta) -> dict[int, int]:
        requerido: dict[int, int] = {}
        for detalle in venta.detalles:
            requerido[detalle.producto_variante_id] = requerido.get(detalle.producto_variante_id, 0) + detalle.cantidad
        return requerido

    def _resolver_venta_propia(self, cliente_id: int, venta_id: int) -> Venta:
        venta = self._ventas.obtener_por_id(venta_id)
        if venta is None or venta.cliente_id != cliente_id:
            raise VentaNoEncontradaError
        return venta

    def crear_checkout(self, cliente_id: int, venta_id: int, success_url: str, cancel_url: str) -> str:
        venta = self._resolver_venta_propia(cliente_id, venta_id)

        if venta.tipo != TipoVenta.DIGITAL or venta.estado != EstadoVenta.PENDIENTE_PAGO:
            raise VentaNoPagableError
        if venta.total <= 0 or not venta.detalles:
            raise VentaNoPagableError

        requerido = self._requerido_por_variante(venta)
        disponible = self._stock.disponible_por_variantes(venta.sucursal_id, list(requerido.keys()))
        if not all(disponible.get(vid, 0) >= cantidad for vid, cantidad in requerido.items()):
            raise StockInsuficienteError

        sesion = crear_checkout_session(
            monto=venta.total,
            descripcion=f"Compra FashionStore {venta.codigo_venta}",
            venta_id=venta.id,
            codigo_venta=venta.codigo_venta,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        pago = Pago(
            venta_id=venta.id,
            proveedor=ProveedorPago.STRIPE,
            stripe_checkout_session_id=sesion.id,
            monto=venta.total,
            estado=EstadoPago.PENDIENTE,
        )
        self._pagos.crear(pago)

        return sesion.url

    def verificar_pago(self, cliente_id: int, session_id: str) -> VentaPagadaOut:
        pago = self._pagos.obtener_por_session_id(session_id)
        if pago is None or pago.venta.cliente_id != cliente_id:
            raise SesionPagoNoEncontradaError

        # Idempotencia -- ya procesado en una verificación anterior: ni
        # vuelve a llamar a Stripe ni vuelve a tocar stock/carrito.
        if pago.estado == EstadoPago.PAGADO:
            return self._venta_pagada_a_salida(pago.venta)

        sesion = obtener_checkout_session(session_id)
        if sesion.payment_status != "paid":
            if pago.estado == EstadoPago.PENDIENTE:
                pago.estado = EstadoPago.CANCELADO if sesion.status == "expired" else EstadoPago.FALLIDO
                self._pagos.guardar()
            raise PagoNoCompletadoError

        # Stripe confirma el pago -- se bloquea la Venta PRIMERO (mismo
        # orden que CU17/CU22: cabecera antes que stock), así dos
        # verificaciones concurrentes de la MISMA venta nunca descuentan
        # stock dos veces ni duplican la limpieza del carrito.
        venta = self._ventas.bloquear_por_id(pago.venta_id)
        assert venta is not None

        if venta.estado == EstadoVenta.PAGADA:
            # Otra verificación concurrente ya la finalizó -- idempotente.
            if pago.estado != EstadoPago.PAGADO:
                pago.estado = EstadoPago.PAGADO
                pago.stripe_payment_intent_id = pago.stripe_payment_intent_id or sesion.payment_intent
                pago.fecha_confirmacion = pago.fecha_confirmacion or _ahora()
                self._pagos.guardar()
            return self._venta_pagada_a_salida(venta)

        requerido = self._requerido_por_variante(venta)
        stock_bloqueado = self._stock.bloquear_filas(venta.sucursal_id, list(requerido.keys()))
        for variante_id, cantidad in requerido.items():
            fila = stock_bloqueado.get(variante_id)
            disponible = (fila.cantidad - fila.stock_reservado) if fila is not None else 0
            if cantidad > disponible:
                # Caso extremo: el stock se agotó entre crear el Checkout y
                # confirmar el pago. Nunca se permite que `cantidad` quede
                # negativa -- se rechaza la finalización en vez de descontar
                # de más (ver CheckConstraint en StockSucursal).
                raise StockInsuficienteError

        for variante_id, cantidad in requerido.items():
            stock_bloqueado[variante_id].cantidad -= cantidad

        venta.estado = EstadoVenta.PAGADA
        pago.estado = EstadoPago.PAGADO
        pago.stripe_payment_intent_id = sesion.payment_intent
        pago.fecha_confirmacion = _ahora()

        # Elimina del carrito SOLO los items que formaron parte de ESTA
        # Venta -- los no seleccionados, y cualquier unidad agregada después
        # de confirmar la compra, quedan intactos (ver Models/venta.py).
        carrito_item_ids = [d.carrito_item_id for d in venta.detalles if d.carrito_item_id is not None]
        self._carrito_items.eliminar_por_ids(carrito_item_ids)

        # Un único commit: Venta + Pago + stock + limpieza del carrito
        # quedan consistentes juntos, o nada de eso se aplica.
        self._pagos.guardar()
        self._ventas.refrescar(venta)

        return self._venta_pagada_a_salida(venta)

    @staticmethod
    def _venta_pagada_a_salida(venta: Venta) -> VentaPagadaOut:
        return VentaPagadaOut(
            id=venta.id,
            codigo_venta=venta.codigo_venta,
            estado=venta.estado.value,
            total=venta.total,
            sucursal=SucursalVentaOut(
                id=venta.sucursal.id,
                nombre=venta.sucursal.nombre,
                direccion=venta.sucursal.direccion,
                ciudad=venta.sucursal.ciudad.nombre,
            ),
        )


def _ahora() -> datetime:
    return datetime.now(timezone.utc)
