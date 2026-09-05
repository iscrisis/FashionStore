"""Contratos de entrada/salida de CU10 — Gestionar temporadas y colecciones."""

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class TemporadaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    is_active: bool


class _TemporadaDatosBase(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 1:
            raise ValueError("El nombre de la temporada es obligatorio.")
        if len(limpio) > 120:
            raise ValueError("El nombre no puede superar los 120 caracteres.")
        return limpio

    @model_validator(mode="after")
    def _validar_rango_fechas(self) -> "_TemporadaDatosBase":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio.")
        return self


class TemporadaCrear(_TemporadaDatosBase):
    is_active: bool = True


class TemporadaActualizar(_TemporadaDatosBase):
    pass


class ColeccionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None
    is_active: bool
    temporada: TemporadaOut


class _ColeccionDatosBase(BaseModel):
    nombre: str
    temporada_id: int
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 1:
            raise ValueError("El nombre de la colección es obligatorio.")
        if len(limpio) > 120:
            raise ValueError("El nombre no puede superar los 120 caracteres.")
        return limpio

    @field_validator("descripcion")
    @classmethod
    def _validar_descripcion(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        if len(limpio) > 255:
            raise ValueError("La descripción no puede superar los 255 caracteres.")
        return limpio or None


class ColeccionCrear(_ColeccionDatosBase):
    is_active: bool = True


class ColeccionActualizar(_ColeccionDatosBase):
    pass


class CambiarEstadoRequest(BaseModel):
    is_active: bool
