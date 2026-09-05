"""Entidad ProductoProveedor, compartida por el paquete P1 — Sucursales y catálogo.

Es la propuesta/información de una prenda que un PROVEEDOR ofrece a
FashionStore — NO es un producto publicado en el catálogo (eso es CU08,
todavía no implementado). Por eso no tiene precio de venta ni stock por
sucursal: "disponibilidad" es una declaración del proveedor, no inventario.

Referencia Temporada y Colección (CU10) y Proveedor (GestionProveedores) sin
duplicarlos.
"""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .coleccion import Coleccion
from .temporada import Temporada


class ProductoProveedor(Base):
    __tablename__ = "productos_proveedor"

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    temporada_id: Mapped[int] = mapped_column(ForeignKey("temporadas.id"), nullable=False)
    coleccion_id: Mapped[int] = mapped_column(ForeignKey("colecciones.id"), nullable=False)
    disponibilidad: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    temporada: Mapped[Temporada] = relationship(lazy="joined")
    coleccion: Mapped[Coleccion] = relationship(lazy="joined")
