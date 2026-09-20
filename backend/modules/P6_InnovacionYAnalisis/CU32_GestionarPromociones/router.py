"""Endpoints de CU32 -- Gestionar promociones (Administrador).

Requiere un ADMINISTRADOR autenticado -- reutiliza get_current_usuario/
require_roles ya existentes (app.core.deps), mismo patrón que el resto del
proyecto. El Cliente y el Cajero NUNCA llegan a este router: solo consultan,
indirectamente, el precio ya resuelto a través de catálogo/carrito/compra/
venta presencial (ver precio_efectivo.py) -- ninguno de esos endpoints exige
rol ADMINISTRADOR.

Rutas REST bajo "/promociones", prefijo propio. Sin DELETE físico -- ver
service.py: "desactivar" es la única baja posible.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import CrearPromocionRequest, EditarPromocionRequest, PromocionDetalleOut, PromocionListadoOut
from .service import (
    PromocionNoEditableError,
    PromocionNoEncontradaError,
    PromocionService,
    ProductoNoEncontradoError,
    RangoFechaInvalidoError,
    SolapamientoError,
)

require_administrador = require_roles(RolUsuario.ADMINISTRADOR)

router = APIRouter(prefix="/promociones", tags=["CU32 - Gestionar promociones"])

_MSG_NO_ENCONTRADA = "Promoción no encontrada."
_MSG_RANGO_INVALIDO = 'La fecha "fin" no puede ser anterior a la fecha "inicio".'
_MSG_PRODUCTO_NO_ENCONTRADO = "Alguno de los productos seleccionados no existe o no está activo."
_MSG_SOLAPAMIENTO = "Uno de los productos ya tiene otra promoción vigente en ese rango de fechas."
_MSG_NO_EDITABLE = "Esta promoción ya finalizó o está desactivada -- no se puede editar."


@router.get("", response_model=list[PromocionListadoOut])
def listar_promociones(
    db: Session = Depends(get_db), actor: Usuario = Depends(require_administrador)
) -> list[PromocionListadoOut]:
    return PromocionService(db).listar()


@router.get("/{promocion_id}", response_model=PromocionDetalleOut)
def obtener_promocion(
    promocion_id: int, db: Session = Depends(get_db), actor: Usuario = Depends(require_administrador)
) -> PromocionDetalleOut:
    try:
        return PromocionService(db).obtener(promocion_id)
    except PromocionNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_NO_ENCONTRADA) from exc


@router.post("", response_model=PromocionDetalleOut, status_code=status.HTTP_201_CREATED)
def crear_promocion(
    payload: CrearPromocionRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_administrador),
) -> PromocionDetalleOut:
    try:
        return PromocionService(db).crear(payload)
    except RangoFechaInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_RANGO_INVALIDO) from exc
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_PRODUCTO_NO_ENCONTRADO) from exc
    except SolapamientoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SOLAPAMIENTO) from exc


@router.put("/{promocion_id}", response_model=PromocionDetalleOut)
def editar_promocion(
    promocion_id: int,
    payload: EditarPromocionRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_administrador),
) -> PromocionDetalleOut:
    try:
        return PromocionService(db).editar(promocion_id, payload)
    except PromocionNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_NO_ENCONTRADA) from exc
    except PromocionNoEditableError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_NO_EDITABLE) from exc
    except RangoFechaInvalidoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_RANGO_INVALIDO) from exc
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_PRODUCTO_NO_ENCONTRADO) from exc
    except SolapamientoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SOLAPAMIENTO) from exc


@router.patch("/{promocion_id}/desactivar", response_model=PromocionDetalleOut)
def desactivar_promocion(
    promocion_id: int, db: Session = Depends(get_db), actor: Usuario = Depends(require_administrador)
) -> PromocionDetalleOut:
    try:
        return PromocionService(db).desactivar(promocion_id)
    except PromocionNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _MSG_NO_ENCONTRADA) from exc
