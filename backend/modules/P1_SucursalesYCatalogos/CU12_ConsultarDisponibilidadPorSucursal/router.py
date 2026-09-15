"""Endpoints de CU12 -- Consultar disponibilidad por sucursal.

Público: NO requiere sesión, JWT ni rol -- Invitado o Cliente lo consulta sin
iniciar sesión, igual que CU07 y CU11. Es de solo lectura: no administra
stock -- crear/modificar cantidades sigue siendo exclusivo del Encargado (ver
CU14_ConsultarInventario). Cruza datos ya existentes de CU08 (Producto,
ProductoVariante), CU06 (Sucursal) y StockSucursal; no crea ninguna tabla
nueva.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from .schemas import ProductoDisponibilidadOut
from .service import DisponibilidadService, ProductoNoEncontradoError

router = APIRouter(prefix="/disponibilidad", tags=["CU12 - Consultar disponibilidad por sucursal"])


@router.get("", response_model=ProductoDisponibilidadOut)
def consultar_disponibilidad(
    producto_id: int = Query(...),
    ciudad_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProductoDisponibilidadOut:
    try:
        return DisponibilidadService(db).consultar_por_producto(producto_id, ciudad_id)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.") from exc
