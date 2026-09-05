"""Contratos de salida de CU07 -- Consultar sucursales (público).

Público y de solo lectura: sin "departamento" ni "is_active" (campos
administrativos de CU06) -- el flujo público es únicamente Ciudad ->
Sucursal, y solo se listan sucursales/ciudades ya activas, así que repetir el
estado en cada fila sería redundante. Da forma a la versión pública de los
mismos datos que ya administra CU06 -- no los duplica.
"""

from pydantic import BaseModel, ConfigDict


class CiudadPublicaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class SucursalPublicaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    direccion: str
    telefono: str
    ciudad: CiudadPublicaOut
