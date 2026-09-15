"""Contratos de entrada/salida de Gestión de Proveedores."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

_TELEFONO_PATTERN = re.compile(r"^[0-9+\-\s()]{6,20}$")
_CORREO_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ProveedorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    razon_social: str
    nombre_contacto: str
    correo: str
    telefono: str
    is_active: bool


class _ProveedorDatosBase(BaseModel):
    razon_social: str
    nombre_contacto: str
    correo: str
    telefono: str

    @field_validator("razon_social")
    @classmethod
    def _validar_razon_social(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("La razón social debe tener al menos 2 caracteres.")
        if len(limpio) > 150:
            raise ValueError("La razón social no puede superar los 150 caracteres.")
        return limpio

    @field_validator("nombre_contacto")
    @classmethod
    def _validar_nombre_contacto(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre de contacto debe tener al menos 2 caracteres.")
        return limpio

    @field_validator("correo")
    @classmethod
    def _validar_correo(cls, valor: str) -> str:
        limpio = valor.strip().lower()
        if not _CORREO_PATTERN.match(limpio):
            raise ValueError("Ingresa un correo válido.")
        return limpio

    @field_validator("telefono")
    @classmethod
    def _validar_telefono(cls, valor: str) -> str:
        limpio = valor.strip()
        if not _TELEFONO_PATTERN.match(limpio):
            raise ValueError(
                "El teléfono solo puede contener dígitos, espacios y los símbolos + - ( )."
            )
        return limpio


class ProveedorCrear(_ProveedorDatosBase):
    is_active: bool = True


class ProveedorActualizar(_ProveedorDatosBase):
    pass


class CambiarEstadoRequest(BaseModel):
    is_active: bool


# --------------------------------------------------------------------------
# Panel propio del Proveedor
#
# El proveedor solo propone nombre/descripción/imagen de referencia/
# disponibilidad: categoría, temporada, colección, precio, tallas y colores
# son decisiones internas de FashionStore que el Administrador completa al
# convertir la propuesta en un Producto real (ver CU08). Por eso
# ProductoProveedorCrear/Actualizar ya no piden temporada_id/coleccion_id.
# --------------------------------------------------------------------------


class VariantesPorColorOut(BaseModel):
    """Variantes ya aprobadas (Producto/ProductoVariante), agrupadas por
    color para que el proveedor las vea en solo lectura -- ej. "Negro: S, M,
    L". Solo tiene sentido cuando estado == APROBADO."""

    color: str
    tallas: list[str]


class ProductoProveedorOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    imagen_url: str | None
    disponibilidad: bool
    is_active: bool
    # Decisión del Administrador sobre esta propuesta -- ver
    # modules.P1_SucursalesYCatalogos.Models.producto_proveedor.EstadoProductoProveedor.
    estado: Literal["PENDIENTE", "APROBADO", "RECHAZADO"]
    variantes: list[VariantesPorColorOut] = []


class _ProductoProveedorDatosBase(BaseModel):
    nombre: str
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre de la prenda debe tener al menos 2 caracteres.")
        if len(limpio) > 150:
            raise ValueError("El nombre no puede superar los 150 caracteres.")
        return limpio

    @field_validator("descripcion")
    @classmethod
    def _validar_descripcion(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        if len(limpio) > 500:
            raise ValueError("La descripción no puede superar los 500 caracteres.")
        return limpio or None


class ProductoProveedorCrear(_ProductoProveedorDatosBase):
    disponibilidad: bool = True


class ProductoProveedorActualizar(_ProductoProveedorDatosBase):
    pass


class DisponibilidadRequest(BaseModel):
    disponibilidad: bool
