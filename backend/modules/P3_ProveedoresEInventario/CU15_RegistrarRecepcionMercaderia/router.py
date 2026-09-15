"""Endpoints de CU15 -- Registrar recepción de mercadería (Panel del Encargado de Sucursal).

Requiere un ENCARGADO_SUCURSAL autenticado. Reutiliza get_current_usuario /
require_roles ya existentes (app.core.deps) -- no crea un JWT ni un AuthService
nuevo. La sucursal autorizada se deriva SIEMPRE de usuario.sucursal_id (nunca
de un id recibido del cliente), mismo patrón que ya usa CU14: un Encargado no
puede registrar ni consultar la recepción de otra sucursal manipulando la
URL, el body o cualquier parámetro.

La API es JSON puro -- preparada para que Flutter la use más adelante, aunque
este panel es solo para Angular Web.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import ProductoParaRecepcionOut, ProveedorResumen, RecepcionOut, RegistrarRecepcionRequest
from .service import (
    ProductoNoEncontradoError,
    ProveedorInactivoError,
    ProveedorNoEncontradoError,
    RecepcionMercaderiaService,
    VarianteDuplicadaError,
    VarianteNoEncontradaError,
)

require_encargado = require_roles(RolUsuario.ENCARGADO_SUCURSAL)

router_panel = APIRouter(prefix="/recepciones-mercaderia/panel", tags=["CU15 - Registrar recepción de mercadería"])


def _sucursal_id_del_actor(actor: Usuario) -> int:
    if actor.sucursal_id is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Esta cuenta no está vinculada a ninguna sucursal."
        )
    return actor.sucursal_id


@router_panel.get("/proveedores", response_model=list[ProveedorResumen])
def listar_proveedores_disponibles(
    db: Session = Depends(get_db), actor: Usuario = Depends(require_encargado)
) -> list[ProveedorResumen]:
    _sucursal_id_del_actor(actor)
    return RecepcionMercaderiaService(db).listar_proveedores_disponibles()


@router_panel.get("/proveedores/{proveedor_id}/productos", response_model=list[ProductoParaRecepcionOut])
def listar_productos_del_proveedor(
    proveedor_id: int, db: Session = Depends(get_db), actor: Usuario = Depends(require_encargado)
) -> list[ProductoParaRecepcionOut]:
    _sucursal_id_del_actor(actor)
    try:
        return RecepcionMercaderiaService(db).listar_productos_del_proveedor(proveedor_id)
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor no encontrado.") from exc


@router_panel.post("", response_model=RecepcionOut, status_code=status.HTTP_201_CREATED)
def registrar_recepcion(
    payload: RegistrarRecepcionRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> RecepcionOut:
    sucursal_id = _sucursal_id_del_actor(actor)
    try:
        return RecepcionMercaderiaService(db).registrar(sucursal_id, actor, payload)
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "El proveedor indicado no existe."
        ) from exc
    except ProveedorInactivoError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "El proveedor indicado está inactivo."
        ) from exc
    except ProductoNoEncontradoError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Uno de los productos indicados no existe o no pertenece al proveedor seleccionado.",
        ) from exc
    except VarianteNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Una de las variantes indicadas no existe o no pertenece al producto correspondiente.",
        ) from exc
    except VarianteDuplicadaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "No puedes repetir la misma variante dentro de la misma recepción.",
        ) from exc
