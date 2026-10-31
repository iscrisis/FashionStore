"""Servicios de CU03 — Asociar usuarios y sucursales a empresa.

Lógica compartida de multitenant/SaaS que es reutilizada por CU05 y CU06.

Responsabilidades:
1. Validar que un usuario pueda realizar asociaciones (debe ser ADMINISTRADOR)
2. Obtener la empresa_id del usuario autenticado
3. Asegurar que los recursos se asocien a la empresa correcta
4. Validar que no se realicen asociaciones cruzadas (empresa A → recurso de empresa B)
"""

from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


class UsuarioSinEmpresaError(Exception):
    """El usuario autenticado no tiene empresa asignada."""


class RolNoAutorizadoParaAsociacionError(Exception):
    """Solo ADMINISTRADOR puede asociar recursos a empresa."""


class TenantViolationError(Exception):
    """Intento de asociar recurso a empresa distinta."""


class AsociacionesEmpresaService:
    """Servicio de asociación usuario/sucursal a empresa."""

    def __init__(self, db: Session):
        self._db = db

    def obtener_empresa_id_del_actor(self, actor: Usuario) -> int:
        """Obtiene la empresa_id del usuario ADMINISTRADOR autenticado.

        Validación:
        - El actor debe ser ADMINISTRADOR de una empresa
        - SUPERADMIN no puede realizar asociaciones específicas a empresa

        Args:
            actor: Usuario autenticado

        Returns:
            int: empresa_id del actor

        Raises:
            RolNoAutorizadoParaAsociacionError: Si no es ADMINISTRADOR
            UsuarioSinEmpresaError: Si no tiene empresa asignada
        """
        if actor.rol != RolUsuario.ADMINISTRADOR:
            raise RolNoAutorizadoParaAsociacionError(
                f"Solo ADMINISTRADOR puede realizar asociaciones. Rol actual: {actor.rol}"
            )

        if actor.empresa_id is None:
            raise UsuarioSinEmpresaError(
                "El usuario ADMINISTRADOR debe tener una empresa asignada."
            )

        return actor.empresa_id

    def validar_empresa_id(self, recurso_empresa_id: int | None, empresa_id_esperado: int) -> None:
        """Valida que un recurso pertenezca a la empresa correcta (validación de tenant).

        Args:
            recurso_empresa_id: empresa_id del recurso
            empresa_id_esperado: empresa_id esperado

        Raises:
            TenantViolationError: Si no coinciden
        """
        if recurso_empresa_id is None:
            raise TenantViolationError("El recurso no tiene empresa asignada.")

        if recurso_empresa_id != empresa_id_esperado:
            raise TenantViolationError(
                f"Tenant violation: recurso pertenece a empresa {recurso_empresa_id}, "
                f"pero se intenta operar sobre empresa {empresa_id_esperado}."
            )

    def asignar_empresa_al_usuario(self, usuario: Usuario, empresa_id: int) -> None:
        """Asigna una empresa a un usuario durante su creación.

        Esta es la operación central de CU03: "asociar usuario a empresa".

        Args:
            usuario: Usuario sin empresa asignada (entity)
            empresa_id: Empresa a asignar

        Nota:
            Solo se usa durante la CREACIÓN de usuario (POST /usuarios desde CU05).
            La empresa no puede cambiar después de creado el usuario.
        """
        usuario.empresa_id = empresa_id

    def asignar_empresa_a_sucursal(self, sucursal, empresa_id: int) -> None:
        """Asigna una empresa a una sucursal durante su creación.

        Esta es la operación central de CU03: "asociar sucursal a empresa".

        Args:
            sucursal: Sucursal sin empresa asignada (entity)
            empresa_id: Empresa a asignar

        Nota:
            Solo se usa durante la CREACIÓN de sucursal (POST /sucursales desde CU06).
            La empresa no puede cambiar después de creada la sucursal.
        """
        sucursal.empresa_id = empresa_id
