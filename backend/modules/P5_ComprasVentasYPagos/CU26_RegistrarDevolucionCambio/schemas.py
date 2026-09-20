"""Contratos de entrada/salida de CU26 -- Registrar devolución o cambio (Cajero).

JSON limpio, sin nada específico de Angular. Angular nunca envía precios,
monto de reembolso, cajero_id ni sucursal_id -- solo `venta_detalle_id` +
`cantidad` (y, según la operación, `motivo`/`observacion` o
`variante_nueva_id`); FastAPI recalcula/verifica todo lo demás contra la
Venta y el VentaDetalle ya registrados.

Campos monetarios como `float` (número JSON), NUNCA `Decimal` -- mismo motivo
ya documentado en CU21/CU24/CU25 (Pydantic v2 serializa `Decimal` como
STRING por defecto). El monto se calcula en Decimal en service.py, esto solo
cambia cómo se serializa hacia afuera.
"""

from datetime import datetime
from typing import Literal

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


class SucursalResumen(BaseModel):
    id: int
    nombre: str


class DetalleDevolucionOut(BaseModel):
    """Una línea de la venta que TODAVÍA puede devolverse/cambiarse -- las
    que ya se agotaron (ver `cantidad_disponible`) no aparecen (filtradas en
    service.py, nunca en el frontend)."""

    venta_detalle_id: int
    producto: ProductoResumen
    variante: VarianteResumen
    cantidad_comprada: int
    cantidad_disponible: int
    precio_unitario: float


class VentaDevolucionOut(BaseModel):
    """La venta encontrada, lista para trabajar en CU26 -- SOLO si estaba
    PAGADA (ver service.py: buscar_venta rechaza cualquier otro estado)."""

    venta_id: int
    codigo_venta: str
    fecha_creacion: datetime
    sucursal: SucursalResumen
    cliente_nombre: str | None
    tipo: str
    metodo_pago: str
    total: float
    detalles: list[DetalleDevolucionOut]


class RegistrarDevolucionRequest(BaseModel):
    venta_id: int
    venta_detalle_id: int
    cantidad: int = Field(gt=0)
    motivo: Literal["TALLA", "DEFECTO", "PRODUCTO_INCORRECTO", "OTRO"]
    observacion: str | None = Field(default=None, max_length=300)


class DevolucionOut(BaseModel):
    id: int
    cantidad: int
    monto_reembolso: float | None
    metodo_reembolso: str | None
    estado_reembolso: str | None
    stripe_refund_id: str | None


class VarianteCambioOut(BaseModel):
    """Una variante alternativa del MISMO producto -- con el disponible YA
    calculado (`stock_actual - stock_reservado`) para la sucursal de la
    Venta (ver service.py: nunca la del Cajero si difiere, aunque en la
    práctica siempre coinciden)."""

    producto_variante_id: int
    talla: TallaResumen
    color: ColorResumen
    disponible: int


class RegistrarCambioRequest(BaseModel):
    venta_id: int
    venta_detalle_id: int
    cantidad: int = Field(gt=0)
    variante_nueva_id: int


class CambioOut(BaseModel):
    id: int
    cantidad: int
    variante_original: VarianteResumen
    variante_nueva: VarianteResumen
