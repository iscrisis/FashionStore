"""Contratos de salida de CU31 -- Emitir comprobante de venta (Cliente/Cajero).

JSON limpio, sin nada específico de Angular -- preparado para que Flutter lo
consuma igual más adelante (ver requerimiento "estructura reutilizable para
Flutter"). Ningún endpoint de este módulo recibe datos de negocio en el
body -- `venta_id` llega SIEMPRE por la URL, y todo lo demás (montos,
cliente, sucursal, método de pago) se resuelve del lado del servidor.

Campos monetarios como `float` (número JSON), NUNCA `Decimal` -- mismo motivo
ya documentado en CU21/CU24/CU25/CU26 (Pydantic v2 serializa `Decimal` como
STRING por defecto).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class SucursalComprobanteOut(BaseModel):
    id: int
    nombre: str
    direccion: str
    ciudad: str


class ClienteComprobanteOut(BaseModel):
    """Solo lo mínimo para el comprobante y para que el Cajero decida si
    mostrar el botón "Enviar" -- `correo` nunca se expone a nadie que no sea
    el propio Cliente o un Cajero ya autorizado sobre esa venta (ver
    service.py: la autorización se valida ANTES de armar esta salida)."""

    nombre: str
    correo: str


class DetalleComprobanteOut(BaseModel):
    producto: ProductoResumen
    variante: VarianteResumen
    cantidad: int
    precio_unitario: float
    subtotal: float


class ComprobanteVentaOut(BaseModel):
    """El comprobante completo -- SIEMPRE de una Venta PAGADA (ver
    service.py: cualquier otro estado se rechaza antes de armar esto).
    `estado`/`estado_pago` van fijos ("PAGADA"/"PAGADO") porque es la única
    combinación desde la que este contrato llega a construirse."""

    venta_id: int
    codigo_venta: str
    fecha_creacion: datetime
    tipo: str
    sucursal: SucursalComprobanteOut
    cliente: ClienteComprobanteOut | None
    detalles: list[DetalleComprobanteOut]
    total: float
    metodo_pago: str
    estado: str
    estado_pago: str


class EnviarComprobanteOut(BaseModel):
    """Respuesta SIEMPRE 200 -- incluso si el correo falló (ver
    service.py/__init__.py: nunca se bloquea ni se revierte nada por un SMTP
    caído, solo se informa `enviado=False` con un mensaje amigable)."""

    enviado: bool
    mensaje: str
