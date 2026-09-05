"""Entidad ProductoVariante -- combinación talla + color de un Producto (CU08).

Representa cada combinación válida de talla y color que ofrece el producto
(ej. Negro/S, Negro/M...). Se genera automáticamente a partir de las tallas y
colores elegidos para el producto -- el Administrador no la crea a mano.

NO guarda stock: queda preparada para que un CU futuro relacione
Sucursal + ProductoVariante + Cantidad, pero eso no es parte de CU08.
"""

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .color import Color
from .talla import Talla


class ProductoVariante(Base):
    __tablename__ = "producto_variantes"
    __table_args__ = (UniqueConstraint("producto_id", "talla_id", "color_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), nullable=False)
    talla_id: Mapped[int] = mapped_column(ForeignKey("tallas.id"), nullable=False)
    color_id: Mapped[int] = mapped_column(ForeignKey("colores.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    talla: Mapped[Talla] = relationship(lazy="joined")
    color: Mapped[Color] = relationship(lazy="joined")
