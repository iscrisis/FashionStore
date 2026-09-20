"""Contratos de entrada/salida de CU25 -- Procesar pago presencial (Cajero).

JSON limpio, sin nada específico de Angular -- toda regla de negocio vive en
FastAPI. Angular nunca envía monto, total, estado, cajero_id ni sucursal_id:
solo el método elegido y los datos propios de ese método
(monto_recibido/tipo_tarjeta/referencia) -- FastAPI recalcula/verifica todo
lo demás contra la Venta ya registrada por CU24.

`ConfirmarPagoRequest` es una unión discriminada por `metodo_pago`: cada
método válido (EFECTIVO/TARJETA/QR) tiene su propio esquema, con SOLO los
campos que le corresponden -- así un pago con TARJETA nunca puede llegar con
`monto_recibido`, por ejemplo.

Campos monetarios como `float` (número JSON), NUNCA `Decimal` -- Pydantic v2
serializa `Decimal` como STRING por defecto (bug real ya corregido en CU21,
ver CU21_UsarCarritoCompras/schemas.py). El monto se calcula en Decimal en
service.py, esto solo cambia cómo se serializa hacia afuera.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ConfirmarPagoEfectivoRequest(BaseModel):
    metodo_pago: Literal["EFECTIVO"]
    monto_recibido: float = Field(gt=0)


class ConfirmarPagoTarjetaRequest(BaseModel):
    metodo_pago: Literal["TARJETA"]
    tipo_tarjeta: Literal["DEBITO", "CREDITO"]
    referencia: str | None = Field(default=None, max_length=120)


class ConfirmarPagoQrRequest(BaseModel):
    metodo_pago: Literal["QR"]
    referencia: str | None = Field(default=None, max_length=120)


ConfirmarPagoRequest = Annotated[
    ConfirmarPagoEfectivoRequest | ConfirmarPagoTarjetaRequest | ConfirmarPagoQrRequest,
    Field(discriminator="metodo_pago"),
]


class PagoConfirmadoOut(BaseModel):
    """Lo mínimo para la pantalla "PAGO REGISTRADO" -- código, total, método
    y (solo EFECTIVO) el cambio. El comprobante completo es CU31, fuera de
    este alcance."""

    codigo_venta: str
    total: float
    metodo_pago: str
    monto_recibido: float | None = None
    cambio: float | None = None
