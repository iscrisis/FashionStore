"""Reglas de negocio de CU22 -- Realizar compra digital (Cliente).

cliente_id llega SIEMPRE ya resuelto desde el usuario autenticado (ver
router.py) -- nunca desde un id que el cliente pueda manipular. Los items de
la compra NUNCA se reciben como una lista de ids desde Angular: se leen
SIEMPRE de `seleccionado=True` en el carrito PROPIO del cliente autenticado
(ver CU21_UsarCarritoCompras/Models/carrito.py) -- así un Cliente no puede
usar, ni siquiera intentando, items del carrito de otro: no hay ningún
parámetro con el que hacerlo.

Flujo (mismos 3 pasos que describe el requerimiento del Cliente):
  1. resumen(): arma "FINALIZAR COMPRA" -- SOLO las líneas seleccionadas del
     carrito, con precio ACTUAL de cada producto y el total.
  2. sucursales_disponibles(): dado un ciudad_id, lista las sucursales
     activas de esa ciudad marcando cuáles pueden cubrir TODA la compra
     (todas las variantes + cantidades seleccionadas a la vez, nunca reparte
     una compra entre varias sucursales) -- `disponible = cantidad -
     stock_reservado` por variante, igual que CU12/CU17.
  3. confirmar(): vuelve a leer el carrito y a validar disponibilidad DESDE
     CERO (nunca confía en precios, totales ni disponibilidad que haya
     mostrado antes al Cliente) y recién ahí crea la Venta (PENDIENTE_PAGO)
     + un VentaDetalle por cada línea, con el precio de ESE momento grabado
     en el detalle.

Ninguna operación de este módulo:
  - modifica StockSucursal.cantidad (el físico) NI StockSucursal.stock_reservado
    -- CU22 únicamente VALIDA disponibilidad, nunca reserva ni descuenta
    stock por una compra PENDIENTE_PAGO (eso, si corresponde, es de CU23);
  - elimina ni modifica ningún CarritoItem -- los items comprados (y los NO
    seleccionados) siguen intactos en el carrito; retirarlos del carrito es
    decisión de CU23, fuera de este alcance;
  - reparte una misma compra entre varias sucursales -- una Venta usa
    exactamente UNA sucursal para todas sus líneas;
  - implementa envío a domicilio/delivery, pago, Stripe, ni CU23-CU27.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P5_ComprasVentasYPagos.Models.carrito import CarritoItem
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta, TipoVenta, Venta, VentaDetalle
from modules.P6_InnovacionYAnalisis.CU32_GestionarPromociones.precio_efectivo import obtener_precios_efectivos

from .repository import (
    CarritoLecturaRepository,
    ProductoLecturaRepository,
    StockSucursalRepository,
    SucursalLecturaRepository,
    VentaRepository,
)
from .schemas import (
    ColorResumen,
    LineaCompraOut,
    ProductoResumen,
    ResumenCompraOut,
    SucursalCompraOut,
    SucursalVentaOut,
    TallaResumen,
    VarianteResumen,
    VentaDetalleOut,
    VentaOut,
)


class SinItemsSeleccionadosError(Exception):
    """El carrito del cliente no tiene ningún item con `seleccionado=True`."""


class SucursalNoEncontradaError(Exception):
    """No existe o no está activa."""


class SucursalNoDisponibleError(Exception):
    """La sucursal elegida ya no puede cubrir TODAS las variantes/cantidades
    seleccionadas (puede haber cambiado desde que se armó la lista)."""


class ProductoNoDisponibleError(Exception):
    """Uno de los productos seleccionados se desactivó justo antes de
    confirmar -- se rechaza toda la compra en vez de crearla incompleta."""


class CompraDigitalService:
    def __init__(self, db: Session):
        self._db = db
        self._carritos = CarritoLecturaRepository(db)
        self._productos = ProductoLecturaRepository(db)
        self._sucursales = SucursalLecturaRepository(db)
        self._stock = StockSucursalRepository(db)
        self._ventas = VentaRepository(db)

    def _items_seleccionados(self, cliente_id: int) -> list[CarritoItem]:
        carrito = self._carritos.obtener_por_cliente(cliente_id)
        if carrito is None:
            return []
        return [item for item in carrito.items if item.seleccionado]

    @staticmethod
    def _requerido_por_variante(items: list[CarritoItem]) -> dict[int, int]:
        """{producto_variante_id: unidades requeridas} -- normalmente 1 por
        item (cada CarritoItem YA es una unidad concreta, ver CU21), pero se
        suma por si dos items seleccionados son la MISMA variante (dos
        unidades independientes agregadas por separado en CU21): una
        sucursal debe cubrir el total de unidades pedidas de esa variante,
        no solo 1."""
        requerido: dict[int, int] = {}
        for item in items:
            requerido[item.producto_variante_id] = requerido.get(item.producto_variante_id, 0) + 1
        return requerido

    def resumen(self, cliente_id: int) -> ResumenCompraOut:
        items = self._items_seleccionados(cliente_id)
        if not items:
            raise SinItemsSeleccionadosError

        producto_ids = {item.producto_variante.producto_id for item in items}
        productos = self._productos.get_activos_by_ids(producto_ids)
        precios = obtener_precios_efectivos(self._db, list(productos.values()))

        lineas: list[LineaCompraOut] = []
        total = Decimal("0")
        for item in items:
            variante = item.producto_variante
            producto = productos.get(variante.producto_id)
            if producto is None:
                # Producto desactivado después de agregarse al carrito -- se
                # omite en vez de mostrar una línea "rota", mismo criterio
                # que ya usa CU21 al armar su propia salida.
                continue
            precio = precios[producto.id]
            total += precio.precio_final
            lineas.append(
                LineaCompraOut(
                    item_id=item.id,
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
                    precio_base=precio.precio_base,
                    en_promocion=precio.en_promocion,
                    porcentaje_descuento=precio.porcentaje_descuento,
                )
            )
        return ResumenCompraOut(items=lineas, total=total)

    def sucursales_disponibles(self, cliente_id: int, ciudad_id: int) -> list[SucursalCompraOut]:
        items = self._items_seleccionados(cliente_id)
        if not items:
            raise SinItemsSeleccionadosError

        requerido = self._requerido_por_variante(items)
        sucursales = self._sucursales.listar_activas_por_ciudad(ciudad_id)
        mapa = self._stock.disponible_por_sucursales([s.id for s in sucursales], list(requerido.keys()))

        salida: list[SucursalCompraOut] = []
        for sucursal in sucursales:
            disponible_variante = mapa.get(sucursal.id, {})
            cubre_todo = all(disponible_variante.get(vid, 0) >= cant for vid, cant in requerido.items())
            salida.append(
                SucursalCompraOut(
                    id=sucursal.id,
                    nombre=sucursal.nombre,
                    direccion=sucursal.direccion,
                    disponible_para_compra=cubre_todo,
                )
            )
        return salida

    def confirmar(self, cliente_id: int, sucursal_id: int) -> VentaOut:
        # Se vuelve a leer TODO desde cero -- carrito, sucursal, stock y
        # precios -- nunca se confía en lo que el Cliente vio en pantallas
        # anteriores (pudieron pasar minutos/horas entre "elegir sucursal" y
        # "confirmar compra").
        items = self._items_seleccionados(cliente_id)
        if not items:
            raise SinItemsSeleccionadosError

        sucursal = self._sucursales.get_activa_by_id(sucursal_id)
        if sucursal is None:
            raise SucursalNoEncontradaError

        requerido = self._requerido_por_variante(items)
        mapa = self._stock.disponible_por_sucursales([sucursal.id], list(requerido.keys()))
        disponible_variante = mapa.get(sucursal.id, {})
        if not all(disponible_variante.get(vid, 0) >= cant for vid, cant in requerido.items()):
            raise SucursalNoDisponibleError

        producto_ids = {item.producto_variante.producto_id for item in items}
        productos = self._productos.get_activos_by_ids(producto_ids)
        precios = obtener_precios_efectivos(self._db, list(productos.values()))

        detalles: list[VentaDetalle] = []
        total = Decimal("0")
        for item in items:
            variante = item.producto_variante
            producto = productos.get(variante.producto_id)
            if producto is None:
                raise ProductoNoDisponibleError
            # CU32 -- el precio EFECTIVO (con o sin promoción ACTIVA en este
            # instante) se resuelve aquí, en el último momento antes de
            # crear el VentaDetalle, y queda HISTÓRICO desde ya: si la
            # promoción termina después, esta Venta sigue mostrando este
            # mismo precio (ver schemas.py:VentaDetalleOut).
            precio = precios[producto.id].precio_final
            total += precio
            detalles.append(
                VentaDetalle(
                    producto_variante_id=variante.id,
                    cantidad=1,
                    precio_unitario=precio,
                    subtotal=precio,
                    # CU23 (procesar pago electrónico) necesita saber, al
                    # confirmar el pago, EXACTAMENTE qué fila del carrito
                    # borrar -- ver Models/venta.py.
                    carrito_item_id=item.id,
                )
            )

        venta = Venta(
            cliente_id=cliente_id,
            sucursal_id=sucursal.id,
            tipo=TipoVenta.DIGITAL,
            estado=EstadoVenta.PENDIENTE_PAGO,
            total=total,
            detalles=detalles,
        )
        self._ventas.crear(venta)

        return self._venta_a_salida(venta, productos)

    @staticmethod
    def _venta_a_salida(venta: Venta, productos: dict[int, Producto]) -> VentaOut:
        detalles_out = [
            VentaDetalleOut(
                producto=ProductoResumen(
                    id=productos[detalle.producto_variante.producto_id].id,
                    nombre=productos[detalle.producto_variante.producto_id].nombre,
                    imagen_principal_url=productos[detalle.producto_variante.producto_id].imagen_principal_url,
                ),
                variante=VarianteResumen(
                    id=detalle.producto_variante.id,
                    talla=TallaResumen.model_validate(detalle.producto_variante.talla),
                    color=ColorResumen.model_validate(detalle.producto_variante.color),
                ),
                cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_unitario,
                subtotal=detalle.subtotal,
            )
            for detalle in venta.detalles
        ]
        return VentaOut(
            id=venta.id,
            codigo_venta=venta.codigo_venta,
            sucursal=SucursalVentaOut(
                id=venta.sucursal.id,
                nombre=venta.sucursal.nombre,
                direccion=venta.sucursal.direccion,
                ciudad=venta.sucursal.ciudad.nombre,
            ),
            tipo=venta.tipo.value,
            estado=venta.estado.value,
            total=venta.total,
            fecha_creacion=venta.fecha_creacion,
            detalles=detalles_out,
        )
