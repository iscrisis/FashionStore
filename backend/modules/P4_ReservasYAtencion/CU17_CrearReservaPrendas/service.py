"""Reglas de negocio de CU17 -- Crear reserva de prendas (Cliente).

cliente_id llega SIEMPRE ya resuelto desde el usuario autenticado (ver
router.py) -- nunca desde un id que el cliente pueda manipular. sucursal_id sí
es un dato que el propio Cliente elige (a diferencia de CU14/CU15/CU16, un
Cliente no tiene una sucursal propia): el backend valida que esa sucursal
exista y esté activa, pero jamás la deriva de la cuenta del actor.

crear() valida todo ANTES de escribir nada -- fecha/horario del bloque,
sucursal activa, variante activa (y su producto activo), y disponibilidad
real para esa sucursal+variante -- y recién entonces crea la Reserva
(cabecera) con UN ReservaDetalle en estado PENDIENTE (ver Models/reserva.py:
CU17 no expone todavía un carrito -- CU21, fuera de alcance -- pero ya arma
la reserva con la forma agrupada final, lista para que un CU futuro agregue
más detalles a una reserva existente sin volver a tocar este modelo). La
reserva NUNCA descuenta stock físico (`cantidad`): solo incrementa
`StockSucursal.stock_reservado` en la misma fila, para que
`cantidad - stock_reservado` (el disponible real, el mismo cálculo que usa
CU12) baje sin tocar el físico. Confirmar/cancelar/entregar cada detalle y
ajustar el stock FÍSICO en ese momento sigue siendo responsabilidad de
CU19/CU20, fuera de este alcance.

La validación de disponibilidad y el incremento de stock_reservado ocurren
sobre la MISMA fila de StockSucursal, bloqueada con SELECT ... FOR UPDATE
(ver StockSucursalRepository.bloquear_para_reservar) y confirmados en un
único commit junto con la Reserva -- así dos clientes no pueden reservar a la
vez la última unidad (el segundo espera a que el primero confirme o aborte
antes de leer el stock_reservado ya actualizado), y nunca queda un
ReservaDetalle sin su stock_reservado correspondiente ni viceversa.

Reglas de fecha/horario (mismas constantes que Angular replica en
horario-reserva.ts para armar el tarjetero de fecha/hora del modal, pero la
autoridad real es SIEMPRE este service -- Angular/Flutter son solo la vista):
  - fecha_reserva: desde hoy hasta 7 días después, ambos inclusive.
  - horario de atención: lunes a sábado 10:00-20:00, en bloques de 1 hora
    exacta (ya validado en schemas.py) -- el último bloque posible empieza
    una hora antes del cierre. DOMINGO NO HAY ATENCIÓN: cualquier
    fecha_reserva en domingo se rechaza sin importar la hora.
  - si fecha_reserva es hoy, hora_inicio debe empezar al menos 1 hora
    después de la hora actual (UTC, mismo criterio que ya usa el resto del
    proyecto para "ahora" -- ver CU03 RecuperarContrasena).

listar_mias() (CU18) importa `expirar_vencidas` de CU20
(AtenderReservaPrendas) -- ver esa función para el detalle del vencimiento
reactivo, ahora aplicado por DETALLE (cada uno puede vencer de forma
independiente, aunque hoy todos comparten el mismo bloque horario de la
cabecera). Es la única dependencia cruzada hacia un CU posterior en todo este
archivo.
"""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P4_ReservasYAtencion.CU20_AtenderReservaPrendas.service import expirar_vencidas
from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva, Reserva, ReservaDetalle

from .repository import (
    ProductoVarianteLecturaRepository,
    ReservaRepository,
    StockSucursalRepository,
    SucursalLecturaRepository,
)
from .schemas import (
    AgregarDetalleRequest,
    ColorResumen,
    CrearReservaRequest,
    ProductoResumen,
    ReservaDetalleOut,
    ReservaOut,
    SucursalResumen,
    TallaResumen,
    VarianteResumen,
)

DIAS_MAXIMO_ANTICIPACION = 7
HORAS_MINIMAS_ANTICIPACION_HOY = 1

