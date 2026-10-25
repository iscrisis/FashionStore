"""Script de debug para auditar SUPERADMIN en BD."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.security import verify_password
from app.db.session import SessionLocal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


def debug_superadmin() -> None:
    db = SessionLocal()
    try:
        print("=" * 60)
        print("AUDITORIA DE SUPERADMIN")
        print("=" * 60)

        # 1. Buscar el usuario
        correo = settings.SUPERADMIN_INITIAL_EMAIL
        print(f"\n1. Buscando usuario por correo: {correo}")

        u = db.query(Usuario).filter_by(correo=correo).first()

        if u is None:
            print("   [ERROR] Usuario NO encontrado en BD")
            return

        print("   [OK] Usuario encontrado")
        print(f"      ID: {u.id}")
        print(f"      Correo: {u.correo}")
        print(f"      Rol: {u.rol}")
        print(f"      Rol.value: {u.rol.value}")
        print(f"      Empresa_id: {u.empresa_id}")
        print(f"      Activo (is_active): {u.is_active}")
        print(f"      Password Hash (primeros 50 chars): {u.password_hash[:50]}...")

        # 2. Verificar contraseña
        password = settings.SUPERADMIN_INITIAL_PASSWORD
        print(f"\n2. Verificando contraseña: {password}")

        result = verify_password(password, u.password_hash)
        print(f"   verify_password() result: {result}")

        if result:
            print("   [OK] Contrasena CORRECTA")
        else:
            print("   [ERROR] Contrasena INCORRECTA")

        # 3. Verificar estado
        print(f"\n3. Verificando estado")
        print(f"   is_active: {u.is_active}")

        if u.is_active:
            print("   [OK] Usuario ACTIVO")
        else:
            print("   [ERROR] Usuario INACTIVO")

        # 4. Resumen
        print(f"\n4. RESUMEN DEL LOGIN")
        all_ok = u is not None and verify_password(password, u.password_hash) and u.is_active
        if all_ok:
            print("   [SUCCESS] LOGIN DEBERIA SER EXITOSO")
        else:
            print("   [FAILED] LOGIN FALLARA POR:")
            if u is None:
                print("      - Usuario no existe")
            if not verify_password(password, u.password_hash):
                print("      - Contrasena incorrecta")
            if not u.is_active:
                print("      - Usuario inactivo")

    finally:
        db.close()


if __name__ == "__main__":
    debug_superadmin()
