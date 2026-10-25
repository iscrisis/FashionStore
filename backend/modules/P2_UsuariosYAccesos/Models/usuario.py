"""Entidad Usuario, compartida por todo el paquete P2 — Usuarios y accesos.

CU01 (iniciar sesión) es el primer consumidor. CU02, CU03, CU04 y CU05 reutilizarán
este mismo modelo — no debe duplicarse por caso de uso.

empresa_id es nullable para soportar SUPERADMIN (rol de plataforma global, sin empresa).
La validación de negocio (SUPERADMIN → empresa_id NULL, demás roles → empresa_id obligatorio)
ocurre en la capa de servicio, no en el ORM.

sucursal_id referencia a Sucursal (modules/P1_SucursalesYCatalogos/Models), no la
duplica: un empleado interno (ENCARGADO_SUCURSAL/CAJERO) queda ligado a su
sucursal, y a través de ella a su ciudad (Usuario → Sucursal → Ciudad). Permite
NULL porque ADMINISTRADOR, SUPERADMIN y CLIENTE no pertenecen a ninguna sucursal.

proveedor_id referencia a Proveedor (modules/P1_SucursalesYCatalogos/Models),
tampoco lo duplica: una cuenta con rol PROVEEDOR queda ligada a SU proveedor
(Usuario → Proveedor), nunca a una sucursal. Es unique porque cada proveedor
tiene una única cuenta de acceso.

telefono lo captura CU02 (registrar cliente) como celular de contacto del
Cliente, y CU04 (actualizar perfil) lo consulta/edita. Permite NULL porque
las cuentas internas (creadas por CU05) no lo exigen.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal

from .rol import RolUsuario


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("empresa_id", "correo", name="uq_usuario_empresa_correo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int | None] = mapped_column(ForeignKey("empresas.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        SAEnum(RolUsuario, name="rol_usuario"), nullable=False, default=RolUsuario.CLIENTE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sucursal_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id"), nullable=True)
    proveedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("proveedores.id"), unique=True, nullable=True
    )
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)

    empresa: Mapped[Empresa] = relationship(lazy="joined")
    sucursal: Mapped[Sucursal | None] = relationship(lazy="joined")
    proveedor: Mapped[Proveedor | None] = relationship(lazy="joined")
