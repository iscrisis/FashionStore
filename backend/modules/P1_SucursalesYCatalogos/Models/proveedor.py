"""Entidad Proveedor - POR EMPRESA.

Multitenant: cada empresa administra sus propios proveedores.
Proveedor NO es Usuario: es una entidad de negocio propia (una empresa/persona
externa que abastece a FashionStore), sin cuenta ni credenciales — no se
relaciona con la tabla usuarios ni con el rol PROVEEDOR (ese es un paso posterior, separado).

GestionProveedores es el primer consumidor.
"""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa


class Proveedor(Base):
    __tablename__ = "proveedores"
    __table_args__ = (
        UniqueConstraint("empresa_id", "razon_social", name="uq_proveedor_empresa_razon_social"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    razon_social: Mapped[str] = mapped_column(String(150), nullable=False)
    nombre_contacto: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    empresa: Mapped[Empresa] = relationship(lazy="joined")
