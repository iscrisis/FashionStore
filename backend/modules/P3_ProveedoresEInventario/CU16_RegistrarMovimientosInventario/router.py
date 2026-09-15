"""Endpoints de CU16 -- Registrar movimientos de inventario (Panel del Encargado de Sucursal).

Requiere un ENCARGADO_SUCURSAL autenticado. Reutiliza get_current_usuario /
require_roles ya existentes (app.core.deps) -- no crea un JWT ni un
AuthService nuevo. La sucursal autorizada se deriva SIEMPRE de
usuario.sucursal_id (nunca de un id recibido del cliente), mismo patrón que
ya usan CU14 y CU15: un Encargado no puede ajustar ni consultar el
inventario de otra sucursal manipulando la URL, el body o cualquier
parámetro.

La API es JSON puro -- preparada para que Flutter la use más adelante,
aunque este panel es solo para Angular Web.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import MovimientoOut, ProductoConVariantesOut, RegistrarMovimientoRequest
from .service import MovimientosInventarioService, StockInsuficienteError, VarianteNoEncontradaError

require_encargado = require_roles(RolUsuario.ENCARGADO_SUCURSAL)

router_panel = APIRouter(
    prefix="/movimientos-inventario/panel", tags=["CU16 - Registrar movimientos de inventario"]
)


def _sucursal_id_del_actor(actor: Usuario) -> int:
    if actor.sucursal_id is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Esta cuenta no está vinculada a ninguna sucursal."
        )
    return actor.sucursal_id


@router_panel.get("/productos", response_model=list[ProductoConVariantesOut])
def buscar_productos(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> list[ProductoConVariantesOut]:
    sucursal_id = _sucursal_id_del_actor(actor)
    return MovimientosInventarioService(db).listar_productos(sucursal_id, search=search)


@router_panel.post("", response_model=MovimientoOut, status_code=status.HTTP_201_CREATED)
def registrar_movimiento(
    payload: RegistrarMovimientoRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> MovimientoOut:
    sucursal_id = _sucursal_id_del_actor(actor)
    try:
        return MovimientosInventarioService(db).registrar(sucursal_id, actor, payload)
    except VarianteNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "La variante indicada no existe o no está disponible.",
        ) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "No hay stock suficiente para registrar ese ajuste negativo.",
        ) from exc


@router_panel.get("/historial", response_model=list[MovimientoOut])
def listar_historial(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> list[MovimientoOut]:
    sucursal_id = _sucursal_id_del_actor(actor)
    return MovimientosInventarioService(db).listar_historial(sucursal_id, limit=limit)
