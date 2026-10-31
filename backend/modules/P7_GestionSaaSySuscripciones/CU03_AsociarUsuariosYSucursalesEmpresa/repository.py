"""Acceso a datos de CU03 — Asociar usuarios y sucursales a empresa.

Encapsula las operaciones de lectura/filtrado específicas de multitenant.
No duplica UsuariosRolesRepository ni SucursalesRepository — estos permanecen en CU05/CU06.

Este repository proporciona métodos helper para validación de tenant.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal


class AsociacionesEmpresaRepository:
    """Acceso a datos para validar asociaciones usuario/sucursal → empresa."""

    def __init__(self, db: Session):
        self._db = db

    def usuario_pertenece_a_empresa(self, usuario_id: int, empresa_id: int) -> bool:
        """Verifica si un usuario pertenece a una empresa.

        Args:
            usuario_id: ID del usuario
            empresa_id: ID de la empresa

        Returns:
            bool: True si el usuario pertenece a esa empresa
        """
        stmt = select(Usuario).where(
            Usuario.id == usuario_id,
            Usuario.empresa_id == empresa_id,
        )
        result = self._db.execute(stmt).scalar_one_or_none()
        return result is not None

    def sucursal_pertenece_a_empresa(self, sucursal_id: int, empresa_id: int) -> bool:
        """Verifica si una sucursal pertenece a una empresa.

        Args:
            sucursal_id: ID de la sucursal
            empresa_id: ID de la empresa

        Returns:
            bool: True si la sucursal pertenece a esa empresa
        """
        stmt = select(Sucursal).where(
            Sucursal.id == sucursal_id,
            Sucursal.empresa_id == empresa_id,
        )
        result = self._db.execute(stmt).scalar_one_or_none()
        return result is not None

    def listar_usuarios_de_empresa(self, empresa_id: int) -> list[Usuario]:
        """Lista todos los usuarios de una empresa (excepto ADMINISTRADOR y SUPERADMIN).

        Args:
            empresa_id: ID de la empresa

        Returns:
            list[Usuario]: Usuarios de esa empresa
        """
        from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario

        stmt = select(Usuario).where(
            Usuario.empresa_id == empresa_id,
            Usuario.rol.notin_([RolUsuario.ADMINISTRADOR, RolUsuario.SUPERADMIN]),
        ).order_by(Usuario.nombre)
        return list(self._db.execute(stmt).scalars().all())

    def listar_sucursales_de_empresa(self, empresa_id: int) -> list[Sucursal]:
        """Lista todas las sucursales de una empresa.

        Args:
            empresa_id: ID de la empresa

        Returns:
            list[Sucursal]: Sucursales de esa empresa
        """
        stmt = select(Sucursal).where(
            Sucursal.empresa_id == empresa_id,
        ).order_by(Sucursal.nombre)
        return list(self._db.execute(stmt).scalars().all())
