"""Endpoints de CU14 -- Consultar inventario (Panel del Encargado de Sucursal).

Requiere un ENCARGADO_SUCURSAL autenticado. Reutiliza get_current_usuario /
require_roles ya existentes (app.core.deps) -- no crea un JWT ni un AuthService
nuevo. La sucursal autorizada se deriva SIEMPRE de usuario.sucursal_id (nunca
de un id recibido del cliente): así un Encargado no puede leer ni modificar el
stock de otra sucursal manipulando la URL, el body o cualquier parámetro.

Deja lista la fuente real de stock (Sucursal + ProductoVariante + Cantidad)
que un futuro CU12 (Consultar disponibilidad por sucursal) consumirá en solo
lectura. La API es JSON puro -- preparada para que Flutter la use más
adelante -- aunque el móvil es únicamente para CLIENTE y este panel es solo
para Angular Web.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import ActualizarStockLoteRequest, ProductoInventarioOut, StockItem, SucursalDelEncargadoOut
from .service import StockSucursalService, SucursalNoEncontradaError, VarianteNoEncontradaError

require_encargado = require_roles(RolUsuario.ENCARGADO_SUCURSAL)

router_panel = APIRouter(prefix="/stock-sucursal/panel", tags=["CU14 - Consultar inventario"])


def _sucursal_id_del_actor(actor: Usuario) -> int:
    if actor.sucursal_id is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Esta cuenta no está vinculada a ninguna sucursal."
        )
    return actor.sucursal_id


@router_panel.get("/mi-sucursal", response_model=SucursalDelEncargadoOut)
def obtener_mi_sucursal(
    db: Session = Depends(get_db), actor: Usuario = Depends(require_encargado)
) -> SucursalDelEncargadoOut:
    try:
        return StockSucursalService(db).mi_sucursal(_sucursal_id_del_actor(actor))
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.") from exc


@router_panel.get("/productos", response_model=list[ProductoInventarioOut])
def listar_inventario(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> list[ProductoInventarioOut]:
    return StockSucursalService(db).listar_inventario(_sucursal_id_del_actor(actor), search=search)


@router_panel.put("/stock", response_model=list[StockItem])
def actualizar_stock(
    payload: ActualizarStockLoteRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_encargado),
) -> list[StockItem]:
    try:
        return StockSucursalService(db).actualizar_stock(
            _sucursal_id_del_actor(actor), payload.items
        )
    except VarianteNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Una de las variantes indicadas no existe."
        ) from exc
