"""Endpoints de CU25 -- Procesar pago presencial (Cajero).

Requiere un CAJERO autenticado. Reutiliza get_current_usuario/require_roles
ya existentes (app.core.deps). La sucursal autorizada se deriva SIEMPRE de
`actor.sucursal_id` (mismo helper `_sucursal_id_del_actor` que ya define
cada router de CU14/CU15/CU16/CU20/CU24 -- se repite aquí en vez de
importarlo, mismo criterio ya documentado en esos módulos).

Rutas REST bajo "/pagos-presenciales" -- prefijo propio, distinto de
"/pagos" (CU23, exclusivo de Cliente/Stripe) y de "/ventas-presenciales"
(CU24): confirmar un pago es una acción sobre una Venta ya creada, no un
alias de ninguno de esos dos recursos.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import ConfirmarPagoRequest, PagoConfirmadoOut
from .service import (
    MontoRecibidoInsuficienteError,
    PagoPresencialService,
    StockInsuficienteError,
    SucursalCajeroNoDefinidaError,
    VentaNoEncontradaError,
    VentaNoPagableError,
    VentaYaPagadaError,
)

require_cajero = require_roles(RolUsuario.CAJERO)

router = APIRouter(prefix="/pagos-presenciales", tags=["CU25 - Procesar pago presencial"])

_MSG_SIN_SUCURSAL = "Tu usuario no está vinculado a ninguna sucursal."


@router.post("/{venta_id}/confirmar", response_model=PagoConfirmadoOut, status_code=status.HTTP_201_CREATED)
def confirmar_pago(
    venta_id: int,
    payload: ConfirmarPagoRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cajero),
) -> PagoConfirmadoOut:
    try:
        return PagoPresencialService(db).confirmar_pago(actor, venta_id, payload)
    except SucursalCajeroNoDefinidaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _MSG_SIN_SUCURSAL) from exc
    except VentaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta no encontrada.") from exc
    except VentaYaPagadaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Esta venta ya fue pagada.") from exc
    except VentaNoPagableError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Esta venta no admite un pago en este momento."
        ) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Ya no hay disponibilidad suficiente para completar esta venta.",
        ) from exc
    except MontoRecibidoInsuficienteError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "El monto recibido es menor al total."
        ) from exc
