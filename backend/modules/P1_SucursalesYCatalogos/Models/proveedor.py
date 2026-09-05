"""Entidad Proveedor, compartida por todo el paquete P1 — Sucursales y catálogo.

GestionProveedores es el primer consumidor. Proveedor NO es Usuario: es una
entidad de negocio propia (una empresa/persona externa que abastece a
FashionStore), sin cuenta ni credenciales — no se relaciona con la tabla
usuarios ni con el rol PROVEEDOR (ese es un paso posterior, separado).
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(primary_key=True)
    razon_social: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    nombre_contacto: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
