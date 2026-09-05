"""Entidad Ciudad, compartida por todo el paquete P1 — Sucursales y catálogo.

CU06 (gestionar sucursales) es el primer consumidor: cada sucursal pertenece a
una ciudad. Se mantiene deliberadamente mínima (id, nombre, departamento,
is_active) porque CU06 no requiere provincia, coordenadas ni mapas.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Ciudad(Base):
    __tablename__ = "ciudades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    departamento: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
