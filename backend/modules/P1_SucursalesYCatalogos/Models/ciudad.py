"""Entidad Ciudad - Catálogo global de ciudades.

CU06 (gestionar sucursales) es el primer consumidor: cada sucursal pertenece a
una ciudad. Se mantiene deliberadamente mínima (id, nombre, departamento,
is_active) porque CU06 no requiere provincia, coordenadas ni mapas.

Nota: el campo empresa_id existe pero es NULL para todas las ciudades.
Las ciudades son un catálogo compartido sin tenant.
"""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa


class Ciudad(Base):
    __tablename__ = "ciudades"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_ciudad_empresa_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int | None] = mapped_column(ForeignKey("empresas.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    departamento: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    empresa: Mapped[Empresa | None] = relationship(lazy="joined", foreign_keys=[empresa_id])
