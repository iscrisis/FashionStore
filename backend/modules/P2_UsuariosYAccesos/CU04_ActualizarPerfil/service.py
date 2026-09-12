"""Reglas de negocio de CU04 -- Actualizar perfil.

El usuario a modificar es SIEMPRE el que ya autenticó el JWT (ver router.py,
Depends(get_current_usuario)); este service nunca recibe ni busca un usuario
por id, así que un cliente no tiene forma de editar a otro usuario
manipulando el request.

Solo toca nombre/correo/telefono. NUNCA password_hash (eso es CU03, ver
CU03_RecuperarContrasena) ni rol/sucursal_id/proveedor_id/is_active (eso es
CU05, ver CU05_GestionarUsuariosRoles) -- ActualizarPerfilRequest ni siquiera
declara esos campos (ver schemas.py).
"""

from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .repository import ActualizarPerfilRepository
from .schemas import ActualizarPerfilRequest


class CorreoYaRegistradoError(Exception):
    """Otro usuario (distinto del que edita su propio perfil) ya usa ese correo."""


class ActualizarPerfilService:
    def __init__(self, db: Session):
        self._repo = ActualizarPerfilRepository(db)

    def actualizar(self, usuario: Usuario, datos: ActualizarPerfilRequest) -> Usuario:
        if self._repo.correo_pertenece_a_otro_usuario(datos.correo, usuario.id):
            raise CorreoYaRegistradoError

        usuario.nombre = datos.nombre
        usuario.correo = datos.correo
        usuario.telefono = datos.telefono
        return self._repo.guardar(usuario)
