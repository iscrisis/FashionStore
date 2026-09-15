"""Entidad ProductoProveedor, compartida por el paquete P1 — Sucursales y catálogo.

Es la propuesta que un PROVEEDOR envía a FashionStore — NO es un producto
publicado en el catálogo (eso es CU08). Por eso no tiene precio, categoría,
temporada, colección, tallas ni colores: esas son decisiones internas de
FashionStore que el Administrador completa recién al convertir la propuesta
en un Producto real (ver CU08_GestionarProductos.service._validar_propuesta).
"disponibilidad" es una declaración del proveedor, no inventario.

estado es la decisión del Administrador sobre esta propuesta -- PENDIENTE
(recién enviada, todavía sin revisar), APROBADO (convertida en un Producto
real) o RECHAZADO (el Administrador decidió no incorporarla; nunca se borra
físicamente, el proveedor conserva su historial). Se fija a APROBADO en el
mismo commit que crea el Producto vinculado (ver CU08 service.crear/
actualizar), nunca de forma independiente -- así nunca queda un Producto sin
su propuesta marcada, ni viceversa.

imagen_url es solo una referencia visual de la propuesta (para que el
Administrador vea qué le están ofreciendo) -- no es la imagen del catálogo:
esa la sube el Administrador por separado al convertir (Producto.imagen_principal_url).
Reutiliza el mismo almacenamiento de imágenes que CU08/CU09 (ver
app/core/image_storage.py), en su propia subcarpeta.

temporada_id/coleccion_id existieron en una versión anterior de este modelo;
se retiraron (ver la migración que quita estas columnas) porque nunca las
usaba CU08 al convertir -- el Administrador siempre elige la temporada y
colección reales desde cero en ese paso.
"""

import enum

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EstadoProductoProveedor(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


class ProductoProveedor(Base):
    __tablename__ = "productos_proveedor"

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    disponibilidad: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    estado: Mapped[EstadoProductoProveedor] = mapped_column(
        SAEnum(EstadoProductoProveedor, name="estado_producto_proveedor"),
        nullable=False,
        default=EstadoProductoProveedor.PENDIENTE,
    )
