"""Entidad Categoría, compartida por todo el paquete P1 — Sucursales y catálogo.

CU09 (gestionar categorías, tallas y colores) es el primer consumidor.

Multitenant: cada categoría pertenece a una empresa. Diferentes empresas pueden
tener categorías con el mismo nombre sin conflicto.

imagen_url es opcional (una categoría puede no tener imagen todavía); se sube
mediante un endpoint dedicado -- ver app/core/image_storage.py.
"""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa


class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_categoria_empresa_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    empresa: Mapped[Empresa] = relationship(lazy="joined")
