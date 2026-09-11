"""Entidad Colección, compartida por todo el paquete P1 — Sucursales y catálogo.

CU10 (gestionar temporadas y colecciones) es el primer consumidor. Una
colección pertenece a una única temporada (Temporada 1 ---- N Colección) y es
global — no se crean colecciones por sucursal.
"""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .temporada import Temporada


class Coleccion(Base):
    __tablename__ = "colecciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    temporada_id: Mapped[int] = mapped_column(ForeignKey("temporadas.id"), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Colección destacada del Home (CU10): a lo sumo una fila la tiene en True
    # -- ver el índice único parcial en la migración y ColeccionesRepository.
    es_destacada_inicio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    imagen_destacada_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    temporada: Mapped[Temporada] = relationship(lazy="joined")
