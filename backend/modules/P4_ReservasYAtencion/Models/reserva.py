"""Entidades de Reservas, propias del paquete P4 -- Reservas y atención.

Una Reserva representa la VISITA completa de un Cliente a una sucursal en un
bloque horario -- NO una prenda suelta. Puede agrupar varias prendas
(ReservaDetalle), cada una con su propio ciclo de vida independiente. Antes
de la migración que introdujo este archivo (ver
alembic/versions/*_split_reserva_cabecera_detalle.py) una fila de "reservas"
ERA una sola prenda; esa tabla es ahora `reserva_detalles`, y `reservas` es
la cabecera nueva.

Reserva (cabecera) -- quién, dónde y cuándo:
  - cliente_id/sucursal_id: mismo criterio que antes (el Cliente ELIGE la
    sucursal, el backend solo valida que exista y esté activa -- a
    diferencia de CU14/15/16, donde siempre sale del Encargado autenticado).
  - codigo_reserva: identificador visible para el Cliente y el Encargado
    (ej. "RS-00025") -- el `id` interno de Postgres NUNCA se expone como
    "número de reserva" en ningún contrato de salida.
  - fecha_reserva/hora_inicio: el bloque de 1h que reserva la VISITA entera
    -- todas las prendas de una misma reserva comparten el mismo bloque y la
    misma sucursal (ver CU17_CrearReservaPrendas/service.py para las reglas
    de fecha/horario). hora_fin no se guarda: siempre es hora_inicio + 1h.
  - estado_general: un resumen AGREGADO de los `estado` de sus detalles
    (ver `calcular_estado_general` más abajo) -- se recalcula cada vez que
    CU19/CU20 cambian el estado de un detalle, dentro de la misma
    transacción; nunca se edita a mano ni es la fuente de verdad de nada.

ReservaDetalle -- una prenda dentro de esa visita:
  - producto_variante_id + cantidad: igual que antes (talla+color, CU08).
  - estado: el ciclo de vida real vive AQUÍ, por prenda -- es lo que permite
    que, dentro de la misma reserva, una prenda llegue a LISTA_PARA_CAJA
    mientras otra sigue PENDIENTE y una tercera fue CANCELADA. Mismo enum
    EstadoReserva y mismo flujo que ya documentaba este archivo:

        PENDIENTE -> PREPARADA -> EN_ATENCION -> ATENDIDA (sin compra)
                                               -> LISTA_PARA_CAJA (a caja)
        PENDIENTE -> EN_ATENCION (llega sin pasar por PREPARADA)
        PENDIENTE | PREPARADA -> VENCIDA (nunca llegó, venció su bloque)
        PENDIENTE | PREPARADA -> CANCELADA (CU19, por detalle o por reserva)

IMPORTANTE (mismo alcance que ya regía antes de esta migración): ninguna de
las dos tablas descuenta StockSucursal.cantidad (el físico). Cada
ReservaDetalle solo dice "esta cantidad de esta variante, dentro de esta
reserva" -- el bloqueo persistente sigue viviendo en
StockSucursal.stock_reservado, una fila de stock por detalle (ver
CU17_CrearReservaPrendas/service.py). Cancelar (CU19) y atender (CU20) cada
detalle -- y liberar su stock_reservado -- siguen siendo responsabilidad de
esos CU, nunca de este módulo.

cliente_id referencia a Usuario (P2_UsuariosYAccesos) SOLO por columna, sin
relationship() ORM -- mismo patrón ya usado por RecepcionMercaderia y
MovimientoInventario (P1): el Cliente dueño de la reserva se resuelve en la
capa de servicio de CU17 a partir del actor ya autenticado, nunca por join.

producto_variante_id sigue con ON DELETE CASCADE por el mismo motivo ya
documentado en stock_sucursal.py y movimiento_inventario.py: CU08 elimina
físicamente una ProductoVariante cuando el Administrador quita esa
combinación talla/color de un producto. reserva_id también usa ON DELETE
CASCADE: una cabecera nunca puede quedar con detalles huérfanos ni un
detalle sin su cabecera.
"""

import enum
from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal


