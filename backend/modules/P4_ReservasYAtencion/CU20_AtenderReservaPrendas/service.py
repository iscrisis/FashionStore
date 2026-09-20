"""Reglas de negocio de CU20 -- Atender reserva de prendas (Encargado).

sucursal_id llega SIEMPRE ya resuelto desde el usuario autenticado (ver
router.py) -- nunca desde un id que Angular pueda manipular: un Encargado
solo consulta y atiende reservas de SU propia sucursal (la sucursal vive en
la CABECERA -- Reserva.sucursal_id -- todos los detalles de una reserva
comparten sucursal y bloque horario, ver Models/reserva.py).

Dos niveles de acción, NUNCA mezclados (quien llega a la sucursal es la
persona, no cada prenda por separado):

  A NIVEL RESERVA/CABECERA:
    - confirmar_llegada_reserva: UN solo botón por reserva. PENDIENTE|
      PREPARADA -> EN_ATENCION. NO toca el estado de ningún detalle (cada
      prenda conserva el suyo -- puede seguir PREPARADA, o incluso
      PENDIENTE si el Encargado no llegó a prepararla).
    - finalizar_atencion: UN solo botón por reserva, habilitado recién
      cuando NINGÚN detalle activo sigue PENDIENTE/PREPARADA (todos ya
      tienen una decisión: LISTA_PARA_CAJA o "no la compra"). Es el único
      punto que libera stock_reservado de las prendas no compradas y decide
      el estado final de la cabecera (LISTA_PARA_CAJA si al menos una
      prenda va a caja, ATENDIDA si ninguna).

  A NIVEL DETALLE/PRENDA:
    - preparar: PENDIENTE -> PREPARADA, individual.
    - decidir_no_comprar / decidir_enviar_a_caja: solo con la reserva ya
      EN_ATENCION y el detalle PREPARADA -- registran la DECISIÓN del
      Encargado (estado -> ATENDIDA o LISTA_PARA_CAJA) pero es una decisión
      TODAVÍA REVERSIBLE en el sentido de que no le suelta el stock ni
      afecta al Cajero hasta que finalizar_atencion la confirme: mientras el
      Encargado sigue resolviendo el resto de la reserva, ninguna prenda
      individual debe llegarle todavía al Cajero (ver
      listar_pendientes_cajero) ni liberar stock_reservado (ver
      finalizar_atencion).

`estado_general` de la cabecera deja de ser un cálculo puramente derivado de
sus detalles (Models/reserva.py:calcular_estado_general) en cuanto pasa a
EN_ATENCION: desde ahí en adelante lo gobiernan EXCLUSIVAMENTE las
transiciones explícitas de este módulo (confirmar_llegada_reserva,
finalizar_atencion) -- por eso preparar() y expirar_vencidas() solo
recalculan mientras estado_general sigue en ESTADOS_VENCIBLES (PENDIENTE/
PREPARADA, la fase previa a la llegada); de lo contrario un detalle
preparado o vencido después de la llegada podría "regresar" la cabecera a un
estado anterior, pisando la llegada ya confirmada.

Ninguna acción de este módulo toca StockSucursal.cantidad (el físico).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva, Reserva, ReservaDetalle

from .repository import (
    ClienteLecturaRepository,
    ProductoLecturaRepository,
    ReservaDetalleRepository,
    ReservaRepository,
    StockSucursalRepository,
)
from .schemas import (
    ClienteResumen,
    ColorResumen,
    ProductoResumen,
    ReservaDetallePanelOut,
    ReservaPanelOut,
    TallaResumen,
    VarianteResumen,
)

# Estados desde los que una reserva/detalle puede vencer -- ver
# expirar_vencidas. También es, exactamente, la fase "previa a la llegada":
# mientras la cabecera está en uno de estos dos estados, estado_general
# sigue gobernado por el cálculo agregado (Models/reserva.py); desde
# EN_ATENCION en adelante el Cliente ya llegó (o el proceso ya terminó) y
# nunca vence ni se recalcula solo, gobiernan las transiciones explícitas de
# este módulo.
ESTADOS_VENCIBLES = (EstadoReserva.PENDIENTE, EstadoReserva.PREPARADA)

# Un detalle "resuelto" (ya tiene una decisión del Encargado, o ya fue
# cancelado por el Cliente vía CU19) no bloquea finalizar_atencion.
_ESTADOS_SIN_DECISION = (EstadoReserva.PENDIENTE, EstadoReserva.PREPARADA)

# Los únicos dos estados cuyo stock_reservado YA se liberó por su propio
# camino antes de llegar a finalizar_atencion (CU19 -- cancelar_detalle/
# cancelar_reserva -- y expirar_vencidas, respectivamente) -- ver
# finalizar_atencion, que libera el de cualquier otro estado (defensivo).
_ESTADOS_YA_LIBERADOS = (EstadoReserva.CANCELADA, EstadoReserva.VENCIDA)


class ReservaNoEncontradaError(Exception):
    """No existe, o no pertenece a la sucursal del Encargado autenticado
    (mismo mensaje: no revela reservas de otras sucursales)."""


class TransicionInvalidaError(Exception):
    """La reserva o el detalle no está en un estado desde el que se pueda
    realizar esta acción."""


class ReservaVencidaError(Exception):
    """La reserva ya venció (el bloque horario terminó sin que el Cliente
    llegara) justo en este intento -- se marcó VENCIDA y liberó el stock de
    sus detalles activos; la acción original ya no aplica."""


class DecisionesPendientesError(Exception):
    """finalizar_atencion: todavía hay algún detalle activo (ni cancelado)
    sin decisión (PENDIENTE o PREPARADA) -- primero hay que resolver
    "no la compra"/"enviar a caja" para cada prenda."""


def _fin_de_bloque(reserva: Reserva) -> datetime:
    return datetime.combine(
        reserva.fecha_reserva, reserva.hora_inicio, tzinfo=timezone.utc
    ) + timedelta(hours=1)


def expirar_vencidas(db: Session, reservas: list[Reserva]) -> None:
    """Comprobación reactiva de CU20: cualquier detalle PENDIENTE o
    PREPARADA de una reserva CUYA CABECERA TODAVÍA esté en esa misma fase
    (ESTADOS_VENCIBLES) y cuyo bloque horario ya haya terminado pasa a
    VENCIDA y libera su stock_reservado; la cabecera recalcula su
    `estado_general` (sigue siendo seguro: solo se llega aquí si la cabecera
    todavía estaba en fase previa a la llegada). La llama tanto
    `listar_panel` (más abajo) como CU17_CrearReservaPrendas.listar_mias
    (CU18) -- es la ÚNICA función que CU17 importa desde CU20, para que
    "Mis reservas" del Cliente nunca muestre como activa una reserva que ya
    venció.

    IMPORTANTE: se filtra por el estado de la CABECERA, no solo del
    detalle -- una prenda puede seguir PREPARADA (sin decisión todavía)
    mientras la reserva YA está EN_ATENCION (el Cliente llegó y el
    Encargado sigue resolviendo el resto); esa prenda NUNCA debe vencer,
    aunque su propio `estado` siga siendo, nominalmente, uno "vencible".

    Re-bloquea cada detalle candidato (y su cabecera) con SELECT ... FOR
    UPDATE antes de mutarlo, aunque `reservas` venga de una lectura sin
    lock -- dos llamadas concurrentes nunca liberan el mismo stock_reservado
    dos veces: la segunda relee bajo lock y encuentra el estado ya cambiado.
    """
    ahora = datetime.now(timezone.utc)
    candidatos = [
        detalle
        for reserva in reservas
        for detalle in reserva.detalles
        if reserva.estado_general in ESTADOS_VENCIBLES
        and detalle.estado in ESTADOS_VENCIBLES
        and ahora >= _fin_de_bloque(reserva)
    ]
    if not candidatos:
        return

    detalle_repo = ReservaDetalleRepository(db)
    reserva_repo = ReservaRepository(db)
    stock_repo = StockSucursalRepository(db)
    hubo_cambios = False

    for candidato in candidatos:
        detalle = detalle_repo.bloquear_por_id(candidato.id)
        if detalle is None or detalle.estado not in ESTADOS_VENCIBLES:
            continue
        cabecera = detalle.reserva
        if cabecera.estado_general not in ESTADOS_VENCIBLES or ahora < _fin_de_bloque(cabecera):
            continue
        stock = stock_repo.bloquear_para_liberar(cabecera.sucursal_id, detalle.producto_variante_id)
        if stock is not None:
            stock.stock_reservado = max(0, stock.stock_reservado - detalle.cantidad)
        detalle.estado = EstadoReserva.VENCIDA
        hubo_cambios = True

        cabecera_bloqueada = reserva_repo.bloquear_por_id(cabecera.id)
        if cabecera_bloqueada.estado_general in ESTADOS_VENCIBLES:
            cabecera_bloqueada.recalcular_estado_general()

    if hubo_cambios:
        db.commit()


class AtenderReservaService:
    def __init__(self, db: Session):
        self._db = db
        self._reservas = ReservaRepository(db)
        self._detalles = ReservaDetalleRepository(db)
        self._productos = ProductoLecturaRepository(db)
        self._clientes = ClienteLecturaRepository(db)
        self._stock = StockSucursalRepository(db)

    def listar_panel(self, sucursal_id: int) -> list[ReservaPanelOut]:
        reservas = self._reservas.listar_por_sucursal(sucursal_id)
        expirar_vencidas(self._db, reservas)
        return [self._reserva_a_salida(reserva) for reserva in reservas]

    def listar_pendientes_cajero(self, sucursal_id: int) -> list[ReservaPanelOut]:
        """Integración mínima de CU20 con el rol Cajero -- "Reservas
        pendientes de atención": SOLO cabeceras cuyo estado_general YA es
        LISTA_PARA_CAJA (es decir, el Encargado ya presionó "Finalizar
        atención" y decidió que al menos una prenda va a caja), de SU
        sucursal. Una reserva EN_ATENCION nunca aparece aquí, aunque alguna
        de sus prendas ya tenga la decisión LISTA_PARA_CAJA tomada -- el
        Cajero solo debe ver la selección FINAL y completa, nunca prenda por
        prenda mientras el Encargado sigue resolviendo el resto (ver
        finalizar_atencion). Dentro de cada cabecera, `detalles` se filtra a
        solo las prendas LISTA_PARA_CAJA -- las que el Cliente no quiso
        (ATENDIDA) no se muestran. No hay nada que vencer aquí: LISTA_PARA_CAJA
        nunca vence (ver ESTADOS_VENCIBLES)."""
        reservas = self._reservas.listar_por_sucursal_y_estado_general(sucursal_id, EstadoReserva.LISTA_PARA_CAJA)
        salidas = []
        for reserva in reservas:
            salida = self._reserva_a_salida(reserva)
            salida.detalles = [d for d in salida.detalles if d.estado == "LISTA_PARA_CAJA"]
            salidas.append(salida)
        return salidas

    def preparar(self, sucursal_id: int, detalle_id: int) -> ReservaDetallePanelOut:
        """PENDIENTE -> PREPARADA. NO modifica stock. Individual: no afecta
        a las demás prendas de la misma reserva."""
        detalle = self._obtener_detalle_de_mi_sucursal(sucursal_id, detalle_id)
        self._expirar_si_corresponde_o_fallar(detalle)
        if detalle.estado != EstadoReserva.PENDIENTE:
            raise TransicionInvalidaError
        detalle.estado = EstadoReserva.PREPARADA
        return self._confirmar_detalle(detalle)

    def confirmar_llegada_reserva(self, sucursal_id: int, reserva_id: int) -> ReservaPanelOut:
        """PENDIENTE|PREPARADA -> EN_ATENCION, a nivel de CABECERA -- un solo
        botón por reserva. NO modifica stock. NO cambia el `estado`
        individual de ningún detalle: cada prenda conserva exactamente el
        que tenía (PREPARADA, o incluso PENDIENTE si no se llegó a preparar)
        -- la llegada es del Cliente, no de cada prenda."""
        cabecera = self._obtener_cabecera_de_mi_sucursal(sucursal_id, reserva_id)
        self._expirar_cabecera_si_corresponde_o_fallar(cabecera)
        if cabecera.estado_general not in (EstadoReserva.PENDIENTE, EstadoReserva.PREPARADA):
            raise TransicionInvalidaError
        cabecera.estado_general = EstadoReserva.EN_ATENCION
        self._reservas.guardar()
        self._reservas.refrescar(cabecera)
        return self._reserva_a_salida(cabecera)

    def decidir_no_comprar(self, sucursal_id: int, detalle_id: int) -> ReservaDetallePanelOut:
        """Decisión del Encargado tras probarse la prenda: el Cliente NO la
        compra. Requiere la reserva EN_ATENCION y el detalle PREPARADA.
        Persiste la decisión (estado -> ATENDIDA) para que sobreviva un
        refresco de página, pero NO libera stock_reservado todavía -- eso
        ocurre recién en finalizar_atencion, junto con el resto de la
        reserva, para no soltar unidades mientras el Encargado sigue
        decidiendo el resto."""
        detalle = self._obtener_detalle_de_mi_sucursal(sucursal_id, detalle_id)
        if detalle.reserva.estado_general != EstadoReserva.EN_ATENCION:
            raise TransicionInvalidaError
        if detalle.estado != EstadoReserva.PREPARADA:
            raise TransicionInvalidaError
        detalle.estado = EstadoReserva.ATENDIDA
        self._db.commit()
        self._db.refresh(detalle)
        return self._detalle_a_salida(detalle)

    def decidir_enviar_a_caja(self, sucursal_id: int, detalle_id: int) -> ReservaDetallePanelOut:
        """Decisión del Encargado: el Cliente SÍ se lleva esta prenda.
        Requiere la reserva EN_ATENCION y el detalle PREPARADA. Marcador
        persistente únicamente (estado -> LISTA_PARA_CAJA): NO crea venta,
        NO crea pago, NO descuenta stock_actual, conserva stock_reservado --
        y todavía NO la muestra al Cajero (ver listar_pendientes_cajero):
        eso solo ocurre cuando finalizar_atencion cierra TODA la reserva."""
        detalle = self._obtener_detalle_de_mi_sucursal(sucursal_id, detalle_id)
        if detalle.reserva.estado_general != EstadoReserva.EN_ATENCION:
            raise TransicionInvalidaError
        if detalle.estado != EstadoReserva.PREPARADA:
            raise TransicionInvalidaError
        detalle.estado = EstadoReserva.LISTA_PARA_CAJA
        self._db.commit()
        self._db.refresh(detalle)
        return self._detalle_a_salida(detalle)

    def finalizar_atencion(self, sucursal_id: int, reserva_id: int) -> ReservaPanelOut:
        """Cierra la atención de TODA la reserva -- un solo botón, habilitado
        recién cuando ningún detalle activo sigue PENDIENTE/PREPARADA (todos
        ya tienen una decisión, o fueron cancelados por el Cliente vía
        CU19). Transaccional: en el mismo commit,
          - libera stock_reservado de cada detalle "no la compra" (ATENDIDA
            por decisión de este flujo) -- exactamente una vez, protegido
            por el FOR UPDATE de la cabecera más el propio guard de
            estado_general == EN_ATENCION (una segunda llamada ya no
            encuentra EN_ATENCION y se rechaza antes de tocar nada más);
          - conserva stock_reservado de cada detalle LISTA_PARA_CAJA (sigue
            retenida para el Cliente);
          - dejan intactos los detalles ya CANCELADA o VENCIDA (CU19/
            expirar_vencidas ya liberaron ese stock en su momento);
          - CUALQUIER otro estado (defensivo: no debería ocurrir con el flujo
            normal, pero un detalle nunca debe poder retener stock_reservado
            más allá de este punto) libera igual que ATENDIDA -- antes se
            asumía en silencio "ya se liberó por su propio camino" para todo
            lo que no fuera ATENDIDA/LISTA_PARA_CAJA, pero esa suposición
            solo es cierta para CANCELADA/VENCIDA; cualquier otro caso dejaba
            `stock_reservado` huérfano para siempre (ya no hay, después de
            finalizar, ningún otro camino -- CU19 exige PENDIENTE/PREPARADA,
            las decisiones de este módulo exigen la reserva todavía
            EN_ATENCION -- que pueda liberarlo);
          - decide el estado final de la cabecera: LISTA_PARA_CAJA si hay
            AL MENOS una prenda para caja, ATENDIDA si ninguna."""
        cabecera = self._obtener_cabecera_de_mi_sucursal(sucursal_id, reserva_id)
        if cabecera.estado_general != EstadoReserva.EN_ATENCION:
            raise TransicionInvalidaError

        if any(d.estado in _ESTADOS_SIN_DECISION for d in cabecera.detalles):
            raise DecisionesPendientesError

        hay_para_caja = False
        for detalle in cabecera.detalles:
            if detalle.estado == EstadoReserva.LISTA_PARA_CAJA:
                hay_para_caja = True
            elif detalle.estado not in _ESTADOS_YA_LIBERADOS:
                stock = self._stock.bloquear_para_liberar(cabecera.sucursal_id, detalle.producto_variante_id)
                if stock is not None:
                    stock.stock_reservado = max(0, stock.stock_reservado - detalle.cantidad)

        cabecera.estado_general = EstadoReserva.LISTA_PARA_CAJA if hay_para_caja else EstadoReserva.ATENDIDA
        self._reservas.guardar()
        self._reservas.refrescar(cabecera)
        return self._reserva_a_salida(cabecera)

    def _obtener_detalle_de_mi_sucursal(self, sucursal_id: int, detalle_id: int) -> ReservaDetalle:
        detalle = self._detalles.bloquear_por_id(detalle_id)
        if detalle is None or detalle.reserva.sucursal_id != sucursal_id:
            raise ReservaNoEncontradaError
        return detalle

    def _obtener_cabecera_de_mi_sucursal(self, sucursal_id: int, reserva_id: int) -> Reserva:
        cabecera = self._reservas.bloquear_por_id(reserva_id)
        if cabecera is None or cabecera.sucursal_id != sucursal_id:
            raise ReservaNoEncontradaError
        return cabecera

    def _expirar_si_corresponde_o_fallar(self, detalle: ReservaDetalle) -> None:
        """Se llama con el detalle YA bloqueado (bloquear_por_id) por
        preparar() -- solo re-libera si corresponde, sin volver a lockear la
        misma fila. Nunca vence si la CABECERA ya avanzó más allá de la fase
        previa a la llegada (ver expirar_vencidas)."""
        if detalle.estado not in ESTADOS_VENCIBLES:
            return
        cabecera = detalle.reserva
        if cabecera.estado_general not in ESTADOS_VENCIBLES:
            return
        if datetime.now(timezone.utc) < _fin_de_bloque(cabecera):
            return
        stock = self._stock.bloquear_para_liberar(cabecera.sucursal_id, detalle.producto_variante_id)
        if stock is not None:
            stock.stock_reservado = max(0, stock.stock_reservado - detalle.cantidad)
        detalle.estado = EstadoReserva.VENCIDA
        self._recalcular_y_guardar(detalle)
        raise ReservaVencidaError

    def _expirar_cabecera_si_corresponde_o_fallar(self, cabecera: Reserva) -> None:
        """Misma comprobación que _expirar_si_corresponde_o_fallar, pero
        para confirmar_llegada_reserva: se llama con la CABECERA ya
        bloqueada, y si el bloque ya terminó, vence TODOS sus detalles
        todavía PENDIENTE/PREPARADA (no solo uno), sin volver a lockear la
        cabecera."""
        if cabecera.estado_general not in ESTADOS_VENCIBLES:
            return
        if datetime.now(timezone.utc) < _fin_de_bloque(cabecera):
            return
        for detalle in cabecera.detalles:
            if detalle.estado not in ESTADOS_VENCIBLES:
                continue
            stock = self._stock.bloquear_para_liberar(cabecera.sucursal_id, detalle.producto_variante_id)
            if stock is not None:
                stock.stock_reservado = max(0, stock.stock_reservado - detalle.cantidad)
            detalle.estado = EstadoReserva.VENCIDA
        cabecera.recalcular_estado_general()
        self._reservas.guardar()
        self._reservas.refrescar(cabecera)
        raise ReservaVencidaError

    def _confirmar_detalle(self, detalle: ReservaDetalle) -> ReservaDetallePanelOut:
        self._recalcular_y_guardar(detalle)
        return self._detalle_a_salida(detalle)

    def _recalcular_y_guardar(self, detalle: ReservaDetalle) -> None:
        """Usado SOLO por preparar()/vencimiento -- ambos ocurren siempre en
        la fase previa a la llegada. Por eso solo recalcula estado_general
        si la cabecera TODAVÍA está en ESTADOS_VENCIBLES: una vez
        EN_ATENCION (o más allá), ese estado lo gobiernan exclusivamente
        confirmar_llegada_reserva/finalizar_atencion -- recalcular aquí lo
        pisaría con el resultado del agregado puro."""
        cabecera = self._reservas.bloquear_por_id(detalle.reserva_id)
        if cabecera.estado_general in ESTADOS_VENCIBLES:
            cabecera.recalcular_estado_general()
        self._reservas.guardar()
        self._db.refresh(detalle)

    def _detalle_a_salida(self, detalle: ReservaDetalle) -> ReservaDetallePanelOut:
        variante = detalle.producto_variante
        producto = self._productos.get_by_id(variante.producto_id)
        return ReservaDetallePanelOut(
            id=detalle.id,
            reserva_id=detalle.reserva_id,
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

    def _reserva_a_salida(self, reserva: Reserva) -> ReservaPanelOut:
        cliente = self._clientes.get_by_id(reserva.cliente_id)
        return ReservaPanelOut(
            id=reserva.id,
            codigo_reserva=reserva.codigo_reserva,
            cliente=ClienteResumen(id=cliente.id, nombre=cliente.nombre),
            estado_general=reserva.estado_general.value,
            fecha_reserva=reserva.fecha_reserva,
            hora_inicio=reserva.hora_inicio,
            hora_fin=_fin_de_bloque(reserva).time(),
            fecha_creacion=reserva.fecha_creacion,
            detalles=[self._detalle_a_salida(detalle) for detalle in reserva.detalles],
        )
