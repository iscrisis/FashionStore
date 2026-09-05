"""Tabla de asociación Producto <-> Color (muchos a muchos), para CU08.

Vincula el producto con los colores que ofrece, reutilizando los colores ya
existentes de CU09 (no los duplica). Es una tabla `secondary` pura -- sin
datos propios --, por eso no tiene una clase de modelo dedicada; la
combinación talla + color con datos propios es ProductoVariante.
"""

from sqlalchemy import Column, ForeignKey, Table

from app.db.base import Base

producto_colores = Table(
    "producto_colores",
    Base.metadata,
    Column("producto_id", ForeignKey("productos.id"), primary_key=True),
    Column("color_id", ForeignKey("colores.id"), primary_key=True),
)