HORA_APERTURA = time(10, 0)
HORA_CIERRE_LUN_A_SAB = time(20, 0)
DOMINGO_WEEKDAY = 6  # date.weekday(): lunes=0 ... domingo=6


class SucursalNoEncontradaError(Exception):
    """No existe o no está activa."""


class VarianteNoEncontradaError(Exception):
    """No existe, está inactiva, o su producto está inactivo."""


class StockInsuficienteError(Exception):
    """No hay disponibilidad suficiente en StockSucursal para esa sucursal+variante."""


class FechaFueraDeRangoError(Exception):
    """fecha_reserva es anterior a hoy o posterior a hoy + 7 días."""


class HorarioInvalidoError(Exception):
    """hora_inicio cae fuera del horario de atención de ese día, o (si
    fecha_reserva es hoy) no respeta la anticipación mínima de 1 hora."""


class ReservaNoEncontradaError(Exception):
    """No existe, o no pertenece al cliente autenticado (mismo mensaje: no
    revela la existencia de reservas de otro cliente) -- ver agregar_detalle."""


class ReservaNoCompatibleError(Exception):
    """La reserva ya no admite más prendas -- solo una reserva PENDIENTE
    (ningún detalle todavía en curso ni finalizado) puede recibir un detalle
    nuevo, ver agregar_detalle."""


def _hora_fin(hora_inicio: time) -> time:
    return (datetime.combine(date.min, hora_inicio) + timedelta(hours=1)).time()


def reserva_a_salida(reserva: Reserva, productos_por_variante_id: dict[int, Producto]) -> ReservaOut:
    """Arma la cabecera + TODOS sus detalles -- `reserva.detalles` y cada
    `detalle.producto_variante` deben venir ya cargados (ver
    ReservaRepository.listar_por_cliente, selectinload) para no disparar una
    consulta por detalle."""
    detalles_out = [
        ReservaDetalleOut(
            id=detalle.id,
            producto=ProductoResumen(
                id=productos_por_variante_id[detalle.producto_variante_id].id,
                nombre=productos_por_variante_id[detalle.producto_variante_id].nombre,
                imagen_principal_url=productos_por_variante_id[detalle.producto_variante_id].imagen_principal_url,
            ),
            variante=VarianteResumen(
                id=detalle.producto_variante.id,
                talla=TallaResumen.model_validate(detalle.producto_variante.talla),
                color=ColorResumen.model_validate(detalle.producto_variante.color),
            ),
            cantidad=detalle.cantidad,
            estado=detalle.estado.value,
        )
        for detalle in reserva.detalles
        if detalle.producto_variante_id in productos_por_variante_id
    ]
    return ReservaOut(
        id=reserva.id,
        codigo_reserva=reserva.codigo_reserva,
        sucursal=SucursalResumen.model_validate(reserva.sucursal),
        estado_general=reserva.estado_general.value,
        fecha_reserva=reserva.fecha_reserva,
        hora_inicio=reserva.hora_inicio,
        hora_fin=_hora_fin(reserva.hora_inicio),
        fecha_creacion=reserva.fecha_creacion,
        detalles=detalles_out,
    )


