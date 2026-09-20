"""Reglas de negocio de CU21 -- Usar carrito de compras (Cliente).

cliente_id llega SIEMPRE ya resuelto desde el usuario autenticado (ver
router.py) -- nunca desde un id que el cliente pueda manipular: un Cliente
jamás puede consultar, modificar ni eliminar el carrito de otro.

El carrito es SOLO intención de compra digital -- ver Models/carrito.py.
Ninguna operación de este módulo:
  - crea Reserva, Venta ni Pago;
  - modifica StockSucursal.cantidad (el físico) NI StockSucursal.stock_reservado.
`StockSucursalRepository.alguna_sucursal_activa_cubre` es una consulta PURA
(sin FOR UPDATE): agregar al carrito valida que la cantidad pedida sea
técnicamente atendible por AL MENOS UNA sucursal activa, pero no bloquea ni
compromete esa unidad para nadie -- el carrito puede quedar guardado días sin
garantía de que el stock siga existiendo; esa validación final (contra la
sucursal que el Cliente elija) es responsabilidad de un CU posterior, fuera
de este alcance.

agregar_item bloquea PRIMERO el Carrito completo (SELECT ... FOR UPDATE,
ver CarritoRepository.bloquear_por_cliente) antes de leer/mutar su colección
de items -- así dos requests concurrentes del mismo Cliente (doble clic,
reintento de red) para la MISMA variante nunca pisan el conteo de unidades
que usa la validación de stock: la segunda espera a que la primera confirme
y relee la colección ya actualizada antes de decidir si agrega su propia
unidad.

Cada llamada a agregar_item crea SIEMPRE una fila nueva (una unidad) -- ya
no existe una UniqueConstraint por variante que fusione cantidades: agregar
la misma variante dos veces es, a propósito, dos CarritoItem independientes,
cada uno con su propio `seleccionado`.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P5_ComprasVentasYPagos.Models.carrito import Carrito, CarritoItem
from modules.P6_InnovacionYAnalisis.CU32_GestionarPromociones.precio_efectivo import obtener_precios_efectivos

from .repository import (
    CarritoRepository,
    ProductoLecturaRepository,
    ProductoVarianteLecturaRepository,
    StockSucursalRepository,
)
from .schemas import (
    ActualizarSeleccionRequest,
    AgregarItemRequest,
    CarritoItemOut,
    CarritoOut,
    ColorResumen,
    ProductoResumen,
    TallaResumen,
    VarianteResumen,
)


class VarianteNoEncontradaError(Exception):
    """No existe, está inactiva, o su producto está inactivo."""


class StockInsuficienteError(Exception):
    """Ninguna sucursal activa puede atender actualmente esa cantidad."""


class ItemNoEncontradoError(Exception):
    """No existe, o no pertenece al carrito del cliente autenticado (mismo
    mensaje: no revela la existencia de items de otro cliente)."""


class CarritoService:
    def __init__(self, db: Session):
        self._db = db
        self._carritos = CarritoRepository(db)
        self._variantes = ProductoVarianteLecturaRepository(db)
        self._productos = ProductoLecturaRepository(db)
        self._stock = StockSucursalRepository(db)

    def consultar(self, cliente_id: int) -> CarritoOut:
        carrito = self._obtener_o_crear(cliente_id)
        return self._a_salida(carrito)

    def agregar_item(self, cliente_id: int, datos: AgregarItemRequest) -> CarritoOut:
        producto, variante_id = self._resolver_variante(datos.producto_variante_id)

        carrito = self._obtener_o_crear_bloqueado(cliente_id)
        unidades_existentes = sum(1 for i in carrito.items if i.producto_variante_id == variante_id)

        if not self._stock.alguna_sucursal_activa_cubre(variante_id, unidades_existentes + 1):
            raise StockInsuficienteError

        carrito.items.append(CarritoItem(producto_variante_id=variante_id, seleccionado=True))
        carrito.fecha_actualizacion = _ahora()

        self._carritos.guardar()
        self._carritos.refrescar(carrito)
        return self._a_salida(carrito)

    def actualizar_seleccion(
        self, cliente_id: int, item_id: int, datos: ActualizarSeleccionRequest
    ) -> CarritoOut:
        # Bloquea el CARRITO primero (nunca el item por separado) -- mismo
        # orden que agregar_item, a propósito: si cada operación lockeara en
        # un orden distinto, dos mutaciones concurrentes sobre el mismo
        # carrito podrían interbloquearse. Con el carrito ya bloqueado, la
        # colección de items (selectinload) queda consistente sin necesitar
        # un lock aparte por fila.
        carrito = self._obtener_o_crear_bloqueado(cliente_id)
        item = next((i for i in carrito.items if i.id == item_id), None)
        if item is None:
            raise ItemNoEncontradoError

        item.seleccionado = datos.seleccionado
        carrito.fecha_actualizacion = _ahora()
        self._carritos.guardar()
        self._carritos.refrescar(carrito)
        return self._a_salida(carrito)

    def eliminar_item(self, cliente_id: int, item_id: int) -> CarritoOut:
        carrito = self._obtener_o_crear_bloqueado(cliente_id)
        item = next((i for i in carrito.items if i.id == item_id), None)
        if item is None:
            raise ItemNoEncontradoError

        carrito.items.remove(item)
        carrito.fecha_actualizacion = _ahora()
        self._carritos.guardar()
        self._carritos.refrescar(carrito)
        return self._a_salida(carrito)

    def _resolver_variante(self, variante_id: int) -> tuple[Producto, int]:
        variante = self._variantes.get_variante_activa_by_id(variante_id)
        if variante is None:
            raise VarianteNoEncontradaError
        producto = self._productos.get_producto_activo(variante.producto_id)
        if producto is None:
            raise VarianteNoEncontradaError
        return producto, variante.id

    def _obtener_o_crear(self, cliente_id: int) -> Carrito:
        carrito = self._carritos.bloquear_por_cliente(cliente_id)
        if carrito is not None:
            return carrito
        return self._crear_sin_lock(cliente_id)

    def _obtener_o_crear_bloqueado(self, cliente_id: int) -> Carrito:
        """Igual que _obtener_o_crear, pero garantiza que la fila devuelta
        esté bloqueada (FOR UPDATE) -- crear() hace su propio commit (libera
        cualquier lock previo), así que relockea después de crear."""
        carrito = self._carritos.bloquear_por_cliente(cliente_id)
        if carrito is not None:
            return carrito
        self._crear_sin_lock(cliente_id)
        carrito = self._carritos.bloquear_por_cliente(cliente_id)
        assert carrito is not None
        return carrito

    def _crear_sin_lock(self, cliente_id: int) -> Carrito:
        """INSERT del carrito nuevo -- si otra transacción concurrente ya lo
        creó entre el SELECT y este INSERT (dos primeros "agregar" casi
        simultáneos del mismo Cliente, ej. dos pestañas), la UniqueConstraint
        de cliente_id rechaza este segundo INSERT: se descarta y se relee el
        que ya quedó creado, en vez de fallar la request."""
        try:
            return self._carritos.crear(cliente_id)
        except IntegrityError:
            self._db.rollback()
            carrito = self._carritos.bloquear_por_cliente(cliente_id)
            assert carrito is not None
            return carrito

    def _a_salida(self, carrito: Carrito) -> CarritoOut:
        # UNA sola consulta para todos los productos del carrito (antes era
        # una consulta por item) -- con varias unidades en el carrito, la
        # respuesta de GET /carrito (imagen, nombre, precio de cada una) ya
        # no depende de N idas y vueltas a la base.
        producto_ids = {item.producto_variante.producto_id for item in carrito.items}
        productos = self._productos.get_activos_by_ids(producto_ids)
        precios = obtener_precios_efectivos(self._db, list(productos.values()))

        items_out: list[CarritoItemOut] = []
        subtotal_seleccionado = Decimal("0")
        for item in carrito.items:
            variante = item.producto_variante
            producto = productos.get(variante.producto_id)
            if producto is None:
                # No existe, o se desactivó después de agregarse -- se omite
                # en vez de mostrar una línea "rota" sin nombre ni precio
                # (mismo criterio ya usado por CU17/CU18 para reservas).
                continue
            precio = precios[producto.id]
            if item.seleccionado:
                subtotal_seleccionado += precio.precio_final
            items_out.append(
                CarritoItemOut(
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
                    seleccionado=item.seleccionado,
                )
            )
        return CarritoOut(
            items=items_out,
            subtotal_seleccionado=subtotal_seleccionado,
            fecha_actualizacion=carrito.fecha_actualizacion,
        )


def _ahora() -> datetime:
    return datetime.now(timezone.utc)
