"""Entidad Producto, compartida por el paquete P1 -- Sucursales y catálogo.

CU08 (gestionar productos) es el primer consumidor. Es el producto ya
publicado en el catálogo de FashionStore, con precio de venta propio --
distinto de ProductoProveedor (la propuesta que envía el proveedor, sin
precio ni datos comerciales). Un Producto puede originarse de una propuesta
enviada por un proveedor (producto_proveedor_id) sin duplicar sus datos.

precio_venta es único por producto, no por sucursal: el mismo precio aplica
en todas las sucursales de FashionStore (ver CU08).

tallas/colores son el catálogo de opciones que ofrece el producto (CU09,
reutilizado); variantes es cada combinación talla+color generada a partir de
esas opciones, sin stock todavía.

imagen_principal_url es la única imagen obligatoria del producto (distinta de
las adicionales en `imagenes`); se sube mediante un endpoint dedicado -- ver
app/core/image_storage.py -- por eso es nullable a nivel de base de datos
(un producto recién creado aún no tiene ninguna imagen cargada).
"""

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .categoria import Categoria
from .coleccion import Coleccion
from .color import Color
from .producto_color import producto_colores
from .producto_imagen import ProductoImagen
from .producto_talla import producto_tallas
from .producto_variante import ProductoVariante
from .proveedor import Proveedor
from .talla import Talla
from .temporada import Temporada


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)

    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), nullable=False)
    producto_proveedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("productos_proveedor.id"), unique=True, nullable=True
    )
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"), nullable=False)
    temporada_id: Mapped[int] = mapped_column(ForeignKey("temporadas.id"), nullable=False)
    coleccion_id: Mapped[int] = mapped_column(ForeignKey("colecciones.id"), nullable=False)

    precio_venta: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    imagen_principal_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    proveedor: Mapped[Proveedor] = relationship(lazy="joined")
    categoria: Mapped[Categoria] = relationship(lazy="joined")
    temporada: Mapped[Temporada] = relationship(lazy="joined")
    coleccion: Mapped[Coleccion] = relationship(lazy="joined")

    tallas: Mapped[list[Talla]] = relationship(
        secondary=producto_tallas, order_by=Talla.nombre, lazy="selectin"
    )
    colores: Mapped[list[Color]] = relationship(
        secondary=producto_colores, order_by=Color.nombre, lazy="selectin"
    )

    variantes: Mapped[list[ProductoVariante]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by=ProductoVariante.id
    )
    imagenes: Mapped[list[ProductoImagen]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by=ProductoImagen.orden
    )
