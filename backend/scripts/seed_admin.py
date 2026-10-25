"""Crea el usuario ADMINISTRADOR inicial de FashionStore.

El ADMINISTRADOR pertenece a la empresa del primer parcial (EMPRESA_INICIAL_*).
Esta es una operación del segundo parcial (multitenant): el ADMIN se asigna a su empresa.

Necesario porque todavía no existe CU05 (Gestionar usuarios y roles), que en el
futuro permitirá crear administradores desde la interfaz. Es idempotente: si el
correo ya existe, no hace nada. Si existe pero sin empresa, lo actualiza.

Uso:
    python scripts/seed_admin.py
    docker compose exec backend python scripts/seed_admin.py

Las credenciales se leen de ADMIN_INITIAL_* y EMPRESA_INICIAL_*
(ver app/core/config.py y .env.example).
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
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa  # noqa: E402


def seed_admin() -> None:
    db = SessionLocal()
    try:
        # Obtener la empresa del primer parcial
        empresa = db.query(Empresa).filter_by(
            nombre=settings.EMPRESA_INICIAL_NOMBRE
        ).first()

        if empresa is None:
            print(f"ERROR: No existe la empresa del primer parcial.")
            print(f"Ejecuta primero: python scripts/seed_empresa.py")
            return

        repository = UsuarioRepository(db)
        existente = repository.get_by_correo(settings.ADMIN_INITIAL_EMAIL)

        if existente is not None:
            # Si existe pero no tiene empresa asignada, asignarlo
            if existente.empresa_id != empresa.id:
                existente.empresa_id = empresa.id
                db.commit()
                print(f"Administrador existente actualizado con empresa: {settings.ADMIN_INITIAL_EMAIL}")
            else:
                print(f"Ya existe un administrador con correo {settings.ADMIN_INITIAL_EMAIL}; no se crea de nuevo.")
            return

        admin = Usuario(
            nombre=settings.ADMIN_INITIAL_NAME,
            correo=settings.ADMIN_INITIAL_EMAIL,
            password_hash=hash_password(settings.ADMIN_INITIAL_PASSWORD),
            rol=RolUsuario.ADMINISTRADOR,
            is_active=True,
            empresa_id=empresa.id,  # ← Asignar a la empresa del primer parcial
        )
        db.add(admin)
        db.commit()
        print(f"Administrador inicial creado: {settings.ADMIN_INITIAL_EMAIL} (Empresa ID: {empresa.id})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
