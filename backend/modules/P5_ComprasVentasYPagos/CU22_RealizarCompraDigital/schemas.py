"""Contratos de entrada/salida de CU22 -- Realizar compra digital (Cliente).

JSON limpio, sin nada específico de Angular -- preparado para que Flutter lo
consuma igual más adelante: toda regla de negocio vive en FastAPI, nunca en
el cliente.

Todos los campos monetarios se exponen como `float` (número JSON), NUNCA
como `Decimal` -- Pydantic v2 serializa `Decimal` como STRING por defecto,
lo que rompe cualquier consumidor que espere un número (bug real ya
corregido en CU21, ver CU21_UsarCarritoCompras/schemas.py). El valor sigue
calculándose en Decimal en service.py (precisión monetaria exacta), esto
solo cambia cómo se serializa hacia afuera.
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


class LineaCompraOut(BaseModel):
    """Una de las prendas ya seleccionadas en el carrito (CU21) -- misma
    unidad concreta (Producto + Color + Talla), nunca con cantidad > 1 por
    línea (ver CU21_UsarCarritoCompras/Models/carrito.py). `precio_unitario`
    es el precio EFECTIVO vigente (CU32); `precio_base`/`en_promocion`/
    `porcentaje_descuento` vienen del mismo cálculo (ver
    P6_InnovacionYAnalisis/CU32_GestionarPromociones/precio_efectivo.py)."""

    item_id: int
    producto_variante_id: int
    producto: ProductoResumen
    variante: VarianteResumen
    precio_unitario: float
    precio_base: float
    en_promocion: bool
    porcentaje_descuento: float | None


class ResumenCompraOut(BaseModel):
    """Pantalla "FINALIZAR COMPRA" -- SOLO las prendas que el Cliente marcó
    como seleccionadas en su carrito, antes de elegir sucursal."""

    items: list[LineaCompraOut]
    total: float


class SucursalCompraOut(BaseModel):
    """Una sucursal activa de la ciudad elegida, con si puede o no cubrir
    TODA la compra (todas las variantes + cantidades seleccionadas) -- ver
    CU22_RealizarCompraDigital/service.py:sucursales_disponibles."""

    id: int
    nombre: str
    direccion: str
    disponible_para_compra: bool


class ConfirmarCompraRequest(BaseModel):
    sucursal_id: int


class SucursalVentaOut(BaseModel):
    id: int
    nombre: str
    direccion: str
    ciudad: str


class VentaDetalleOut(BaseModel):
    """`precio_unitario`/`subtotal` quedan HISTÓRICOS desde este momento
    (CU32): el precio efectivo (con o sin promoción) se congela en
    VentaDetalle al confirmar -- si la promoción cambia o termina después,
    esta Venta ya confirmada sigue mostrando el mismo precio con el que se
    pagó, nunca se recalcula (ver service.py:confirmar)."""

    producto: ProductoResumen
    variante: VarianteResumen
    cantidad: int
    precio_unitario: float
    subtotal: float


class VentaOut(BaseModel):
    """La compra digital ya confirmada -- PENDIENTE_PAGO (CU23 decidirá
    después si se aprueba o se rechaza el pago, fuera de este alcance)."""

    id: int
    codigo_venta: str
    sucursal: SucursalVentaOut
    tipo: str
    estado: str
    total: float
    fecha_creacion: datetime
    detalles: list[VentaDetalleOut]
