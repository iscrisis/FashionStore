"""Contratos de entrada/salida de CU23 -- Procesar pago electrónico (Cliente).

JSON limpio, sin nada específico de Angular -- preparado para que Flutter lo
consuma igual más adelante: toda la lógica de Stripe vive en FastAPI, nunca
en el cliente. Angular jamás envía monto, precio ni estado: solo `venta_id`
(para pedir el Checkout) o `session_id` (para pedir la verificación).

Campos monetarios como `float` (número JSON), NUNCA `Decimal` -- Pydantic v2
serializa `Decimal` como STRING por defecto, bug real ya corregido en CU21
(ver CU21_UsarCarritoCompras/schemas.py). El monto se calcula en Decimal en
service.py, esto solo cambia cómo se serializa hacia afuera.
"""

from pydantic import BaseModel


class CrearCheckoutRequest(BaseModel):
    venta_id: int


class CheckoutSessionOut(BaseModel):
    """Únicamente la URL segura de Checkout -- Angular no recibe nada más
    de Stripe (ni el session_id, que solo vuelve a aparecer más tarde en la
    propia URL de retorno que arma FastAPI)."""

    checkout_url: str


class VerificarPagoRequest(BaseModel):
    session_id: str


class SucursalVentaOut(BaseModel):
    id: int
    nombre: str
    direccion: str
    ciudad: str


class VentaPagadaOut(BaseModel):
    """Solo se construye DESPUÉS de que FastAPI confirmó el pago contra
    Stripe -- ver service.py:verificar_pago. `estado` siempre vale "PAGADA"
    en esta salida (nunca se expone "PENDIENTE_PAGO" aquí)."""

    id: int
    codigo_venta: str
    estado: str
    total: float
    sucursal: SucursalVentaOut
