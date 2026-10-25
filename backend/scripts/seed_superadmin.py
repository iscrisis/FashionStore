"""Crea el usuario SUPERADMIN inicial de FashionStore.

El SUPERADMIN es el rol de plataforma global, por encima de los administradores
de empresa. Es idempotente: si el correo ya existe, no hace nada.

Uso:
    python scripts/seed_superadmin.py
    docker compose exec backend python scripts/seed_superadmin.py

Las credenciales se leen de SUPERADMIN_INITIAL_NAME / SUPERADMIN_INITIAL_EMAIL /
SUPERADMIN_INITIAL_PASSWORD (ver app/core/config.py y .env.example).
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


def seed_superadmin() -> None:
    db = SessionLocal()
    try:
        repository = UsuarioRepository(db)
        existente = repository.get_by_correo(settings.SUPERADMIN_INITIAL_EMAIL)
        if existente is not None:
            print(f"Ya existe un usuario con correo {settings.SUPERADMIN_INITIAL_EMAIL}; no se crea de nuevo.")
            return

        superadmin = Usuario(
            nombre=settings.SUPERADMIN_INITIAL_NAME,
            correo=settings.SUPERADMIN_INITIAL_EMAIL,
            password_hash=hash_password(settings.SUPERADMIN_INITIAL_PASSWORD),
            rol=RolUsuario.SUPERADMIN,
            is_active=True,
            empresa_id=None,  # SUPERADMIN no pertenece a ninguna empresa
        )
        db.add(superadmin)
        db.commit()
        print(f"SUPERADMIN inicial creado: {settings.SUPERADMIN_INITIAL_EMAIL}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_superadmin()
