"""Reseta la contraseña del SUPERADMIN a la configurada en .env

Uso:
    python scripts/reset_superadmin_password.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario


def reset_superadmin_password() -> None:
    db = SessionLocal()
    try:
        u = db.query(Usuario).filter_by(correo=settings.SUPERADMIN_INITIAL_EMAIL).first()

        if u is None:
            print(f"ERROR: Usuario {settings.SUPERADMIN_INITIAL_EMAIL} no existe.")
            return

        if u.rol != RolUsuario.SUPERADMIN:
            print(f"ERROR: Usuario existe pero rol es {u.rol}, no SUPERADMIN.")
            return

        u.password_hash = hash_password(settings.SUPERADMIN_INITIAL_PASSWORD)
        db.commit()
        print(f"Contraseña actualizada para: {settings.SUPERADMIN_INITIAL_EMAIL}")
    finally:
        db.close()


if __name__ == "__main__":
    reset_superadmin_password()
