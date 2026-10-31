"""Reseta la contraseña del usuario test admin"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.db.session import SessionLocal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario


def reset_test_admin() -> None:
    db = SessionLocal()
    try:
        # Intentar actualizar un admin existente o crear uno
        correo = "testadmin@fashionstore.com"
        password = "testpass123"

        u = db.query(Usuario).filter_by(correo=correo).first()

        if u is None:
            print(f"Creando nuevo usuario: {correo}")
            u = Usuario(
                nombre="Test Admin",
                correo=correo,
                password_hash=hash_password(password),
                rol=RolUsuario.ADMINISTRADOR,
                is_active=True,
            )
            db.add(u)
        else:
            print(f"Actualizando contraseña para: {correo}")
            u.password_hash = hash_password(password)

        db.commit()
        print(f"OK - Usuario: {correo} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    reset_test_admin()
