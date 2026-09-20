"""Endpoints de CU23 -- Procesar pago electrónico (Cliente).

Requiere un CLIENTE autenticado. Reutiliza get_current_usuario / require_roles
ya existentes (app.core.deps). cliente_id sale SIEMPRE de `actor` (el
usuario autenticado), nunca del body: un Cliente jamás puede pagar ni
verificar el pago de la Venta de otro.

Rutas REST bajo "/pagos". `success_url`/`cancel_url` de Stripe se arman acá
(no en el service, que no necesita conocer rutas de Angular) apuntando a
FRONTEND_URL (ya existente, reutilizada -- ver app/core/config.py) +
"/pago/resultado", con `{CHECKOUT_SESSION_ID}` como placeholder literal que
Stripe reemplaza por el id real de la sesión al redirigir de vuelta.

Los mensajes de error nunca exponen el detalle interno de Stripe ni un
estado técnico -- solo texto amigable (ver requerimiento de CU23: "no
mostrar errores internos de Stripe").
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import require_roles
from app.db.session import get_db
from app.integrations.stripe_client import StripeNoConfiguradoError, StripeOperationError
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import CheckoutSessionOut, CrearCheckoutRequest, VentaPagadaOut, VerificarPagoRequest
from .service import (
    PagoElectronicoService,
    PagoNoCompletadoError,
    SesionPagoNoEncontradaError,
    StockInsuficienteError,
    VentaNoEncontradaError,
    VentaNoPagableError,
)

require_cliente = require_roles(RolUsuario.CLIENTE)

router = APIRouter(prefix="/pagos", tags=["CU23 - Procesar pago electrónico"])

_MSG_VENTA_NO_ENCONTRADA = "No se encontró la compra indicada."
_MSG_VENTA_NO_PAGABLE = "Esta compra ya no admite un nuevo intento de pago."
_MSG_STOCK_INSUFICIENTE = "Ya no hay disponibilidad suficiente para completar esta compra."
_MSG_STRIPE_NO_DISPONIBLE = "El pago no está disponible en este momento. Inténtalo más tarde."
_MSG_PAGO_NO_COMPLETADO = "El pago no fue completado."
_MSG_SESION_NO_ENCONTRADA = "No se encontró esa sesión de pago."


@router.post("/checkout", response_model=CheckoutSessionOut, status_code=status.HTTP_201_CREATED)
def crear_checkout(
    payload: CrearCheckoutRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> CheckoutSessionOut:
    base = settings.FRONTEND_URL.rstrip("/")
    success_url = f"{base}/pago/resultado?venta_id={payload.venta_id}&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base}/pago/resultado?venta_id={payload.venta_id}&cancelado=1"

    try:
        checkout_url = PagoElectronicoService(db).crear_checkout(
            actor.id, payload.venta_id, success_url, cancel_url
        )
        return CheckoutSessionOut(checkout_url=checkout_url)
    except VentaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_VENTA_NO_ENCONTRADA) from exc
    except VentaNoPagableError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_VENTA_NO_PAGABLE) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_STOCK_INSUFICIENTE) from exc
    except (StripeNoConfiguradoError, StripeOperationError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, _MSG_STRIPE_NO_DISPONIBLE) from exc


@router.post("/verificar", response_model=VentaPagadaOut)
def verificar_pago(
    payload: VerificarPagoRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> VentaPagadaOut:
    try:
        return PagoElectronicoService(db).verificar_pago(actor.id, payload.session_id)
    except SesionPagoNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_SESION_NO_ENCONTRADA) from exc
    except PagoNoCompletadoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_PAGO_NO_COMPLETADO) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_STOCK_INSUFICIENTE) from exc
    except (StripeNoConfiguradoError, StripeOperationError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, _MSG_STRIPE_NO_DISPONIBLE) from exc
