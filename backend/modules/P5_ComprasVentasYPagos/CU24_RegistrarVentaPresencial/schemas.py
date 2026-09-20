"""Contratos de entrada/salida de CU24 -- Registrar venta presencial (Cajero).

JSON limpio, sin nada específico de Angular -- preparado para que Flutter lo
consuma igual más adelante: toda regla de negocio vive en FastAPI, nunca en
el cliente. Angular nunca envía precios, subtotal ni total: solo
`producto_variante_id` + `cantidad` por línea (venta directa) o el
`reserva_id` a cargar (venta desde reserva); FastAPI recalcula todo.

Campos monetarios como `float` (número JSON), NUNCA `Decimal` -- Pydantic v2
serializa `Decimal` como STRING por defecto (bug real ya corregido en CU21,
ver CU21_UsarCarritoCompras/schemas.py). El monto se calcula en Decimal en
service.py, esto solo cambia cómo se serializa hacia afuera.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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


class ProductoBusquedaOut(BaseModel):
    """Un resultado de "buscar producto por nombre" -- SOLO variantes
    activas, con el disponible YA calculado para la sucursal del Cajero
    autenticado (`stock_actual - stock_reservado`, nunca stock reservado).
    `precio_unitario` es SIEMPRE el precio EFECTIVO vigente (CU32 -- el
    Cajero nunca debe vender a un precio distinto del que ve la Web, ver
    P6_InnovacionYAnalisis/CU32_GestionarPromociones/precio_efectivo.py);
    `en_promocion`/`porcentaje_descuento` son solo informativos para esta
    pantalla."""

    producto_variante_id: int
    producto: ProductoResumen
    variante: VarianteResumen
    precio_unitario: float
    en_promocion: bool
    porcentaje_descuento: float | None
    disponible: int


class ItemVentaDirectaRequest(BaseModel):
    producto_variante_id: int
    cantidad: int = Field(gt=0)


class CrearVentaDirectaRequest(BaseModel):
    items: list[ItemVentaDirectaRequest] = Field(min_length=1)


class VentaDetalleOut(BaseModel):
    producto: ProductoResumen
    variante: VarianteResumen
    cantidad: int
    precio_unitario: float
    subtotal: float


class ReservaResumenOut(BaseModel):
    codigo_reserva: str
    cliente_nombre: str


class VentaPresencialOut(BaseModel):
    """La venta presencial ya registrada -- PENDIENTE_PAGO (CU25 confirmará
    el pago en el mostrador, fuera de este alcance)."""

    id: int
    codigo_venta: str
    tipo: str
    estado: str
    origen: str
    total: float
    fecha_creacion: datetime
    reserva: ReservaResumenOut | None
    detalles: list[VentaDetalleOut]
