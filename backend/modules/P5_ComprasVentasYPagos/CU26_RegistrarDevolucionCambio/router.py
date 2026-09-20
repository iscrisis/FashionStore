"""Endpoints de CU26 -- Registrar devolución o cambio (Cajero).

Requiere un CAJERO autenticado. Reutiliza get_current_usuario/require_roles
ya existentes (app.core.deps). La sucursal autorizada se deriva SIEMPRE de
`actor.sucursal_id` (mismo helper `_sucursal_de` que ya define cada router de
CU14/CU15/CU16/CU20/CU24/CU25 -- se repite aquí en vez de importarlo, mismo
criterio ya documentado en esos módulos: no acoplar routers por una función
de una línea), nunca de un sucursal_id que Angular pueda enviar.

Rutas REST bajo "/devoluciones-cambios", prefijo propio -- no reutiliza
"/ventas-presenciales" ni "/pagos-presenciales": CU26 opera SOBRE una Venta
ya pagada, pero es un recurso distinto (una devolución/cambio, no una venta
ni un pago nuevo).

Los mensajes de error de Stripe nunca exponen el detalle interno de la
librería -- mismo criterio ya usado en CU23 (ver
app/integrations/stripe_client.py).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.integrations.stripe_client import StripeNoConfiguradoError, StripeOperationError
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import (
    CambioOut,
    DevolucionOut,
    RegistrarCambioRequest,
    RegistrarDevolucionRequest,
    VarianteCambioOut,
    VentaDevolucionOut,
)
from .service import (
    CantidadInvalidaError,
    DevolucionCambioService,
    ObservacionRequeridaError,
    PagoNoEncontradoError,
    StockInsuficienteError,
    SucursalCajeroNoDefinidaError,
    VarianteIgualError,
    VarianteMismoProductoError,
    VarianteNoEncontradaError,
    VentaDetalleNoEncontradoError,
    VentaNoEncontradaError,
)

require_cajero = require_roles(RolUsuario.CAJERO)

router = APIRouter(prefix="/devoluciones-cambios", tags=["CU26 - Registrar devolución o cambio"])

_MSG_SIN_SUCURSAL = "Tu usuario no está vinculado a ninguna sucursal."
_MSG_VENTA_NO_ENCONTRADA = "No se encontró una venta pagada con ese código en tu sucursal."
_MSG_DETALLE_NO_ENCONTRADO = "Esa prenda no pertenece a la venta indicada."
_MSG_CANTIDAD_INVALIDA = "La cantidad indicada supera lo que todavía puede devolverse o cambiarse."
_MSG_OBSERVACION_REQUERIDA = "Escribe una breve observación para el motivo \"Otro\"."
_MSG_VARIANTE_NO_ENCONTRADA = "Esa variante no existe o no está disponible."
_MSG_VARIANTE_MISMO_PRODUCTO = "Solo puedes cambiar por otra talla o color del mismo producto."
_MSG_VARIANTE_IGUAL = "Selecciona una talla o color distinto al actual."
_MSG_STOCK_INSUFICIENTE = "No hay disponibilidad suficiente para esa prenda."
_MSG_PAGO_NO_ENCONTRADO = "Esta venta no tiene un pago confirmado registrado."
_MSG_STRIPE_NO_DISPONIBLE = "El reembolso no está disponible en este momento. Inténtalo más tarde."


@router.get("/buscar", response_model=VentaDevolucionOut)
def buscar_venta(
    codigo_venta: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cajero),
) -> VentaDevolucionOut:
    try:
        return DevolucionCambioService(db).buscar_venta(actor, codigo_venta)
    except SucursalCajeroNoDefinidaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _MSG_SIN_SUCURSAL) from exc
    except VentaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_VENTA_NO_ENCONTRADA) from exc
    except PagoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_PAGO_NO_ENCONTRADO) from exc


@router.get("/{venta_id}/opciones-cambio/{venta_detalle_id}", response_model=list[VarianteCambioOut])
def opciones_cambio(
    venta_id: int,
    venta_detalle_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cajero),
) -> list[VarianteCambioOut]:
    try:
        return DevolucionCambioService(db).opciones_cambio(actor, venta_id, venta_detalle_id)
    except SucursalCajeroNoDefinidaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _MSG_SIN_SUCURSAL) from exc
    except VentaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_VENTA_NO_ENCONTRADA) from exc
    except VentaDetalleNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_DETALLE_NO_ENCONTRADO) from exc


@router.post("/devolucion", response_model=DevolucionOut, status_code=status.HTTP_201_CREATED)
def registrar_devolucion(
    payload: RegistrarDevolucionRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cajero),
) -> DevolucionOut:
    try:
        return DevolucionCambioService(db).registrar_devolucion(actor, payload)
    except SucursalCajeroNoDefinidaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _MSG_SIN_SUCURSAL) from exc
    except VentaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_VENTA_NO_ENCONTRADA) from exc
    except VentaDetalleNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_DETALLE_NO_ENCONTRADO) from exc
    except ObservacionRequeridaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_OBSERVACION_REQUERIDA) from exc
    except CantidadInvalidaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_CANTIDAD_INVALIDA) from exc
    except PagoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_PAGO_NO_ENCONTRADO) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_STOCK_INSUFICIENTE) from exc
    except (StripeNoConfiguradoError, StripeOperationError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, _MSG_STRIPE_NO_DISPONIBLE) from exc


@router.post("/cambio", response_model=CambioOut, status_code=status.HTTP_201_CREATED)
def registrar_cambio(
    payload: RegistrarCambioRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cajero),
) -> CambioOut:
    try:
        return DevolucionCambioService(db).registrar_cambio(actor, payload)
    except SucursalCajeroNoDefinidaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _MSG_SIN_SUCURSAL) from exc
    except VentaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_VENTA_NO_ENCONTRADA) from exc
    except VentaDetalleNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_DETALLE_NO_ENCONTRADO) from exc
    except VarianteIgualError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_VARIANTE_IGUAL) from exc
    except VarianteNoEncontradaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_VARIANTE_NO_ENCONTRADA) from exc
    except VarianteMismoProductoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_VARIANTE_MISMO_PRODUCTO) from exc
    except CantidadInvalidaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_CANTIDAD_INVALIDA) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_STOCK_INSUFICIENTE) from exc
