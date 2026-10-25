"""Entidad Talla - POR EMPRESA.

Multitenant: cada empresa administra sus propias tallas.
Dos empresas pueden tener independientemente tallas llamadas "M" o tamaños "40".

CU09 (gestionar categorías, tallas y colores) es el primer consumidor.
nombre es texto libre a propósito (no un enum XS/S/M/L/XL): admite cualquier
formato de talla que FashionStore necesite registrar, hoy o más adelante.
"""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa


class Talla(Base):
    __tablename__ = "tallas"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_talla_empresa_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    empresa: Mapped[Empresa] = relationship(lazy="joined")
