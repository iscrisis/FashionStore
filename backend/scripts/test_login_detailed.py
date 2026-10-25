"""Test detallado de login directamente contra el endpoint."""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Simular request como si viniera del endpoint
from fastapi import FastAPI
from app.db.session import SessionLocal
from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.service import LoginService, CredencialesInvalidasError, UsuarioInactivoError
from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.schemas import LoginRequest


def test_with_exact_payload():
    """Test con exactamente el payload que envía el cliente HTTP."""

    # Payload JSON que viene del cliente
    payload_json = '{"correo":"superadmin@fashionstore.com","password":"changeme"}'

    print("=" * 60)
    print("TEST DETALLADO DE LOGIN")
    print("=" * 60)

    print(f"\n1. Payload JSON recibido:")
    print(f"   {payload_json}")

    # Parsear JSON como lo hace FastAPI
    payload_dict = json.loads(payload_json)
    print(f"\n2. Parseado como dict:")
    print(f"   {payload_dict}")

    # Crear objeto LoginRequest como lo hace FastAPI
    login_request = LoginRequest(**payload_dict)
    print(f"\n3. LoginRequest objeto:")
    print(f"   correo: '{login_request.correo}' (type: {type(login_request.correo).__name__}, len: {len(login_request.correo)})")
    print(f"   password: '{login_request.password}' (type: {type(login_request.password).__name__}, len: {len(login_request.password)})")

    # Ahora llamar al service exactamente como lo hace el router
    db = SessionLocal()
    try:
        service = LoginService(db)
        print(f"\n4. Llamando a service.autenticar()...")

        try:
            usuario, token = service.autenticar(login_request.correo, login_request.password)
            print(f"   [SUCCESS]")
            print(f"   Usuario ID: {usuario.id}")
            print(f"   Usuario Rol: {usuario.rol.value}")
        except CredencialesInvalidasError:
            print(f"   [ERROR] CredencialesInvalidasError")
        except UsuarioInactivoError:
            print(f"   [ERROR] UsuarioInactivoError")
        except Exception as e:
            print(f"   [ERROR] {type(e).__name__}: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    test_with_exact_payload()
