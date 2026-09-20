"""Contratos de entrada/salida de CU17 -- Crear reserva de prendas (Cliente).

`ReservaOut` representa la CABECERA de una reserva (una visita del Cliente a
una sucursal, en un bloque horario) con su lista de `detalles` (prendas) --
ver Models/reserva.py. CU19 (cancelar) y CU20 (atender) reutilizan
`ReservaDetalleOut` para sus respuestas a nivel de detalle individual, en vez
de duplicarlo.

El request de creación (`CrearReservaRequest`) sigue pidiendo UNA sola
prenda: CU17 no expone todavía un carrito (fuera de alcance, ver CU21) --
internamente arma una reserva con un único detalle, pero la salida ya usa la
forma agrupada para que el Cliente vea "Reserva RS-00025" desde el primer
momento, consistente con lo que después mostrará CU18 si esa misma reserva
llega a tener más prendas.
"""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Agregado por CU20 (Atender reserva de prendas): PREPARADA, EN_ATENCION,
# LISTA_PARA_CAJA y VENCIDA amplían el ciclo de vida de un detalle más allá
# de PENDIENTE/CANCELADA/ATENDIDA -- ver Models/reserva.py para el flujo
# completo y CU20_AtenderReservaPrendas para quién produce cada uno. El mismo
# enum sirve para `estado_general` de la cabecera (agregado, ver
# Models/reserva.py:calcular_estado_general) y para `estado` de cada detalle.
EstadoReservaOut = Literal[
    "PENDIENTE", "PREPARADA", "EN_ATENCION", "LISTA_PARA_CAJA", "CANCELADA", "ATENDIDA", "VENCIDA"
]


class TallaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class VarianteResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    talla: TallaResumen
    color: ColorResumen


class ProductoResumen(BaseModel):
    id: int
    nombre: str
    imagen_principal_url: str | None


class CiudadResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class SucursalResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    # Agregado para CU18 (Consultar reserva): la tarjeta del Cliente muestra
    # sucursal + ciudad juntas -- Sucursal.ciudad ya viene cargada (relationship
    # lazy="joined", ver Models/sucursal.py), no agrega ninguna consulta nueva.
    ciudad: CiudadResumen


class CrearReservaRequest(BaseModel):
    producto_variante_id: int
    sucursal_id: int
    cantidad: int = Field(gt=0)
    fecha_reserva: date
    hora_inicio: time

    @field_validator("hora_inicio")
    @classmethod
    def _validar_bloque_de_hora(cls, valor: time) -> time:
        # Regla estructural (no depende de "ahora"): los bloques son de 1
        # hora exacta -- "10:00", "11:00", nunca "10:30". La ventana de fecha
        # (hoy..+7 días), el horario de atención por día de la semana y la
        # anticipación mínima si es hoy SÍ dependen de "ahora" y se validan
        # en el service (ver CrearReservaService._validar_fecha_hora).
        if valor.minute != 0 or valor.second != 0 or valor.microsecond != 0:
            raise ValueError("El horario debe ser un bloque exacto de una hora (ej. 10:00, 11:00).")
        return valor


class AgregarDetalleRequest(BaseModel):
    """Agregar UNA prenda más a una reserva PENDIENTE ya existente -- ver
    CrearReservaService.agregar_detalle. No pide sucursal/fecha/hora: esos
    datos son siempre los de la cabecera a la que se agrega (todas las
    prendas de una reserva comparten sucursal y bloque horario)."""

    producto_variante_id: int
    cantidad: int = Field(gt=0)


class ReservaDetalleOut(BaseModel):
    """Una prenda dentro de una reserva -- reutilizado por CU19 (cancelar un
    detalle) y CU20 (panel del Encargado, acciones por detalle)."""

    id: int
    producto: ProductoResumen
    variante: VarianteResumen
    cantidad: int
    estado: EstadoReservaOut


class ReservaOut(BaseModel):
    """Cabecera de una reserva (una visita del Cliente a una sucursal) con
    todas sus prendas -- ver Models/reserva.py. `id` es el identificador
    interno; `codigo_reserva` (ej. "RS-00025") es el que se muestra siempre
    al Cliente."""

    id: int
    codigo_reserva: str
    sucursal: SucursalResumen
    estado_general: EstadoReservaOut
    fecha_reserva: date
    hora_inicio: time
    # El bloque reservado siempre dura 1h exacta -- se calcula en el service
    # a partir de hora_inicio, nunca se guarda como columna independiente.
    hora_fin: time
    fecha_creacion: datetime
    detalles: list[ReservaDetalleOut]
