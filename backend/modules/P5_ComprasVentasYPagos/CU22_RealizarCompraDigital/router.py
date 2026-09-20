"""Endpoints de CU22 -- Realizar compra digital (Cliente).

Requiere un CLIENTE autenticado. Reutiliza get_current_usuario / require_roles
ya existentes (app.core.deps) -- no crea un JWT ni un AuthService nuevo.
cliente_id sale SIEMPRE de `actor` (el usuario autenticado), nunca de la URL,
query ni body: un Cliente jamás puede usar el carrito de otro (ver
service.py: los items se leen SIEMPRE del carrito propio, nunca por id
recibido desde Angular).

Rutas REST bajo "/compra-digital", mismo criterio ya usado por CU17/CU21: el
recurso es siempre el del Cliente autenticado.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import ConfirmarCompraRequest, ResumenCompraOut, SucursalCompraOut, VentaOut
from .service import (
    CompraDigitalService,
    ProductoNoDisponibleError,
    SinItemsSeleccionadosError,
    SucursalNoDisponibleError,
    SucursalNoEncontradaError,
)

require_cliente = require_roles(RolUsuario.CLIENTE)

router = APIRouter(prefix="/compra-digital", tags=["CU22 - Realizar compra digital"])

_MSG_SIN_SELECCION = "No hay prendas seleccionadas. Vuelve al carrito y selecciona al menos una."


@router.get("/resumen", response_model=ResumenCompraOut)
def obtener_resumen(
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> ResumenCompraOut:
    try:
        return CompraDigitalService(db).resumen(actor.id)
    except SinItemsSeleccionadosError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SIN_SELECCION) from exc


@router.get("/sucursales", response_model=list[SucursalCompraOut])
def listar_sucursales_disponibles(
    ciudad_id: int = Query(...),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> list[SucursalCompraOut]:
    try:
        return CompraDigitalService(db).sucursales_disponibles(actor.id, ciudad_id)
    except SinItemsSeleccionadosError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SIN_SELECCION) from exc


@router.post("", response_model=VentaOut, status_code=status.HTTP_201_CREATED)
def confirmar_compra(
    payload: ConfirmarCompraRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> VentaOut:
    try:
        return CompraDigitalService(db).confirmar(actor.id, payload.sucursal_id)
    except SinItemsSeleccionadosError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _MSG_SIN_SELECCION) from exc
    except SucursalNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La sucursal indicada no existe o no está activa."
        ) from exc
    except SucursalNoDisponibleError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Esa sucursal ya no tiene disponibilidad para todas las prendas seleccionadas.",
        ) from exc
    except ProductoNoDisponibleError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Una de las prendas seleccionadas ya no está disponible. Vuelve al carrito.",
        ) from exc
