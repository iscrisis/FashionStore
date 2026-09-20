"""Reglas de negocio de CU24 -- Registrar venta presencial (Cajero).

sucursal_id llega SIEMPRE resuelto desde `actor.sucursal_id` (el Cajero
autenticado) -- nunca desde un valor que Angular pueda enviar: un Cajero
solo puede consultar stock, registrar ventas y cargar reservas de SU PROPIA
sucursal.

Dos formas de armar la Venta, nunca mezcladas:
  - crear_venta_directa(): el Cajero eligió productos/variantes/cantidades a
    mano. Valida que cada cantidad quepa en `stock_actual - stock_reservado`
    de la sucursal del Cajero -- una venta directa JAMÁS puede consumir
    unidades ya reservadas por otro Cliente (CU17).
  - crear_venta_desde_reserva(): carga las prendas que CU20 ya dejó
    LISTA_PARA_CAJA en una Reserva de la MISMA sucursal. Esas prendas ya
    tienen su stock comprometido en `stock_reservado` desde que se creó la
    reserva -- CU24 no vuelve a validar disponibilidad contra
    `stock_actual - stock_reservado` para ellas (ya se validó al reservar) y
    NO permite modificar qué prendas ni cuántas unidades se cargan.

En AMBOS casos, CU24:
  - NUNCA modifica StockSucursal (ni `cantidad` ni `stock_reservado`) --
    solo valida. Descontar/liberar stock es responsabilidad de un CU25
    futuro, después de confirmar el pago.
  - NUNCA cambia el estado de la Reserva ni de sus ReservaDetalle -- sigue
    LISTA_PARA_CAJA hasta que CU25 la finalice.
  - Crea la Venta SIEMPRE en PENDIENTE_PAGO (CU24 no cobra, eso es CU25).
  - Calcula precio_unitario/subtotal/total SIEMPRE desde el precio EFECTIVO
    vigente en este momento (CU32 -- promoción ACTIVA si existe, ver
    P6_InnovacionYAnalisis/CU32_GestionarPromociones/precio_efectivo.py) --
    nunca un valor que envíe Angular. El Cajero vende SIEMPRE al mismo
    precio que ve la Web en ese instante, nunca a Producto.precio_venta
    "pelado" si hay una promoción activa.

crear_venta_desde_reserva() es idempotente por diseño: si ya existe una
Venta PENDIENTE_PAGO ligada a esa `reserva_id`, la reutiliza en vez de crear
una segunda (evita dos ventas activas para la misma reserva, p. ej. si el
Cajero pulsa "Cargar venta" dos veces).
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva, Reserva
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta, OrigenVenta, TipoVenta, Venta, VentaDetalle
from modules.P6_InnovacionYAnalisis.CU32_GestionarPromociones.precio_efectivo import obtener_precios_efectivos

from .repository import (
    ProductoLecturaRepository,
    ProductoVarianteLecturaRepository,
    ReservaLecturaRepository,
    StockSucursalRepository,
    UsuarioLecturaRepository,
    VentaRepository,
)
from .schemas import (
    ColorResumen,
    CrearVentaDirectaRequest,
    ProductoBusquedaOut,
    ProductoResumen,
    ReservaResumenOut,
    TallaResumen,
    VarianteResumen,
    VentaDetalleOut,
    VentaPresencialOut,
)


class SucursalCajeroNoDefinidaError(Exception):
    """El Cajero autenticado no tiene sucursal_id (no debería ocurrir en un
    uso normal, pero se valida explícitamente en vez de asumirlo)."""


class VarianteNoEncontradaError(Exception):
    """No existe, o no está activa (ella o su producto)."""


class StockInsuficienteError(Exception):
    """La cantidad pedida supera `stock_actual - stock_reservado` en la
    sucursal del Cajero -- una venta directa nunca puede consumir stock ya
    reservado por otro Cliente."""


class ReservaNoEncontradaError(Exception):
    """No existe esa reserva."""


class ReservaOtraSucursalError(Exception):
    """La reserva pertenece a una sucursal distinta a la del Cajero."""


class ReservaSinPrendasParaCajaError(Exception):
    """Esa reserva no tiene ningún detalle en estado LISTA_PARA_CAJA (ya se
    cargó todo, o ninguna prenda llegó a esa decisión)."""


class VentaPresencialService:
    def __init__(self, db: Session):
        self._db = db
        self._variantes = ProductoVarianteLecturaRepository(db)
        self._productos = ProductoLecturaRepository(db)
        self._stock = StockSucursalRepository(db)
        self._reservas = ReservaLecturaRepository(db)
        self._usuarios = UsuarioLecturaRepository(db)
        self._ventas = VentaRepository(db)

    @staticmethod
    def _sucursal_de(cajero: Usuario) -> int:
        if cajero.sucursal_id is None:
            raise SucursalCajeroNoDefinidaError
        return cajero.sucursal_id

    def buscar_productos(self, cajero: Usuario, nombre: str) -> list[ProductoBusquedaOut]:
        sucursal_id = self._sucursal_de(cajero)

        variantes = self._variantes.buscar_activas_por_nombre_producto(nombre)
        variante_ids = [v.id for v in variantes]
        disponible_map = self._stock.disponible_por_variantes(sucursal_id, variante_ids)

        producto_ids = {v.producto_id for v in variantes}
        productos = self._productos.get_activos_by_ids(producto_ids)
        precios = obtener_precios_efectivos(self._db, list(productos.values()))

        salida: list[ProductoBusquedaOut] = []
        for variante in variantes:
            producto = productos.get(variante.producto_id)
            if producto is None:
                continue
            precio = precios[producto.id]
            salida.append(
                ProductoBusquedaOut(
                    producto_variante_id=variante.id,
                    producto=ProductoResumen(
                        id=producto.id, nombre=producto.nombre, imagen_principal_url=producto.imagen_principal_url
                    ),
                    variante=VarianteResumen(
                        id=variante.id,
                        talla=TallaResumen.model_validate(variante.talla),
                        color=ColorResumen.model_validate(variante.color),
                    ),
                    precio_unitario=precio.precio_final,
                    en_promocion=precio.en_promocion,
                    porcentaje_descuento=precio.porcentaje_descuento,
                    disponible=disponible_map.get(variante.id, 0),
                )
            )
        return salida

    def crear_venta_directa(self, cajero: Usuario, datos: CrearVentaDirectaRequest) -> VentaPresencialOut:
        sucursal_id = self._sucursal_de(cajero)

        # Se suma por variante (por si el Cajero mandó la misma variante en
        # más de una línea) -- la validación de disponible y la Venta final
        # usan SIEMPRE el total requerido por variante, nunca línea por línea.
        requerido: dict[int, int] = {}
        for item in datos.items:
            requerido[item.producto_variante_id] = requerido.get(item.producto_variante_id, 0) + item.cantidad

        variantes = self._variantes.get_activas_by_ids(list(requerido.keys()))
        if len(variantes) != len(requerido):
            raise VarianteNoEncontradaError

        disponible_map = self._stock.disponible_por_variantes(sucursal_id, list(requerido.keys()))
        if not all(disponible_map.get(vid, 0) >= cantidad for vid, cantidad in requerido.items()):
            raise StockInsuficienteError

        producto_ids = {v.producto_id for v in variantes.values()}
        productos = self._productos.get_activos_by_ids(producto_ids)
        precios = obtener_precios_efectivos(self._db, list(productos.values()))

        detalles: list[VentaDetalle] = []
        total = Decimal("0")
        for variante_id, cantidad in requerido.items():
            variante = variantes[variante_id]
            producto = productos.get(variante.producto_id)
            if producto is None:
                raise VarianteNoEncontradaError
            # CU32 -- precio EFECTIVO en este instante, congelado desde ya en
            # el VentaDetalle (histórico, ver Models/venta.py).
            precio = precios[producto.id].precio_final
            subtotal = precio * cantidad
            total += subtotal
            detalles.append(
                VentaDetalle(
                    producto_variante_id=variante_id,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=subtotal,
                )
            )

        venta = Venta(
            cliente_id=None,
            cajero_id=cajero.id,
            sucursal_id=sucursal_id,
            tipo=TipoVenta.PRESENCIAL,
            estado=EstadoVenta.PENDIENTE_PAGO,
            origen=OrigenVenta.DIRECTA,
            reserva_id=None,
            total=total,
            detalles=detalles,
        )
        self._ventas.crear(venta)

        return self._venta_a_salida(venta, productos)

    def crear_venta_desde_reserva(self, cajero: Usuario, reserva_id: int) -> VentaPresencialOut:
        sucursal_id = self._sucursal_de(cajero)

        reserva = self._reservas.obtener_por_id(reserva_id)
        if reserva is None:
            raise ReservaNoEncontradaError
        if reserva.sucursal_id != sucursal_id:
            raise ReservaOtraSucursalError

        existente = self._ventas.obtener_pendiente_por_reserva(reserva_id)
        if existente is not None:
            producto_ids = {d.producto_variante.producto_id for d in existente.detalles}
            productos = self._productos.get_activos_by_ids(producto_ids)
            return self._venta_a_salida(existente, productos, reserva=reserva)

        # SOLO las prendas que CU20 marcó "para caja" -- nunca las que el
        # Cliente decidió no comprar, ni las canceladas/vencidas.
        detalles_para_caja = [d for d in reserva.detalles if d.estado == EstadoReserva.LISTA_PARA_CAJA]
        if not detalles_para_caja:
            raise ReservaSinPrendasParaCajaError

        producto_ids = {d.producto_variante.producto_id for d in detalles_para_caja}
        productos = self._productos.get_activos_by_ids(producto_ids)
        precios = obtener_precios_efectivos(self._db, list(productos.values()))

        detalles_venta: list[VentaDetalle] = []
        total = Decimal("0")
        for detalle in detalles_para_caja:
            variante = detalle.producto_variante
            producto = productos.get(variante.producto_id)
            if producto is None:
                # Producto desactivado después de reservarse -- se omite,
                # mismo criterio ya usado por CU21/CU22/CU23.
                continue
            # CU32 -- precio EFECTIVO en este instante (la Reserva, CU17,
            # nunca guardó ningún precio), congelado desde ya en el
            # VentaDetalle.
            precio = precios[producto.id].precio_final
            subtotal = precio * detalle.cantidad
            total += subtotal
            detalles_venta.append(
                VentaDetalle(
                    producto_variante_id=variante.id,
                    cantidad=detalle.cantidad,
                    precio_unitario=precio,
                    subtotal=subtotal,
                )
            )

        if not detalles_venta:
            raise ReservaSinPrendasParaCajaError

        venta = Venta(
            cliente_id=reserva.cliente_id,
            cajero_id=cajero.id,
            sucursal_id=sucursal_id,
            tipo=TipoVenta.PRESENCIAL,
            estado=EstadoVenta.PENDIENTE_PAGO,
            origen=OrigenVenta.RESERVA,
            reserva_id=reserva.id,
            total=total,
            detalles=detalles_venta,
        )
        self._ventas.crear(venta)

        return self._venta_a_salida(venta, productos, reserva=reserva)

    def _venta_a_salida(
        self, venta: Venta, productos: dict[int, Producto], reserva: Reserva | None = None
    ) -> VentaPresencialOut:
        detalles_out: list[VentaDetalleOut] = []
        for detalle in venta.detalles:
            variante = detalle.producto_variante
            producto = productos.get(variante.producto_id)
            if producto is None:
                continue
            detalles_out.append(
                VentaDetalleOut(
                    producto=ProductoResumen(
                        id=producto.id, nombre=producto.nombre, imagen_principal_url=producto.imagen_principal_url
                    ),
                    variante=VarianteResumen(
                        id=variante.id,
                        talla=TallaResumen.model_validate(variante.talla),
                        color=ColorResumen.model_validate(variante.color),
                    ),
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    subtotal=detalle.subtotal,
                )
            )

        reserva_out = None
        if reserva is not None:
            cliente = self._usuarios.get_by_id(reserva.cliente_id) if reserva.cliente_id else None
            reserva_out = ReservaResumenOut(
                codigo_reserva=reserva.codigo_reserva,
                cliente_nombre=cliente.nombre if cliente is not None else "Cliente",
            )

        return VentaPresencialOut(
            id=venta.id,
            codigo_venta=venta.codigo_venta,
            tipo=venta.tipo.value,
            estado=venta.estado.value,
            origen=venta.origen.value if venta.origen is not None else OrigenVenta.DIRECTA.value,
            total=venta.total,
            fecha_creacion=venta.fecha_creacion,
            reserva=reserva_out,
            detalles=detalles_out,
        )
