"""Crea algunas ciudades de arranque para un entorno de desarrollo nuevo, antes
de que un administrador registre las suyas desde CU06 (Gestionar sucursales →
Gestionar ciudades). Es idempotente: si una ciudad ya existe (por nombre), no
la duplica.

Uso:
    python scripts/seed_ciudades.py
    docker compose exec backend python scripts/seed_ciudades.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from modules.P1_SucursalesYCatalogos.CU06_GestionarSucursales.repository import (  # noqa: E402
    CiudadesRepository,
)
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad  # noqa: E402

CIUDADES_INICIALES = [
    ("Santa Cruz", "Santa Cruz"),
    ("Cochabamba", "Cochabamba"),
    ("La Paz", "La Paz"),
]


def seed_ciudades() -> None:
    db = SessionLocal()
    try:
        repo = CiudadesRepository(db)
        existentes = {c.nombre for c in repo.listar()}
        for nombre, departamento in CIUDADES_INICIALES:
            if nombre in existentes:
                print(f"Ya existe la ciudad '{nombre}'; no se crea de nuevo.")
                continue
            db.add(Ciudad(nombre=nombre, departamento=departamento, is_active=True))
            print(f"Ciudad creada: {nombre} ({departamento})")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_ciudades()
