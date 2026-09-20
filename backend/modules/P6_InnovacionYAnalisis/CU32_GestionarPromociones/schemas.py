"""Contratos de entrada/salida de CU32 -- Gestionar promociones (Administrador).

JSON limpio, sin nada específico de Angular -- preparado para que Flutter lo
reutilice después (aunque la gestión en sí sea exclusivamente web/ADMIN, ver
__init__.py). Angular nunca calcula el descuento ni decide el estado: ambos
siempre vienen ya resueltos por FastAPI.

Campos monetarios/porcentuales como `float`, NUNCA `Decimal` -- mismo motivo
ya documentado en CU21/CU22/CU24/CU26/CU27/CU31 (Pydantic v2 serializa
`Decimal` como STRING por defecto).
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductoPromocionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    imagen_principal_url: str | None


class PromocionListadoOut(BaseModel):
    """Una fila del listado -- SIN la lista completa de productos (ver
    __init__.py: "no llenar las tarjetas con la lista completa de
    productos"), solo la cantidad. El detalle completo vive en
    PromocionDetalleOut (VER/EDITAR)."""

    id: int
    nombre: str
    porcentaje_descuento: float
    fecha_inicio: date
    fecha_fin: date
    estado: str
    cantidad_productos: int
    fecha_creacion: datetime


class PromocionDetalleOut(BaseModel):
    id: int
    nombre: str
    porcentaje_descuento: float
    fecha_inicio: date
    fecha_fin: date
    estado: str
    activa: bool
    fecha_creacion: datetime
    productos: list[ProductoPromocionOut]


class CrearPromocionRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    porcentaje_descuento: float = Field(gt=0, lt=100)
    fecha_inicio: date
    fecha_fin: date
    producto_ids: list[int] = Field(min_length=1)


class EditarPromocionRequest(CrearPromocionRequest):
    """Mismos campos que crear -- una edición reemplaza nombre, porcentaje,
    vigencia y la lista completa de productos (nunca un PATCH parcial, ver
    service.py: no permitir una promoción sin productos aplica igual aquí)."""
