"""Entidad Sucursal, compartida por todo el paquete P1 — Sucursales y catálogo.

CU06 (gestionar sucursales) es el primer consumidor. Una sucursal pertenece a
una única ciudad (Ciudad 1 ----- N Sucursal) y a una única empresa (Empresa 1 ----- N Sucursal).

Multitenant: cada sucursal pertenece explícitamente a una empresa. El aislamiento
se garantiza mediante empresa_id + FK a Empresa.
La relación a Ciudad es simple: ciudad_id → Ciudad.id
"""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .ciudad import Ciudad
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa


class Sucursal(Base):
    __tablename__ = "sucursales"
    __table_args__ = (
        UniqueConstraint("empresa_id", "id", name="uq_sucursal_empresa_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    ciudad_id: Mapped[int] = mapped_column(ForeignKey("ciudades.id"), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    empresa: Mapped[Empresa] = relationship(lazy="joined")
    ciudad: Mapped[Ciudad] = relationship(lazy="joined")
