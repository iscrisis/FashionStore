"""Simula exactamente el flujo del endpoint de login."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.service import LoginService


def simulate_login() -> None:
    db = SessionLocal()
    try:
        service = LoginService(db)

        correo = "superadmin@fashionstore.com"
        password = "changeme"

        print("=" * 60)
        print("SIMULACION DE LOGIN")
        print("=" * 60)
        print(f"\nIntentando login con:")
        print(f"  Correo: {correo}")
        print(f"  Password: {password}")

        try:
            usuario, token = service.autenticar(correo, password)
            print(f"\n[SUCCESS] Login exitoso")
            print(f"  ID: {usuario.id}")
            print(f"  Correo: {usuario.correo}")
            print(f"  Rol: {usuario.rol.value}")
            print(f"  Token (primeros 50 chars): {token[:50]}...")
        except Exception as e:
            print(f"\n[ERROR] {type(e).__name__}: {str(e)}")

    finally:
        db.close()


if __name__ == "__main__":
    simulate_login()
