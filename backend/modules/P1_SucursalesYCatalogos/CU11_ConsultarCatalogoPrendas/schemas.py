"""Contratos de salida de CU11 -- Consultar catálogo de prendas (público).

Público y de solo lectura: sin campos administrativos (proveedor,
producto_proveedor_id, is_active, etc.). Da forma a la versión pública de los
mismos datos que ya administran CU08 (productos), CU09 (categorías, tallas,
colores) y CU10 (temporadas, colecciones) -- no los duplica.

precio_venta se expone como número (float), no como texto, para que Angular y
más adelante Flutter lo consuman como un dato numérico estable.
"""

from pydantic import BaseModel, ConfigDict


class TallaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class TemporadaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColeccionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None
    temporada: TemporadaOut


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    imagen_url: str | None


class ProductoImagenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    orden: int


class ProductoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None
    precio_venta: float
    imagen_principal_url: str | None
    imagenes: list[ProductoImagenOut]
    categoria: CategoriaOut
    temporada: TemporadaOut
    coleccion: ColeccionOut
    tallas: list[TallaOut]
    colores: list[ColorOut]
