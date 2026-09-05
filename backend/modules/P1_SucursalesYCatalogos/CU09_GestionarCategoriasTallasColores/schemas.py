"""Contratos de entrada/salida de CU09 — Gestionar categorías, tallas y colores.

Categoría, Talla y Color comparten exactamente la misma forma (nombre, estado),
así que reutilizan los mismos esquemas — igual que CambiarEstadoRequest ya se
reutiliza para más de una entidad en CU06.
"""

from pydantic import BaseModel, ConfigDict, field_validator


class ItemCatalogoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    is_active: bool


class CategoriaOut(BaseModel):
    """Igual que ItemCatalogoOut, pero solo Categoría tiene imagen -- Talla y
    Color siguen usando ItemCatalogoOut sin cambios."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    imagen_url: str | None
    is_active: bool


class ItemCatalogoCrear(BaseModel):
    nombre: str
    is_active: bool = True

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 1:
            raise ValueError("El nombre es obligatorio.")
        if len(limpio) > 80:
            raise ValueError("El nombre no puede superar los 80 caracteres.")
        return limpio


class ItemCatalogoActualizar(BaseModel):
    nombre: str

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 1:
            raise ValueError("El nombre es obligatorio.")
        if len(limpio) > 80:
            raise ValueError("El nombre no puede superar los 80 caracteres.")
        return limpio


class CambiarEstadoRequest(BaseModel):
    is_active: bool
