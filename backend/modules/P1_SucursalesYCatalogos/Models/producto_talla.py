"""Tabla de asociación Producto <-> Talla (muchos a muchos), para CU08.

Vincula el producto con las tallas que ofrece, reutilizando las tallas ya
existentes de CU09 (no las duplica).

Multitenant: Usa FK compuesta para garantizar que:
  - Producto.empresa_id == Talla.empresa_id
No permite asociar productos de Empresa A con tallas de Empresa B.
"""

from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Table

from app.db.base import Base

producto_tallas = Table(
    "producto_tallas",
    Base.metadata,
    Column("producto_id", ForeignKey("productos.id"), primary_key=True),
    Column("empresa_id", ForeignKey("empresas.id"), primary_key=True),
    Column("talla_id", primary_key=False),
    ForeignKeyConstraint(
        ["empresa_id", "talla_id"],
        ["tallas.empresa_id", "tallas.id"],
        name="fk_producto_tallas_talla_compuesto"
    ),
)
