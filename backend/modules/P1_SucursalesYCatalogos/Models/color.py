"""Entidad Color, compartida por todo el paquete P1 — Sucursales y catálogo.

CU09 (gestionar categorías, tallas y colores) es el primer consumidor. Es un
catálogo global (no pertenece a una sucursal). Solo nombre — sin código hex,
sin orden de despliegue: CU09 no los necesita.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Color(Base):
    __tablename__ = "colores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
