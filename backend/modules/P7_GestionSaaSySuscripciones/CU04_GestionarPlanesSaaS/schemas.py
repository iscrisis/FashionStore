"""Schemas de CU04 — Gestionar planes SaaS.

Request/Response DTOs para la gestión de planes.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class PlanBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50)
    descripcion: str = Field(..., min_length=1)
    precio: Decimal = Field(..., ge=Decimal("0.00"))
    limite_sucursales: int = Field(..., ge=1)
    limite_usuarios: int = Field(..., ge=1)

    # Funcionalidades
    gestion_productos: bool = True
    gestion_ventas: bool = True
    reservas: bool = True
    operacion_offline: bool = True
    reportes_convencionales: bool = True
    reportes_generativos_ia: bool = False


class PlanCrear(PlanBase):
    pass


class PlanActualizar(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=100)
    descripcion: str | None = Field(None, min_length=1)
    precio: Decimal | None = Field(None, ge=Decimal("0.00"))
    limite_sucursales: int | None = Field(None, ge=1)
    limite_usuarios: int | None = Field(None, ge=1)

    # Funcionalidades (opcionales)
    gestion_productos: bool | None = None
    gestion_ventas: bool | None = None
    reservas: bool | None = None
    operacion_offline: bool | None = None
    reportes_convencionales: bool | None = None
    reportes_generativos_ia: bool | None = None


class PlanResponse(PlanBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlanListResponse(BaseModel):
    id: int
    nombre: str
    slug: str
    descripcion: str
    precio: Decimal
    limite_sucursales: int
    limite_usuarios: int
    gestion_productos: bool
    gestion_ventas: bool
    reservas: bool
    operacion_offline: bool
    reportes_convencionales: bool
    reportes_generativos_ia: bool
    es_activo: bool

    class Config:
        from_attributes = True


class CambiarEstadoPlanRequest(BaseModel):
    is_active: bool
