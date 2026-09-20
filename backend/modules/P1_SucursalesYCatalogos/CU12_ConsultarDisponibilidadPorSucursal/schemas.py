"""Contratos de salida de CU12 -- Consultar disponibilidad por sucursal (público).

JSON limpio, sin HTML ni nada específico de Angular -- preparado para que
Flutter lo consuma igual más adelante:

    producto_id
    disponibilidad
      - sucursal (+ ciudad)
      - variantes (talla + color + cantidad)

"cantidad" es lo REALMENTE disponible para reservar/comprar -- stock físico
(el que escribe el Encargado, ver CU14_ConsultarInventario) menos lo ya
comprometido por reservas PENDIENTES (StockSucursal.stock_reservado, ver
CU17_CrearReservaPrendas), nunca el físico crudo (ver repository.py
cantidades_por_variantes). El cliente decide cómo mostrar
"Disponible"/"Agotado" a partir de ese número -- el backend no inventa ese
texto, pero si sigue enviando el físico sin descontar, el Cliente vería como
"Disponible" una unidad que otro Cliente ya reservó.

"producto_variante_id" se agrega para CU17 (crear reserva de prendas): el
Cliente necesita el id real de la variante para poder reservarla, no solo su
talla/color legibles. Es un campo aditivo -- ya se resolvía internamente en
el repository, solo faltaba exponerlo en la salida -- no cambia el resto del
contrato ni la lógica de disponibilidad.
"""

from pydantic import BaseModel


class VarianteDisponibleOut(BaseModel):
    producto_variante_id: int
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
