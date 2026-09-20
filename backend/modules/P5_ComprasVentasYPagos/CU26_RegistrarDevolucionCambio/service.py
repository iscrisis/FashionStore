"""Reglas de negocio de CU26 -- Registrar devolución o cambio (Cajero).

sucursal_id llega SIEMPRE resuelto desde `actor.sucursal_id` (el Cajero
autenticado) -- nunca desde un valor que Angular pueda enviar: un Cajero solo
puede buscar y operar ventas PAGADAS de SU PROPIA sucursal. Tampoco se confía
en `cajero_id`, montos, precios ni estado que Angular envíe: el Cajero sale
del token, el monto de reembolso se recalcula SIEMPRE desde
`VentaDetalle.precio_unitario` (congelado por CU22/CU24, nunca el precio
ACTUAL del producto), y el estado se vuelve a leer de la Venta bloqueada.

buscar_venta() es de solo lectura -- localiza la Venta por `codigo_venta`
(NUNCA lista todas las ventas), exige PAGADA, y devuelve únicamente las
líneas que TODAVÍA tienen unidades sin devolver/cambiar (ver
`cantidad_operada_por_detalle` en repository.py).

registrar_devolucion() / registrar_cambio() hacen, cada una, en una única
transacción:
  1. Bloquean la Venta (FOR UPDATE) y verifican sucursal + PAGADA.
  2. Bloquean el VentaDetalle (FOR UPDATE) y verifican que pertenezca a esa
     Venta.
  3. Recalculan `cantidad_operada_por_detalle` YA DENTRO del bloqueo (nunca
     antes) -- así dos operaciones concurrentes sobre la MISMA línea jamás
     devuelven/cambian, entre ambas, más unidades que las compradas.
  4. Bloquean las filas de StockSucursal involucradas y validan
     disponibilidad (solo CAMBIO: la variante nueva necesita
     `stock_actual - stock_reservado` suficiente -- nunca puede consumir
     unidades reservadas por una Reserva de otro Cliente, CU17).
  5. Recién ahí mutan: reintegran stock (y, en CAMBIO, descuentan la
     variante nueva), y crean el registro DevolucionCambio -- si es
     DEVOLUCION, con el reembolso ya resuelto (ver `_resolver_reembolso`).

Si cualquier validación falla, no se ejecuta ninguna mutación: la Venta, sus
detalles y el stock quedan exactamente como estaban.

CAMBIO exige que la variante nueva sea del MISMO producto que la original
(ver VarianteMismoProductoError) -- eso GARANTIZA, por construcción, el mismo
precio (`Producto.precio_venta` es por producto, no por variante), así que
CU26 nunca necesita calcular ni bloquear una diferencia de precio: un cambio
nunca genera un nuevo cobro ni un reembolso parcial.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.integrations.stripe_client import crear_refund
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P5_ComprasVentasYPagos.Models.devolucion import (
    DevolucionCambio,
    EstadoReembolso,
    MotivoDevolucion,
    TipoOperacionDevolucion,
)
from modules.P5_ComprasVentasYPagos.Models.pago import ProveedorPago
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta

from .repository import (
    DevolucionCambioRepository,
    PagoRepository,
    ProductoLecturaRepository,
    ProductoVarianteRepository,
    StockSucursalRepository,
    UsuarioLecturaRepository,
    VentaDetalleRepository,
    VentaRepository,
)
from .schemas import (
    CambioOut,
    ColorResumen,
    DetalleDevolucionOut,
    DevolucionOut,
    ProductoResumen,
    RegistrarCambioRequest,
    RegistrarDevolucionRequest,
    SucursalResumen,
    TallaResumen,
    VarianteCambioOut,
    VarianteResumen,
    VentaDevolucionOut,
)


class SucursalCajeroNoDefinidaError(Exception):
    """El Cajero autenticado no tiene sucursal_id."""


class VentaNoEncontradaError(Exception):
    """No existe, no pertenece a la sucursal del Cajero autenticado, o no
    está PAGADA -- mismo mensaje genérico para los tres casos (no revela la
    existencia de ventas de otra sucursal ni su estado real)."""


class VentaDetalleNoEncontradoError(Exception):
    """No existe, o no pertenece a la Venta indicada."""


class CantidadInvalidaError(Exception):
    """La cantidad pedida supera lo que todavía puede devolverse/cambiarse
    de esa línea (`cantidad_comprada - ya_operado`)."""


class ObservacionRequeridaError(Exception):
    """motivo == OTRO sin una observación."""


class VarianteNoEncontradaError(Exception):
    """La variante nueva no existe, o no está activa (ella o su producto)."""


class VarianteMismoProductoError(Exception):
    """La variante nueva no pertenece al mismo producto que la original --
    CU26 (MVP) solo permite cambiar talla/color, nunca de producto."""


class VarianteIgualError(Exception):
    """La variante nueva es la misma que la original -- no hay nada que
    cambiar."""


class StockInsuficienteError(Exception):
    """La variante nueva no tiene disponibilidad suficiente
    (`stock_actual - stock_reservado`), o la variante original no tiene fila
    de stock registrada en esta sucursal (defensivo)."""


class PagoNoEncontradoError(Exception):
    """Defensivo -- una Venta PAGADA siempre debería tener un Pago PAGADO
    (CU23/CU25 lo crean en la misma transacción que marcan la Venta)."""


class DevolucionCambioService:
    def __init__(self, db: Session):
        self._db = db
        self._ventas = VentaRepository(db)
        self._detalles = VentaDetalleRepository(db)
        self._devoluciones = DevolucionCambioRepository(db)
        self._pagos = PagoRepository(db)
        self._variantes = ProductoVarianteRepository(db)
        self._stock = StockSucursalRepository(db)
        self._productos = ProductoLecturaRepository(db)
        self._usuarios = UsuarioLecturaRepository(db)

    @staticmethod
    def _sucursal_de(cajero: Usuario) -> int:
        if cajero.sucursal_id is None:
            raise SucursalCajeroNoDefinidaError
        return cajero.sucursal_id

    def buscar_venta(self, cajero: Usuario, codigo_venta: str) -> VentaDevolucionOut:
        sucursal_id = self._sucursal_de(cajero)

        venta = self._ventas.obtener_por_codigo(codigo_venta.strip().upper())
        if venta is None or venta.sucursal_id != sucursal_id or venta.estado != EstadoVenta.PAGADA:
            raise VentaNoEncontradaError

        pago = self._pagos.obtener_pagado_por_venta(venta.id)
        if pago is None:
            raise PagoNoEncontradoError

        producto_ids = {d.producto_variante.producto_id for d in venta.detalles}
        productos = self._productos.get_by_ids(producto_ids)

        detalles_out: list[DetalleDevolucionOut] = []
        for detalle in venta.detalles:
            disponible = detalle.cantidad - self._devoluciones.cantidad_operada_por_detalle(detalle.id)
            if disponible <= 0:
                continue
            variante = detalle.producto_variante
            producto = productos.get(variante.producto_id)
            if producto is None:
                continue
            detalles_out.append(
                DetalleDevolucionOut(
                    venta_detalle_id=detalle.id,
                    producto=ProductoResumen(
                        id=producto.id, nombre=producto.nombre, imagen_principal_url=producto.imagen_principal_url
                    ),
                    variante=VarianteResumen(
                        id=variante.id,
                        talla=TallaResumen.model_validate(variante.talla),
                        color=ColorResumen.model_validate(variante.color),
                    ),
                    cantidad_comprada=detalle.cantidad,
                    cantidad_disponible=disponible,
                    precio_unitario=detalle.precio_unitario,
                )
            )

        cliente_nombre = None
        if venta.cliente_id is not None:
            cliente = self._usuarios.get_by_id(venta.cliente_id)
            cliente_nombre = cliente.nombre if cliente is not None else None

        return VentaDevolucionOut(
            venta_id=venta.id,
            codigo_venta=venta.codigo_venta,
            fecha_creacion=venta.fecha_creacion,
            sucursal=SucursalResumen(id=venta.sucursal.id, nombre=venta.sucursal.nombre),
            cliente_nombre=cliente_nombre,
            tipo=venta.tipo.value,
            metodo_pago=pago.proveedor.value,
            total=venta.total,
            detalles=detalles_out,
        )

    def opciones_cambio(self, cajero: Usuario, venta_id: int, venta_detalle_id: int) -> list[VarianteCambioOut]:
        sucursal_id = self._sucursal_de(cajero)

        venta = self._ventas.obtener_por_id(venta_id)
        if venta is None or venta.sucursal_id != sucursal_id or venta.estado != EstadoVenta.PAGADA:
            raise VentaNoEncontradaError

        detalle = next((d for d in venta.detalles if d.id == venta_detalle_id), None)
        if detalle is None:
            raise VentaDetalleNoEncontradoError

        variante_original = detalle.producto_variante
        opciones = self._variantes.listar_activas_por_producto(
            variante_original.producto_id, excluir_id=variante_original.id
        )
        variante_ids = [v.id for v in opciones]
        disponible_map = self._stock.disponible_por_variantes(venta.sucursal_id, variante_ids)

        return [
            VarianteCambioOut(
                producto_variante_id=v.id,
                talla=TallaResumen.model_validate(v.talla),
                color=ColorResumen.model_validate(v.color),
                disponible=max(disponible_map.get(v.id, 0), 0),
            )
            for v in opciones
        ]

    def registrar_devolucion(self, cajero: Usuario, datos: RegistrarDevolucionRequest) -> DevolucionOut:
        sucursal_id = self._sucursal_de(cajero)

        venta = self._ventas.bloquear_por_id(datos.venta_id)
        if venta is None or venta.sucursal_id != sucursal_id or venta.estado != EstadoVenta.PAGADA:
            raise VentaNoEncontradaError

        detalle = self._detalles.bloquear_por_id(datos.venta_detalle_id)
        if detalle is None or detalle.venta_id != venta.id:
            raise VentaDetalleNoEncontradoError

        if datos.motivo == "OTRO" and not (datos.observacion or "").strip():
            raise ObservacionRequeridaError

        disponible = detalle.cantidad - self._devoluciones.cantidad_operada_por_detalle(detalle.id)
        if datos.cantidad > disponible:
            raise CantidadInvalidaError

        pago = self._pagos.obtener_pagado_por_venta(venta.id)
        if pago is None:
            raise PagoNoEncontradoError

        monto_reembolso = detalle.precio_unitario * datos.cantidad

        # Todas las validaciones/bloqueos internos SIEMPRE antes de tocar
        # Stripe (ver `_resolver_reembolso` más abajo) -- un refund real es
        # irreversible por un rollback de esta transacción, así que ningún
        # motivo de fallo interno (stock sin fila registrada, etc.) puede
        # descubrirse DESPUÉS de haber cobrado el reembolso.
        stock_bloqueado = self._stock.bloquear_filas(venta.sucursal_id, [detalle.producto_variante_id])
        fila = stock_bloqueado.get(detalle.producto_variante_id)
        if fila is None:
            raise StockInsuficienteError

        metodo_reembolso, estado_reembolso, stripe_refund_id = self._resolver_reembolso(pago, monto_reembolso)

        fila.cantidad += datos.cantidad

        registro = DevolucionCambio(
            venta_id=venta.id,
            venta_detalle_id=detalle.id,
            tipo=TipoOperacionDevolucion.DEVOLUCION,
            cantidad=datos.cantidad,
            variante_original_id=detalle.producto_variante_id,
            variante_nueva_id=None,
            motivo=MotivoDevolucion(datos.motivo),
            observacion=(datos.observacion or "").strip() or None,
            monto_reembolso=monto_reembolso,
            metodo_reembolso=metodo_reembolso,
            estado_reembolso=estado_reembolso,
            stripe_refund_id=stripe_refund_id,
            cajero_id=cajero.id,
            sucursal_id=venta.sucursal_id,
        )
        self._devoluciones.crear(registro)

        return DevolucionOut(
            id=registro.id,
            cantidad=registro.cantidad,
            monto_reembolso=registro.monto_reembolso,
            metodo_reembolso=registro.metodo_reembolso.value if registro.metodo_reembolso else None,
            estado_reembolso=registro.estado_reembolso.value if registro.estado_reembolso else None,
            stripe_refund_id=registro.stripe_refund_id,
        )

    def registrar_cambio(self, cajero: Usuario, datos: RegistrarCambioRequest) -> CambioOut:
        sucursal_id = self._sucursal_de(cajero)

        venta = self._ventas.bloquear_por_id(datos.venta_id)
        if venta is None or venta.sucursal_id != sucursal_id or venta.estado != EstadoVenta.PAGADA:
            raise VentaNoEncontradaError

        detalle = self._detalles.bloquear_por_id(datos.venta_detalle_id)
        if detalle is None or detalle.venta_id != venta.id:
            raise VentaDetalleNoEncontradoError

        if datos.variante_nueva_id == detalle.producto_variante_id:
            raise VarianteIgualError

        variante_nueva = self._variantes.get_activa_by_id(datos.variante_nueva_id)
        if variante_nueva is None:
            raise VarianteNoEncontradaError

        variante_original = detalle.producto_variante
        if variante_nueva.producto_id != variante_original.producto_id:
            raise VarianteMismoProductoError

        disponible = detalle.cantidad - self._devoluciones.cantidad_operada_por_detalle(detalle.id)
        if datos.cantidad > disponible:
            raise CantidadInvalidaError

        stock_bloqueado = self._stock.bloquear_filas(
            venta.sucursal_id, [variante_original.id, variante_nueva.id]
        )
        fila_original = stock_bloqueado.get(variante_original.id)
        fila_nueva = stock_bloqueado.get(variante_nueva.id)
        if fila_original is None:
            raise StockInsuficienteError

        disponible_nueva = (fila_nueva.cantidad - fila_nueva.stock_reservado) if fila_nueva is not None else 0
        if datos.cantidad > disponible_nueva:
            raise StockInsuficienteError

        fila_original.cantidad += datos.cantidad
        fila_nueva.cantidad -= datos.cantidad  # type: ignore[union-attr] -- ya validado arriba, nunca None aquí

        registro = DevolucionCambio(
            venta_id=venta.id,
            venta_detalle_id=detalle.id,
            tipo=TipoOperacionDevolucion.CAMBIO,
            cantidad=datos.cantidad,
            variante_original_id=variante_original.id,
            variante_nueva_id=variante_nueva.id,
            motivo=None,
            observacion=None,
            monto_reembolso=None,
            metodo_reembolso=None,
            estado_reembolso=None,
            stripe_refund_id=None,
            cajero_id=cajero.id,
            sucursal_id=venta.sucursal_id,
        )
        self._devoluciones.crear(registro)

        return CambioOut(
            id=registro.id,
            cantidad=registro.cantidad,
            variante_original=VarianteResumen(
                id=variante_original.id,
                talla=TallaResumen.model_validate(variante_original.talla),
                color=ColorResumen.model_validate(variante_original.color),
            ),
            variante_nueva=VarianteResumen(
                id=variante_nueva.id,
                talla=TallaResumen.model_validate(variante_nueva.talla),
                color=ColorResumen.model_validate(variante_nueva.color),
            ),
        )

    @staticmethod
    def _resolver_reembolso(
        pago, monto_reembolso: Decimal
    ) -> tuple[ProveedorPago, EstadoReembolso, str | None]:
        """CASO 1 (EFECTIVO): el Cajero ya entregó el dinero en mano -- queda
        COMPLETADO de inmediato, FashionStore solo deja constancia (monto,
        fecha, cajero -- ver Models/devolucion.py).
        CASO 2/3 (TARJETA/QR): se procesan fuera del sistema (POS/app
        bancaria) -- queda REGISTRADO, el texto para el Cajero vive en el
        frontend (nunca se integra un proveedor nuevo).
        CASO 4 (STRIPE): refund real en modo TEST, por el monto exacto de la
        prenda devuelta -- nunca el total de la compra."""
        if pago.proveedor == ProveedorPago.STRIPE:
            if not pago.stripe_payment_intent_id:
                raise PagoNoEncontradoError
            refund = crear_refund(payment_intent_id=pago.stripe_payment_intent_id, monto=monto_reembolso)
            return ProveedorPago.STRIPE, EstadoReembolso.COMPLETADO, refund.id
        if pago.proveedor == ProveedorPago.EFECTIVO:
            return ProveedorPago.EFECTIVO, EstadoReembolso.COMPLETADO, None
        # TARJETA / QR
        return pago.proveedor, EstadoReembolso.REGISTRADO, None
