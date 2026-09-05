"""Entidad Talla, compartida por todo el paquete P1 — Sucursales y catálogo.

CU09 (gestionar categorías, tallas y colores) es el primer consumidor. Es un
catálogo global (no pertenece a una sucursal). nombre es texto libre a
propósito (no un enum XS/S/M/L/XL): admite cualquier formato de talla que
FashionStore necesite registrar, hoy o más adelante.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Talla(Base):
    __tablename__ = "tallas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
