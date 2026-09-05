"""Tabla de asociación Producto <-> Talla (muchos a muchos), para CU08.

Vincula el producto con las tallas que ofrece, reutilizando las tallas ya
existentes de CU09 (no las duplica). Es una tabla `secondary` pura -- sin
datos propios --, por eso no tiene una clase de modelo dedicada; la
combinación talla + color con datos propios es ProductoVariante.
"""

from sqlalchemy import Column, ForeignKey, Table

from app.db.base import Base

producto_tallas = Table(
    "producto_tallas",
    Base.metadata,
    Column("producto_id", ForeignKey("productos.id"), primary_key=True),
    Column("talla_id", ForeignKey("tallas.id"), primary_key=True),
)
