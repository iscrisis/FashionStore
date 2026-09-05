"""Crea el usuario ADMINISTRADOR inicial de FashionStore.

Necesario porque todavía no existe CU05 (Gestionar usuarios y roles), que en el
futuro permitirá crear administradores desde la interfaz. Es idempotente: si el
correo ya existe, no hace nada.

Uso:
    python scripts/seed_admin.py
    docker compose exec backend python scripts/seed_admin.py

Las credenciales se leen de ADMIN_INITIAL_NAME / ADMIN_INITIAL_EMAIL /
ADMIN_INITIAL_PASSWORD (ver app/core/config.py y .env.example).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.repository import UsuarioRepository  # noqa: E402
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario  # noqa: E402
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario  # noqa: E402


def seed_admin() -> None:
    db = SessionLocal()
    try:
        repository = UsuarioRepository(db)
        existente = repository.get_by_correo(settings.ADMIN_INITIAL_EMAIL)
        if existente is not None:
            print(f"Ya existe un usuario con correo {settings.ADMIN_INITIAL_EMAIL}; no se crea de nuevo.")
            return

        admin = Usuario(
            nombre=settings.ADMIN_INITIAL_NAME,
            correo=settings.ADMIN_INITIAL_EMAIL,
            password_hash=hash_password(settings.ADMIN_INITIAL_PASSWORD),
            rol=RolUsuario.ADMINISTRADOR,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Administrador inicial creado: {settings.ADMIN_INITIAL_EMAIL}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
