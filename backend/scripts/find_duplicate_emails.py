"""Busca usuarios duplicados por correo."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


def find_duplicate_emails() -> None:
    db = SessionLocal()
    try:
        correo = "superadmin@fashionstore.com"
        print("=" * 60)
        print(f"BUSCANDO USUARIOS CON CORREO: {correo}")
        print("=" * 60)

        usuarios = db.query(Usuario).filter_by(correo=correo).all()

        print(f"\nTotal de usuarios encontrados: {len(usuarios)}")

        for u in usuarios:
            print(f"\n  ID: {u.id}")
            print(f"  Correo: {u.correo}")
            print(f"  Rol: {u.rol.value}")
            print(f"  Empresa_id: {u.empresa_id}")
            print(f"  Activo: {u.is_active}")
            print(f"  Hash (primeros 30): {u.password_hash[:30]}...")

        if len(usuarios) > 1:
            print(f"\n[WARNING] Hay {len(usuarios)} usuarios con el mismo correo!")
        elif len(usuarios) == 1:
            print(f"\n[OK] Solo hay 1 usuario con este correo")
        else:
            print(f"\n[ERROR] No hay usuarios con este correo")

    finally:
        db.close()


if __name__ == "__main__":
    find_duplicate_emails()
