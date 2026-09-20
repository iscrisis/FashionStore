"""Contratos de entrada/salida de CU21 -- Usar carrito de compras (Cliente).

JSON limpio, sin nada específico de Angular -- preparado para que Flutter lo
consume igual más adelante (ver docstring del paquete): toda regla de negocio
vive en FastAPI, nunca en el cliente.

`CarritoOut` siempre trae la lista completa de `items` (nunca un item
aislado): cada mutación (agregar, seleccionar, eliminar) devuelve el
carrito entero ya actualizado, mismo criterio que ya usan CU17/CU19/CU20 al
devolver la cabecera completa tras una transición -- el Cliente/Flutter
reemplaza todo su estado local con la respuesta, sin reconstruirlo a mano.

Cada item es UNA unidad concreta de una variante (no tiene `cantidad`):
agregar la misma variante otra vez crea OTRO item independiente, con su
propio `item_id` y su propio `seleccionado` -- así el Cliente puede marcar
solo una de dos unidades iguales para una compra futura.

`precio_unitario`/`subtotal_seleccionado` se exponen como `float` (número
JSON), NUNCA como `Decimal`: Pydantic v2 serializa `Decimal` como STRING en
JSON por defecto (`"80.00"`, no `80.00`), lo que rompe cualquier consumidor
que espere un número (Angular, Flutter). Mismo criterio ya usado por
Producto.precio_venta en CU11 (ver
CU11_ConsultarCatalogoPrendas/schemas.py) -- el valor SIGUE calculándose en
Decimal en service.py (precisión monetaria exacta contra PostgreSQL), esto
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


class AgregarItemRequest(BaseModel):
    """Agrega SIEMPRE una sola unidad -- sin `cantidad`: para dos unidades de
    la misma variante, el Cliente llama este endpoint dos veces (ver
    CarritoService.agregar_item)."""

    producto_variante_id: int


class ActualizarSeleccionRequest(BaseModel):
    """Marca/desmarca una unidad puntual para una compra futura -- no crea
    Venta ni Pago (eso es de un CU posterior)."""

    seleccionado: bool


class CarritoItemOut(BaseModel):
    """Una unidad concreta del carrito -- Producto + Color + Talla (una
    ProductoVariante). `precio_unitario` es SIEMPRE el precio EFECTIVO
    vigente al momento de consultar (CU32 -- promoción ACTIVA si existe,
    si no el precio base), nunca un valor guardado -- ver Models/carrito.py.
    `precio_base`/`en_promocion`/`porcentaje_descuento` (CU32) se calculan
    en el mismo lugar (ver P6_InnovacionYAnalisis/
    CU32_GestionarPromociones/precio_efectivo.py), nunca en Angular."""

    item_id: int
    producto_variante_id: int
    producto: ProductoResumen
    variante: VarianteResumen
    precio_unitario: float
    precio_base: float
    en_promocion: bool
    porcentaje_descuento: float | None
    seleccionado: bool


class CarritoOut(BaseModel):
    items: list[CarritoItemOut]
    subtotal_seleccionado: float
    fecha_actualizacion: datetime
