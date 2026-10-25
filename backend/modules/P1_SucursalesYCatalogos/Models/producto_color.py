"""Tabla de asociación Producto <-> Color (muchos a muchos), para CU08.

Vincula el producto con los colores que ofrece, reutilizando los colores ya
existentes de CU09 (no los duplica).

Multitenant: Usa FK compuesta para garantizar que:
  - Producto.empresa_id == Color.empresa_id
No permite asociar productos de Empresa A con colores de Empresa B.
"""

from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Table

from app.db.base import Base

producto_colores = Table(
    "producto_colores",
    Base.metadata,
    Column("producto_id", ForeignKey("productos.id"), primary_key=True),
    Column("empresa_id", ForeignKey("empresas.id"), primary_key=True),
    Column("color_id", primary_key=False),
    ForeignKeyConstraint(
        ["empresa_id", "color_id"],
        ["colores.empresa_id", "colores.id"],
        name="fk_producto_colores_color_compuesto"
    ),
)
