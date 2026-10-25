"""Crea la empresa del primer parcial — Empresa principal de FashionStore.

Esta es la empresa "por defecto" que corresponde al primer parcial de desarrollo.
Todos los datos del primer parcial (usuarios, sucursales, productos, etc.) pertenecen
a esta empresa en la arquitectura multitenant del segundo parcial.

Es idempotente: si la empresa ya existe por nombre o slug, no la duplica.

Uso:
    python scripts/seed_empresa.py
    docker compose exec backend python scripts/seed_empresa.py

Las credenciales se leen de EMPRESA_INICIAL_* (ver app/core/config.py y .env.example).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa  # noqa: E402


def seed_empresa() -> None:
    db = SessionLocal()
    try:
        # Verificar si existe por nombre o slug
        existente_nombre = db.query(Empresa).filter_by(nombre=settings.EMPRESA_INICIAL_NOMBRE).first()
        existente_slug = db.query(Empresa).filter_by(slug=settings.EMPRESA_INICIAL_SLUG).first()

        if existente_nombre or existente_slug:
            print(f"Ya existe una empresa con nombre o slug del primer parcial; no se crea de nuevo.")
            return

        empresa = Empresa(
            nombre=settings.EMPRESA_INICIAL_NOMBRE,
            slug=settings.EMPRESA_INICIAL_SLUG,
            razon_social=settings.EMPRESA_INICIAL_RAZON_SOCIAL,
            correo=settings.EMPRESA_INICIAL_CORREO,
            telefono=settings.EMPRESA_INICIAL_TELEFONO,
            is_active=True,
        )
        db.add(empresa)
        db.commit()
        print(f"Empresa del primer parcial creada: {settings.EMPRESA_INICIAL_NOMBRE} (ID: {empresa.id})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_empresa()
