"""Entidad ProductoImagen -- imágenes asociadas a un Producto (CU08).

Guarda únicamente la URL de la imagen: el proyecto no tiene todavía ningún
mecanismo de subida de archivos ni servicio externo (Cloudinary, S3, etc.), y
CU08 no debe introducir uno. Permite más de una imagen por producto para
mostrarlas luego en catálogo web, detalle de producto y Flutter.
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProductoImagen(Base):
    __tablename__ = "producto_imagenes"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
