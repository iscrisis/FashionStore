"""Entidad Temporada, compartida por todo el paquete P1 — Sucursales y catálogo.

CU10 (gestionar temporadas y colecciones) es el primer consumidor. Es global
(no pertenece a una sucursal): Temporada 1 ---- N Colección.
"""

from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Temporada(Base):
    __tablename__ = "temporadas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
