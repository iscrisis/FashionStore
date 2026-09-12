"""Acceso a datos propio de CU04 -- Actualizar perfil.

Solo agrega lo que CU04 necesita (verificar correo duplicado y guardar). La
búsqueda del usuario a editar NO vive aquí ni en ningún repository: llega ya
resuelta por app.core.deps.get_current_usuario (el mismo JWT que ya usa
CU01/CU05) directamente al router -- así no existe ningún método que reciba
un id arbitrario para buscar "cualquier" usuario.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


class ActualizarPerfilRepository:
    def __init__(self, db: Session):
        self.db = db

    def correo_pertenece_a_otro_usuario(self, correo: str, usuario_id: int) -> bool:
        stmt = select(func.count()).select_from(Usuario).where(
            func.lower(Usuario.correo) == correo.strip().lower(),
            Usuario.id != usuario_id,
        )
        return self.db.execute(stmt).scalar_one() > 0

    def guardar(self, usuario: Usuario) -> Usuario:
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
