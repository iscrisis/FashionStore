"""Entidad Categoría, compartida por todo el paquete P1 — Sucursales y catálogo.

CU09 (gestionar categorías, tallas y colores) es el primer consumidor. Es un
catálogo global (no pertenece a una sucursal): CU08 (crear productos) la
reutilizará más adelante, sin duplicarla.

imagen_url es opcional (una categoría puede no tener imagen todavía); se sube
mediante un endpoint dedicado -- ver app/core/image_storage.py -- y se
reutilizará más adelante en una sección pública tipo "Compra por categorías"
(no implementada todavía).
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
