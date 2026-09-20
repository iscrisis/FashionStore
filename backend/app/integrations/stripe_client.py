"""Integración con Stripe Checkout Hosted (modo TEST) -- procesar pago
electrónico.

Único punto del backend que importa el SDK de `stripe` y lee
STRIPE_SECRET_KEY (ver app/core/config.py). No pertenece a ningún caso de
uso específico: CU23 es su primer consumidor, mismo criterio que
app/integrations/mailer.py con SMTP/CU03. La clave secreta NUNCA se envía a
Angular, nunca se registra en logs (ver `logger.error`, que solo deja
constancia del tipo de error, nunca el payload ni la clave) y nunca se lee
desde el request HTTP -- solo desde la variable de entorno del proceso.

Con Stripe Checkout Hosted, Angular NUNCA maneja número de tarjeta, CVC ni
fecha de vencimiento: solo recibe la URL de Checkout que devuelve
`crear_checkout_session` y redirige el navegador ahí (misma pestaña) -- toda
la pantalla de pago la sirve Stripe.
"""

import logging
from decimal import ROUND_HALF_UP, Decimal

import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)


class StripeNoConfiguradoError(Exception):
    """Falta STRIPE_SECRET_KEY -- ver .env.example."""


class StripeOperationError(Exception):
    """Stripe rechazó la operación (red, clave inválida, moneda no admitida,
    etc.) -- el detalle interno nunca se expone al Cliente (ver
    CU23_ProcesarPagoElectronico/router.py, que solo muestra un mensaje
    genérico y amigable)."""


def _monto_a_unidad_minima(monto: Decimal) -> int:
    """Convierte un monto Decimal en la moneda configurada (Bs u otra de 2
    decimales, ver STRIPE_CURRENCY) a la unidad mínima que espera Stripe
    (centavos) -- SIEMPRE con Decimal, nunca float, para no arrastrar
    imprecisión binaria en un monto de dinero real. `quantize` redondea al
    entero más cercano antes de convertir a int -- el monto ya viene con
    2 decimales exactos desde Venta.total (Numeric(10, 2)), así que en la
    práctica nunca hay nada que redondear de verdad."""
    return int((monto * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _api_key() -> str:
    if not settings.STRIPE_SECRET_KEY:
        raise StripeNoConfiguradoError(
            "STRIPE_SECRET_KEY no está configurada -- ver backend/.env.example."
        )
    return settings.STRIPE_SECRET_KEY


def crear_checkout_session(
    *,
    monto: Decimal,
    descripcion: str,
    venta_id: int,
    codigo_venta: str,
    success_url: str,
    cancel_url: str,
) -> "stripe.checkout.Session":
    """Crea una Checkout Session de Stripe por el monto EXACTO que ya
    calculó FastAPI (ver CU23_ProcesarPagoElectronico/service.py -- nunca un
    monto que Angular envíe). Un único line item (no uno por prenda): así el
    total cobrado en Stripe coincide exactamente con Venta.total, sin
    depender de que la suma de varios `unit_amount` redondeados dé lo mismo
    centavo a centavo."""
    try:
        return stripe.checkout.Session.create(
            api_key=_api_key(),
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": settings.STRIPE_CURRENCY,
                        "product_data": {"name": descripcion},
                        "unit_amount": _monto_a_unidad_minima(monto),
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            locale="es",
            client_reference_id=str(venta_id),
            metadata={"venta_id": str(venta_id), "codigo_venta": codigo_venta},
        )
    except stripe.error.StripeError as exc:
        logger.error("Stripe rechazó la creación del Checkout Session (%s).", type(exc).__name__)
        raise StripeOperationError("No se pudo iniciar el pago con Stripe.") from exc


def obtener_checkout_session(session_id: str) -> "stripe.checkout.Session":
    """Consulta a Stripe el estado REAL de una sesión -- única fuente de
    verdad de si un pago se completó (ver verificar_pago en service.py:
    Angular nunca decide esto, solo reenvía el session_id que Stripe le dio
    al volver)."""
    try:
        return stripe.checkout.Session.retrieve(session_id, api_key=_api_key())
    except stripe.error.StripeError as exc:
        logger.error("Stripe rechazó la consulta del Checkout Session (%s).", type(exc).__name__)
        raise StripeOperationError("No se pudo verificar el pago con Stripe.") from exc


def crear_refund(*, payment_intent_id: str, monto: Decimal) -> "stripe.Refund":
    """Reembolsa (modo TEST) el PaymentIntent de una compra pagada con
    Stripe -- primer consumidor: CU26 (registrar devolución/cambio), sobre
    una Venta DIGITAL ya PAGADA por CU23. El monto es SIEMPRE el que ya
    calculó FastAPI a partir de VentaDetalle (nunca uno que Angular envíe,
    ver CU26_RegistrarDevolucionCambio/service.py) y puede ser PARCIAL --
    corresponde únicamente a la cantidad de esa prenda que se devuelve, no
    necesariamente al total de la compra."""
    try:
        return stripe.Refund.create(
            api_key=_api_key(),
            payment_intent=payment_intent_id,
            amount=_monto_a_unidad_minima(monto),
        )
    except stripe.error.StripeError as exc:
        logger.error("Stripe rechazó el refund (%s).", type(exc).__name__)
        raise StripeOperationError("No se pudo procesar el reembolso con Stripe.") from exc
