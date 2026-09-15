"""Contratos de salida de CU12 -- Consultar disponibilidad por sucursal (público).

JSON limpio, sin HTML ni nada específico de Angular -- preparado para que
Flutter lo consuma igual más adelante:

    producto_id
    disponibilidad
      - sucursal (+ ciudad)
      - variantes (talla + color + cantidad)

"cantidad" es el dato real que ya escribe el Encargado (ver
CU14_ConsultarInventario); el cliente decide cómo mostrar "Disponible"/"Agotado"
a partir de ese número -- el backend no inventa ese texto.
"""

from pydantic import BaseModel


class VarianteDisponibleOut(BaseModel):
    talla_id: int
    talla: str
    color_id: int
    color: str
    cantidad: int


class DisponibilidadSucursalOut(BaseModel):
    sucursal_id: int
    sucursal: str
    ciudad_id: int
    ciudad: str
    variantes: list[VarianteDisponibleOut]


class ProductoDisponibilidadOut(BaseModel):
    producto_id: int
    disponibilidad: list[DisponibilidadSucursalOut]
