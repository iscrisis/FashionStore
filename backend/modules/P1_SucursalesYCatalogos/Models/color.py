"""Entidad Color - POR EMPRESA.

Multitenant: cada empresa administra sus propios colores.
Dos empresas pueden tener independientemente colores llamados "Rojo" pero con
diferentes especificaciones o tonalidades.

CU09 (gestionar categorías, tallas y colores) es el primer consumidor.
Solo nombre — sin código hex, sin orden de despliegue: CU09 no los necesita.
"""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa


class Color(Base):
    __tablename__ = "colores"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_color_empresa_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    empresa: Mapped[Empresa] = relationship(lazy="joined")
