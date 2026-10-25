"""Entidad Colección, compartida por todo el paquete P1 — Sucursales y catálogo.

CU10 (gestionar temporadas y colecciones) es el primer consumidor. Una
colección pertenece a una única temporada (Temporada 1 ---- N Colección) y a una única empresa.

Multitenant: cada colección pertenece a una empresa. El índice único parcial para
es_destacada debe ser por empresa (UNIQUE(empresa_id) WHERE es_destacada = true).
"""

from sqlalchemy import Boolean, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
from .temporada import Temporada


class Coleccion(Base):
    __tablename__ = "colecciones"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_coleccion_empresa_nombre"),
        ForeignKeyConstraint(
            ["empresa_id", "temporada_id"],
            ["temporadas.empresa_id", "temporadas.id"],
            name="fk_coleccion_temporada_compuesto"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    temporada_id: Mapped[int] = mapped_column(nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Colección destacada del Home (CU10): a lo sumo una por empresa
    # Requiere índice único parcial: UNIQUE(empresa_id) WHERE es_destacada = true
    es_destacada_inicio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    imagen_destacada_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    empresa: Mapped[Empresa] = relationship(lazy="joined")
    temporada: Mapped[Temporada] = relationship(lazy="joined")
