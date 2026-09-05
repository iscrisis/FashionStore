"""Reglas de negocio de CU05 — Gestionar usuarios y roles."""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .repository import UsuariosRolesRepository
from .schemas import ROLES_INTERNOS, UsuarioActualizar, UsuarioCrear


class UsuarioNoEncontradoError(Exception):
    pass


class CorreoDuplicadoError(Exception):
    pass


class RolNoAsignableError(Exception):
    """CLIENTE no se asigna desde CU05 (pertenece a CU02 — Registrar cliente)."""


class OperacionNoPermitidaError(Exception):
    """Auto-bloqueo del administrador o remoción del último ADMINISTRADOR activo."""


class UsuariosRolesService:
    def __init__(self, db: Session):
        self._repo = UsuariosRolesRepository(db)

    def listar(
        self, search: str | None, rol: RolUsuario | None, is_active: bool | None
    ) -> list[Usuario]:
        return self._repo.listar(search=search, rol=rol, is_active=is_active)

    def obtener(self, usuario_id: int) -> Usuario:
        usuario = self._repo.get_by_id(usuario_id)
        if usuario is None:
            raise UsuarioNoEncontradoError
        return usuario

    def crear(self, datos: UsuarioCrear) -> Usuario:
        if datos.rol not in ROLES_INTERNOS:
            raise RolNoAsignableError

        if self._repo.get_by_correo(datos.correo) is not None:
            raise CorreoDuplicadoError

        usuario = Usuario(
            nombre=datos.nombre.strip(),
            correo=datos.correo.strip().lower(),
            password_hash=hash_password(datos.password),
            rol=datos.rol,
            is_active=datos.is_active,
        )
        return self._repo.crear(usuario)

    def actualizar_datos(self, usuario_id: int, datos: UsuarioActualizar) -> Usuario:
        usuario = self.obtener(usuario_id)

        existente = self._repo.get_by_correo(datos.correo.strip().lower())
        if existente is not None and existente.id != usuario.id:
            raise CorreoDuplicadoError

        usuario.nombre = datos.nombre.strip()
        usuario.correo = datos.correo.strip().lower()
        return self._repo.guardar(usuario)

    def cambiar_rol(self, usuario_id: int, nuevo_rol: RolUsuario, actor: Usuario) -> Usuario:
        if nuevo_rol not in ROLES_INTERNOS:
            raise RolNoAsignableError

        usuario = self.obtener(usuario_id)

        es_ultimo_admin = (
            usuario.rol == RolUsuario.ADMINISTRADOR
            and nuevo_rol != RolUsuario.ADMINISTRADOR
            and self._repo.contar_administradores_activos(excluyendo_id=usuario.id) == 0
        )
        if es_ultimo_admin:
            raise OperacionNoPermitidaError

        usuario.rol = nuevo_rol
        return self._repo.guardar(usuario)

    def cambiar_estado(self, usuario_id: int, activo: bool, actor: Usuario) -> Usuario:
        usuario = self.obtener(usuario_id)

        # No hace falta además contar administradores activos aquí: para llegar a este
        # endpoint el actor ya debe ser un ADMINISTRADOR activo (require_admin), así que
        # desactivar a alguien más nunca deja el sistema en cero administradores — el único
        # camino real hacia ese escenario es la autodesactivación, ya bloqueada arriba.
        if not activo and usuario.id == actor.id:
            raise OperacionNoPermitidaError

        usuario.is_active = activo
        return self._repo.guardar(usuario)