class CrearReservaService:
    def __init__(self, db: Session):
        self._db = db
        self._sucursales = SucursalLecturaRepository(db)
        self._variantes = ProductoVarianteLecturaRepository(db)
        self._stock = StockSucursalRepository(db)
        self._reservas = ReservaRepository(db)

    def _resolver_variante(self, variante_id: int) -> tuple[Producto, ProductoVariante]:
        variante = self._variantes.get_variante_activa_by_id(variante_id)
        if variante is None:
            raise VarianteNoEncontradaError
        producto = self._variantes.get_producto_activo(variante.producto_id)
        if producto is None:
            raise VarianteNoEncontradaError
        return producto, variante

    def _validar_fecha_hora(self, fecha_reserva: date, hora_inicio: time) -> None:
        ahora = datetime.now(timezone.utc)
        hoy = ahora.date()

        if fecha_reserva < hoy or fecha_reserva > hoy + timedelta(days=DIAS_MAXIMO_ANTICIPACION):
            raise FechaFueraDeRangoError

        # Domingo no hay atención -- se rechaza cualquier horario ese día,
        # sin excepción, antes de comparar contra horas de apertura/cierre.
        if fecha_reserva.weekday() == DOMINGO_WEEKDAY:
            raise HorarioInvalidoError

        # El último bloque posible empieza una hora antes del cierre
        # (bloques de 1h ya validados en schemas.py).
        ultimo_bloque_posible = (
            datetime.combine(date.min, HORA_CIERRE_LUN_A_SAB) - timedelta(hours=1)
        ).time()
        if hora_inicio < HORA_APERTURA or hora_inicio > ultimo_bloque_posible:
            raise HorarioInvalidoError

        if fecha_reserva == hoy:
            inicio_bloque = datetime.combine(fecha_reserva, hora_inicio, tzinfo=timezone.utc)
            if inicio_bloque < ahora + timedelta(hours=HORAS_MINIMAS_ANTICIPACION_HOY):
                raise HorarioInvalidoError

    def crear(self, cliente: Usuario, datos: CrearReservaRequest) -> ReservaOut:
        self._validar_fecha_hora(datos.fecha_reserva, datos.hora_inicio)

        sucursal = self._sucursales.get_activa_by_id(datos.sucursal_id)
        if sucursal is None:
            raise SucursalNoEncontradaError

        producto, variante = self._resolver_variante(datos.producto_variante_id)

        # Bloquea la fila de stock de esta sucursal+variante para el resto de
        # la transacción -- sin este lock, dos requests concurrentes podrían
        # leer la misma última unidad disponible y ambas crear la reserva.
        stock = self._stock.bloquear_para_reservar(sucursal.id, variante.id)
        disponible = (stock.cantidad - stock.stock_reservado) if stock is not None else 0
        if datos.cantidad > disponible:
            raise StockInsuficienteError

        detalle = ReservaDetalle(
            producto_variante_id=variante.id,
            cantidad=datos.cantidad,
            estado=EstadoReserva.PENDIENTE,
        )
        reserva = Reserva(
            cliente_id=cliente.id,
            sucursal_id=sucursal.id,
            fecha_reserva=datos.fecha_reserva,
            hora_inicio=datos.hora_inicio,
            estado_general=EstadoReserva.PENDIENTE,
            detalles=[detalle],
        )
        # stock.stock_reservado (dirty en esta misma Session) y la Reserva
        # nueva (con su detalle, por cascada) se confirman en un único commit
        # (ver ReservaRepository.crear) -- nunca puede quedar uno sin el otro.
        stock.stock_reservado += datos.cantidad
        self._reservas.crear(reserva)

        return reserva_a_salida(reserva, {variante.id: producto})

    def _productos_por_variante(self, reservas: list[Reserva]) -> dict[int, Producto]:
        """Cache de Producto por producto_variante_id sobre TODOS los
        detalles de `reservas`, para armar cada ReservaOut sin una consulta
        de Producto por detalle -- reutilizado por listar_mias y
        listar_compatibles."""
        productos_cache: dict[int, Producto | None] = {}
        productos_por_variante: dict[int, Producto] = {}
        for reserva in reservas:
            for detalle in reserva.detalles:
                variante = detalle.producto_variante
                producto_id = variante.producto_id
                if producto_id not in productos_cache:
                    productos_cache[producto_id] = self._variantes.get_producto_activo(producto_id)
                producto = productos_cache[producto_id]
                if producto is not None:
                    productos_por_variante[variante.id] = producto
        return productos_por_variante

    def listar_mias(self, cliente_id: int) -> list[ReservaOut]:
        reservas = self._reservas.listar_por_cliente(cliente_id)

        # Integración mínima con CU20 (Atender reserva de prendas): antes de
        # responder, cualquier detalle PENDIENTE/PREPARADA de ESTE cliente
        # cuyo bloque horario ya haya terminado pasa a VENCIDA (y libera su
        # stock_reservado, y recalcula estado_general de su cabecera) -- así
        # "Mis reservas" nunca muestra como activa una reserva que ya venció.
        # Es la única función que se importa desde CU20 (ver
        # CU20_AtenderReservaPrendas/__init__.py); no se duplica ni se mueve
        # nada de ese módulo.
        expirar_vencidas(self._db, reservas)

        productos_por_variante = self._productos_por_variante(reservas)

        return [
            reserva_a_salida(reserva, productos_por_variante)
            for reserva in reservas
            # Una reserva cuyo único producto ya fue desactivado no tiene
            # nada que mostrar -- mismo criterio que ya aplicaba la versión
            # anterior (una fila = una prenda): se omite en vez de mostrar
            # un detalle "roto" sin nombre ni imagen.
            if any(d.producto_variante_id in productos_por_variante for d in reserva.detalles)
        ]

    def listar_compatibles(self, cliente_id: int, sucursal_id: int) -> list[ReservaOut]:
        """Reservas del Cliente en `sucursal_id` a las que HOY se les podría
        agregar una prenda más -- solo estado_general PENDIENTE (ver
        agregar_detalle: ninguna prenda de la reserva empezó a atenderse
        todavía). Corre expirar_vencidas ANTES de filtrar, mismo criterio
        que listar_mias, para no ofrecer como "compatible" una reserva cuyo
        bloque horario ya venció pero el estado en la base todavía no se
        había actualizado."""
        reservas = self._reservas.listar_por_cliente_y_sucursal(cliente_id, sucursal_id)
        expirar_vencidas(self._db, reservas)

        pendientes = [r for r in reservas if r.estado_general == EstadoReserva.PENDIENTE]
        productos_por_variante = self._productos_por_variante(pendientes)

        return [
            reserva_a_salida(reserva, productos_por_variante)
            for reserva in pendientes
            if any(d.producto_variante_id in productos_por_variante for d in reserva.detalles)
        ]

    def agregar_detalle(self, cliente: Usuario, reserva_id: int, datos: AgregarDetalleRequest) -> ReservaOut:
        """Agrega UNA prenda a una reserva PENDIENTE ya existente -- NUNCA
        crea una cabecera nueva (ver Models/reserva.py). Si esa misma
        variante YA está en la reserva como un detalle todavía PENDIENTE, se
        fusiona incrementando su `cantidad` en vez de insertar una fila
        duplicada (evita duplicaciones accidentales, p. ej. un doble clic) --
        un detalle CANCELADA para esa misma variante no cuenta para la
        fusión, se agrega uno nuevo.

        Mismo orden de locks y misma validación de disponibilidad
        (`stock_actual - stock_reservado`) que crear(): se bloquea primero la
        cabecera (para leer estado_general de forma segura) y después la
        fila de StockSucursal, todo en una única transacción."""
        cabecera = self._reservas.bloquear_por_id(reserva_id)
        if cabecera is None or cabecera.cliente_id != cliente.id:
            raise ReservaNoEncontradaError
        if cabecera.estado_general != EstadoReserva.PENDIENTE:
            raise ReservaNoCompatibleError

        producto, variante = self._resolver_variante(datos.producto_variante_id)

        stock = self._stock.bloquear_para_reservar(cabecera.sucursal_id, variante.id)
        disponible = (stock.cantidad - stock.stock_reservado) if stock is not None else 0
        if datos.cantidad > disponible:
            raise StockInsuficienteError

        existente = next(
            (
                detalle
                for detalle in cabecera.detalles
                if detalle.producto_variante_id == variante.id and detalle.estado == EstadoReserva.PENDIENTE
            ),
            None,
        )
        if existente is not None:
            existente.cantidad += datos.cantidad
        else:
            cabecera.detalles.append(
                ReservaDetalle(
                    producto_variante_id=variante.id,
                    cantidad=datos.cantidad,
                    estado=EstadoReserva.PENDIENTE,
                )
            )
        stock.stock_reservado += datos.cantidad
        cabecera.recalcular_estado_general()

        self._reservas.guardar()
        self._reservas.refrescar(cabecera)

        productos_por_variante = self._productos_por_variante([cabecera])
        return reserva_a_salida(cabecera, productos_por_variante)
