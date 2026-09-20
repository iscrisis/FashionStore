"""Acceso a datos de Usuario necesario para CU02 -- Registrar cliente.

Consulta y escribe el mismo modelo que ya usan CU01 y CU05
(modules/P2_UsuariosYAccesos/Models/usuario.py); no crea una tabla paralela
de clientes.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


class RegistroClienteRepository:
    def __init__(self, db: Session):
        self.db = db

    def existe_correo(self, correo: str) -> bool:
        stmt = select(func.count()).select_from(Usuario).where(
            func.lower(Usuario.correo) == correo.strip().lower()
        )
        return self.db.execute(stmt).scalar_one() > 0

    def crear(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