class EstadoReserva(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PREPARADA = "PREPARADA"
    EN_ATENCION = "EN_ATENCION"
    LISTA_PARA_CAJA = "LISTA_PARA_CAJA"
    CANCELADA = "CANCELADA"
    ATENDIDA = "ATENDIDA"
    VENCIDA = "VENCIDA"


_ESTADOS_TERMINALES = (EstadoReserva.CANCELADA, EstadoReserva.ATENDIDA, EstadoReserva.VENCIDA)
_ESTADOS_EN_CURSO_FUERTE = (EstadoReserva.EN_ATENCION, EstadoReserva.LISTA_PARA_CAJA)


def calcular_estado_general(estados_detalle: list[EstadoReserva]) -> EstadoReserva:
    """Resume los `estado` de TODOS los detalles de una reserva en un único
    `estado_general` de cabecera -- se llama cada vez que un detalle cambia
    de estado (CU17 al crear, CU19 al cancelar, CU20 al avanzar el flujo o
    vencer), nunca se asigna a mano.

    Reglas, en orden de evaluación:
      1. Sin detalles (no debería ocurrir nunca): PENDIENTE por defecto.
      2. TODOS CANCELADA: CANCELADA -- el Cliente canceló la visita entera.
      3. TODOS terminales (CANCELADA/ATENDIDA/VENCIDA mezclados, pero no
         todos CANCELADA): prioriza el desenlace más "avanzado" para el
         resumen -- ATENDIDA si hay al menos una, si no VENCIDA si hay al
         menos una, si no CANCELADA.
      4. Algún detalle EN_ATENCION o LISTA_PARA_CAJA: EN_ATENCION -- el
         Cliente ya está en la sucursal, sin importar qué pasó con el resto.
      5. Algún detalle PREPARADA: PREPARADA.
      6. Cualquier otro caso (todos PENDIENTE, o PENDIENTE mezclado con
         detalles ya terminales): PENDIENTE -- todavía hay prendas por
         atender y el Cliente no ha llegado.
    """
    if not estados_detalle:
        return EstadoReserva.PENDIENTE

    if all(estado == EstadoReserva.CANCELADA for estado in estados_detalle):
        return EstadoReserva.CANCELADA

    if all(estado in _ESTADOS_TERMINALES for estado in estados_detalle):
        if EstadoReserva.ATENDIDA in estados_detalle:
            return EstadoReserva.ATENDIDA
        if EstadoReserva.VENCIDA in estados_detalle:
            return EstadoReserva.VENCIDA
        return EstadoReserva.CANCELADA

    if any(estado in _ESTADOS_EN_CURSO_FUERTE for estado in estados_detalle):
        return EstadoReserva.EN_ATENCION

    if any(estado == EstadoReserva.PREPARADA for estado in estados_detalle):
        return EstadoReserva.PREPARADA

    return EstadoReserva.PENDIENTE


class Reserva(Base):
    """Cabecera -- una visita del Cliente a una sucursal en un bloque
    horario, con 1 o más prendas (ver ReservaDetalle.reserva)."""

    __tablename__ = "reservas"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_reserva: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), nullable=False)
    fecha_reserva: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    estado_general: Mapped[EstadoReserva] = mapped_column(
        SAEnum(EstadoReserva, name="estado_reserva"), nullable=False, default=EstadoReserva.PENDIENTE
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sucursal: Mapped[Sucursal] = relationship(lazy="joined")
    # order_by por id: los detalles se muestran siempre en el orden en que se
    # agregaron a la reserva -- relevante quede fijo aunque cambien de estado.
    detalles: Mapped[list["ReservaDetalle"]] = relationship(
        back_populates="reserva", cascade="all, delete-orphan", order_by="ReservaDetalle.id"
    )

    def recalcular_estado_general(self) -> None:
        """Recalcula `estado_general` a partir del `estado` actual de cada
        detalle YA cargado en `self.detalles` -- se llama siempre dentro de
        la misma transacción que mutó algún detalle (ver CU17/CU19/CU20
        service.py), nunca dispara una consulta nueva por sí sola."""
        self.estado_general = calcular_estado_general([detalle.estado for detalle in self.detalles])


class ReservaDetalle(Base):
    """Una prenda dentro de una Reserva -- variante + cantidad, con estado
    individual (ver EstadoReserva) independiente del de sus hermanos."""

    __tablename__ = "reserva_detalles"
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_reserva_detalle_cantidad_positiva"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reserva_id: Mapped[int] = mapped_column(ForeignKey("reservas.id", ondelete="CASCADE"), nullable=False)
    producto_variante_id: Mapped[int] = mapped_column(
        ForeignKey("producto_variantes.id", ondelete="CASCADE"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[EstadoReserva] = mapped_column(
        SAEnum(EstadoReserva, name="estado_reserva"), nullable=False, default=EstadoReserva.PENDIENTE
    )

    reserva: Mapped[Reserva] = relationship(back_populates="detalles")
    producto_variante: Mapped[ProductoVariante] = relationship(lazy="joined")
