"""Entidad Sucursal, compartida por todo el paquete P1 — Sucursales y catálogo.

CU06 (gestionar sucursales) es el primer consumidor. Una sucursal pertenece a
una única ciudad (Ciudad 1 ----- N Sucursal). No incluye todavía stock,
inventario, productos, ventas, reservas, proveedores ni relación con usuarios
(encargado/cajero) — eso pertenece a requerimientos posteriores.
"""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .ciudad import Ciudad


class Sucursal(Base):
    __tablename__ = "sucursales"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    ciudad_id: Mapped[int] = mapped_column(ForeignKey("ciudades.id"), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    ciudad: Mapped[Ciudad] = relationship(lazy="joined")
