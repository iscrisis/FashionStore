"""Acceso a datos de Empresa y Usuario necesario para CU02."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario


class AdministradorEmpresaRepository:
    """Repositorio para operaciones de consulta y actualización de administrador."""

    def __init__(self, db: Session):
        self.db = db

    def obtener_empresa_por_id(self, empresa_id: int) -> Empresa | None:
        """Obtener empresa por su ID."""
        return self.db.get(Empresa, empresa_id)

    def obtener_administrador_por_empresa(self, empresa_id: int) -> Usuario | None:
        """Obtener el usuario ADMINISTRADOR asociado a una empresa.

        Returns:
            Usuario con rol ADMINISTRADOR para la empresa, o None si no existe.
        """
        stmt = select(Usuario).where(
            Usuario.empresa_id == empresa_id,
            Usuario.rol == RolUsuario.ADMINISTRADOR,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def obtener_usuario_por_id(self, usuario_id: int) -> Usuario | None:
        """Obtener usuario por su ID."""
        return self.db.get(Usuario, usuario_id)

    def existe_correo_usuario(
        self, correo: str, excluyendo_usuario_id: int | None = None
    ) -> bool:
        """Verificar si ya existe un usuario con ese correo.

        Args:
            correo: Email a verificar.
            excluyendo_usuario_id: ID del usuario a excluir (para actualización).

        Returns:
            True si existe otro usuario con ese correo, False en caso contrario.
        """
        stmt = select(func.count()).select_from(Usuario).where(
            func.lower(Usuario.correo) == correo.strip().lower()
        )
        if excluyendo_usuario_id is not None:
            stmt = stmt.where(Usuario.id != excluyendo_usuario_id)
        return self.db.execute(stmt).scalar_one() > 0

    def actualizar_administrador(
        self,
        usuario: Usuario,
        nombre: str,
        correo: str,
        is_active: bool,
    ) -> Usuario:
        """Actualizar datos permitidos del administrador.

        Restricciones:
        - NO permite cambiar empresa_id
        - NO permite cambiar rol
        - Solo actualiza: nombre, correo, is_active

        Args:
            usuario: Objeto Usuario a actualizar.
            nombre: Nuevo nombre.
            correo: Nuevo correo.
            is_active: Nuevo estado.

        Returns:
            Usuario actualizado y persistido.
        """
        usuario.nombre = nombre
        usuario.correo = correo
        usuario.is_active = is_active
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
