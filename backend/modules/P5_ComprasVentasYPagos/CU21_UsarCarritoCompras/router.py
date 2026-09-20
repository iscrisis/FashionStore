"""Endpoints de CU21 -- Usar carrito de compras (Cliente).

Requiere un CLIENTE autenticado. Reutiliza get_current_usuario / require_roles
ya existentes (app.core.deps) -- no crea un JWT ni un AuthService nuevo.
cliente_id sale SIEMPRE de `actor` (el usuario autenticado), nunca de la URL,
query ni body: un Cliente jamás puede consultar, modificar ni eliminar el
carrito de otro manipulando un id.

Rutas REST bajo "/carrito", mismo criterio ya usado por CU17
(POST /reservas, GET /reservas/mias) y CU17-agregar-detalle
(POST /reservas/{id}/detalles): el recurso (Carrito) es siempre el del
Cliente autenticado -- nunca se referencia por su propio id en la URL,
"/carrito" ya significa "el mío".

La API es JSON puro -- preparada para que Flutter la use más adelante, igual
que el resto del proyecto.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import ActualizarSeleccionRequest, AgregarItemRequest, CarritoOut
from .service import (
    CarritoService,
    ItemNoEncontradoError,
    StockInsuficienteError,
    VarianteNoEncontradaError,
)

require_cliente = require_roles(RolUsuario.CLIENTE)

router = APIRouter(prefix="/carrito", tags=["CU21 - Usar carrito de compras"])


@router.get("", response_model=CarritoOut)
def consultar_carrito(
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> CarritoOut:
    return CarritoService(db).consultar(actor.id)


@router.post("/items", response_model=CarritoOut, status_code=status.HTTP_201_CREATED)
def agregar_item(
    payload: AgregarItemRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> CarritoOut:
    try:
        return CarritoService(db).agregar_item(actor.id, payload)
    except VarianteNoEncontradaError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "La variante indicada no existe o no está disponible.",
        ) from exc
    except StockInsuficienteError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "No hay disponibilidad suficiente para esa cantidad.",
        ) from exc


@router.patch("/items/{item_id}", response_model=CarritoOut)
def actualizar_seleccion(
    item_id: int,
    payload: ActualizarSeleccionRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> CarritoOut:
    try:
        return CarritoService(db).actualizar_seleccion(actor.id, item_id, payload)
    except ItemNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado en el carrito.") from exc


@router.delete("/items/{item_id}", response_model=CarritoOut)
def eliminar_item(
    item_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_cliente),
) -> CarritoOut:
    try:
        return CarritoService(db).eliminar_item(actor.id, item_id)
    except ItemNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado en el carrito.") from exc
