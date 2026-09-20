"""Endpoints de CU31 -- Emitir comprobante de venta (Cliente/Cajero).

Requiere un CLIENTE o un CAJERO autenticado -- reutiliza get_current_usuario/
require_roles ya existentes (app.core.deps), mismo patrón que el resto de
P5. La autorización fina (esta Venta es del Cliente que pide, o de la
sucursal del Cajero que pide) vive en service.py -- este router solo decide
QUIÉN puede llamar, no CUÁL Venta.

Rutas REST bajo "/comprobantes", prefijo propio -- nunca anidado bajo
"/ventas-presenciales" ni ningún otro recurso existente: un comprobante es
una PROYECCIÓN de una Venta ya pagada, no una acción sobre CU22/23/24/25 (que
no se modifican, ver __init__.py). `venta_id` es siempre el id interno
(consistente con el resto de P5 -- CU25/CU26 también reciben `venta_id`, no
`codigo_venta`, en sus rutas).

Preparado para que CU27 (fuera de este alcance) reutilice GET
/comprobantes/{venta_id} tal cual para su propio detalle -- por eso el
contrato de salida (ComprobanteVentaOut) no depende de nada específico de
esta pantalla.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import ComprobanteVentaOut, EnviarComprobanteOut
from .service import (
    ClienteSinCorreoError,
    ComprobanteVentaService,
    PagoNoEncontradoError,
    VentaNoEncontradaError,
    VentaSinComprobanteError,
)

require_cliente_o_cajero = require_roles(RolUsuario.CLIENTE, RolUsuario.CAJERO)

router = APIRouter(prefix="/comprobantes", tags=["CU31 - Emitir comprobante de venta"])

_MSG_VENTA_NO_ENCONTRADA = "Venta no encontrada."
_MSG_SIN_COMPROBANTE = "Esta venta todavía no tiene un comprobante disponible."
_MSG_PAGO_NO_ENCONTRADO = "Esta venta no tiene un pago confirmado registrado."
_MSG_SIN_CLIENTE = "Esta venta no tiene un cliente registrado al cual enviarle el comprobante."


@router.get("/{venta_id}", response_model=ComprobanteVentaOut)
def obtener_comprobante(
    venta_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente_o_cajero),
) -> ComprobanteVentaOut:
    try:
        return ComprobanteVentaService(db).obtener_comprobante(actor, venta_id)
    except VentaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_VENTA_NO_ENCONTRADA) from exc
    except VentaSinComprobanteError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SIN_COMPROBANTE) from exc
    except PagoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_PAGO_NO_ENCONTRADO) from exc


@router.get("/{venta_id}/pdf")
def descargar_comprobante_pdf(
    venta_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente_o_cajero),
) -> Response:
    try:
        codigo_venta, pdf_bytes = ComprobanteVentaService(db).generar_pdf(actor, venta_id)
    except VentaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_VENTA_NO_ENCONTRADA) from exc
    except VentaSinComprobanteError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SIN_COMPROBANTE) from exc
    except PagoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_PAGO_NO_ENCONTRADO) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{codigo_venta}.pdf"'},
    )


@router.post("/{venta_id}/enviar", response_model=EnviarComprobanteOut)
def enviar_comprobante(
    venta_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente_o_cajero),
) -> EnviarComprobanteOut:
    try:
        return ComprobanteVentaService(db).enviar_comprobante(actor, venta_id)
    except VentaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_VENTA_NO_ENCONTRADA) from exc
    except VentaSinComprobanteError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SIN_COMPROBANTE) from exc
    except PagoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_PAGO_NO_ENCONTRADO) from exc
    except ClienteSinCorreoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SIN_CLIENTE) from exc
