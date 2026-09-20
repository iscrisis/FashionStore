"""Contratos de salida de CU20 -- Atender reserva de prendas (Encargado).

Define sus PROPIOS contratos en vez de reutilizar ReservaOut de CU17: el
panel del Encargado necesita datos que la vista del Cliente nunca expone
(nombre de quién reservó) y jamás depende de un `cliente_id` recibido del
frontend para autorizar nada -- ver service.py, que siempre resuelve la
sucursal desde el actor autenticado.

`ReservaPanelOut` es la cabecera (una tarjeta = una reserva = una visita del
Cliente) con TODOS sus detalles anidados -- ver Models/reserva.py. Dos
niveles de acción, nunca mezclados (ver service.py):
  - a nivel DETALLE (preparar, decidir no comprar / enviar a caja): cada
    acción devuelve solo ese `ReservaDetallePanelOut` ya actualizado, nunca
    la cabecera completa -- el panel (Angular) reemplaza esa única tarjeta
    de detalle dentro de la reserva que ya tiene cargada.
  - a nivel RESERVA (confirmar llegada, finalizar atención): cada acción
    devuelve la `ReservaPanelOut` completa, porque cambia el estado de la
    cabecera misma.

Reutilizada también por GET /reservas/cajero/pendientes (integración mínima
con el rol Cajero): la misma forma agrupada, filtrando `detalles` a solo las
prendas LISTA_PARA_CAJA de cabeceras cuyo estado_general YA es
LISTA_PARA_CAJA (ver AtenderReservaService.listar_pendientes_cajero).

JSON limpio, sin nada específico de Angular -- mismo espíritu que el resto de
la API (preparado para que Flutter lo consuma igual, aunque el panel del
Encargado es exclusivamente Angular Web por ahora).
"""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict

EstadoReservaPanel = Literal[
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
    id: int
    talla: TallaResumen
    color: ColorResumen


class ProductoResumen(BaseModel):
    id: int
    nombre: str
    imagen_principal_url: str | None


class ClienteResumen(BaseModel):
    id: int
    nombre: str


class ReservaDetallePanelOut(BaseModel):
    """Una prenda dentro de la reserva, tal como la ve el Encargado -- lo
    que devuelve preparar/decidir-no-comprar/decidir-enviar-a-caja,
    afectando SOLO este detalle, nunca al resto de la reserva ni a su
    cabecera."""

    id: int
    reserva_id: int
    producto: ProductoResumen
    variante: VarianteResumen
    cantidad: int
    estado: EstadoReservaPanel


class ReservaPanelOut(BaseModel):
    """Cabecera de una reserva (una visita del Cliente) con TODAS sus
    prendas -- una tarjeta del panel del Encargado."""

    id: int
    codigo_reserva: str
    cliente: ClienteResumen
    estado_general: EstadoReservaPanel
    fecha_reserva: date
    hora_inicio: time
    hora_fin: time
    fecha_creacion: datetime
    detalles: list[ReservaDetallePanelOut]
