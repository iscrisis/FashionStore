#!/usr/bin/env python3
"""
Auditoría de sincronización entre modelos SQLAlchemy y esquema PostgreSQL.
NO MODIFICA LA BASE DE DATOS.
"""

import os
import sys
import re
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.db.session import get_db
from app.db.base import Base

# Conectar a la BD
db = next(get_db())
inspector = inspect(db)

# Obtener todas las tablas reales
real_tables = set(inspector.get_table_names())
print(f"\n=== TABLAS EN BD ===\nTotal: {len(real_tables)}\n")
for table in sorted(real_tables):
    print(f"  {table}")

# Obtener todos los modelos SQLAlchemy
print(f"\n=== MODELOS SQLALCHEMY ===")
model_tables = {}
for attr_name in dir(Base.registry.mappers):
    pass

# Análisis de modelos
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
from modules.P7_GestionSaaSySuscripciones.Models.plan import Plan

MODELS_TO_AUDIT = [
    Producto, ProductoVariante, Coleccion, Categoria, Temporada,
    Sucursal, Ciudad, Usuario, Empresa, Plan
]

print(f"\nAnalizando {len(MODELS_TO_AUDIT)} modelos...")

differences = []

for model in MODELS_TO_AUDIT:
    table_name = model.__tablename__
    print(f"\n--- {table_name} ---")

    if table_name not in real_tables:
        print(f"❌ TABLA NO EXISTE")
        differences.append(f"CRÍTICA: Tabla {table_name} no existe")
        continue

    # Obtener columnas reales
    real_columns = {col['name']: col for col in inspector.get_columns(table_name)}

    # Obtener columnas del modelo
    model_mapper = inspect(model)
    model_columns = {col.name: col for col in model_mapper.columns}

    print(f"  Modelo: {len(model_columns)} columnas")
    print(f"  BD: {len(real_columns)} columnas")

    # Comparar
    for col_name, col_obj in model_columns.items():
        if col_name not in real_columns:
            msg = f"CRÍTICA: {table_name}.{col_name} FALTANTE en BD"
            print(f"  ❌ {col_name}")
            differences.append(msg)
        else:
            real_col = real_columns[col_name]
            model_type = str(col_obj.type)
            real_type = str(real_col['type'])
            if model_type != real_type:
                msg = f"ALTA: {table_name}.{col_name} tipo diferente (modelo: {model_type}, BD: {real_type})"
                print(f"  ⚠️ {col_name}: {model_type} vs {real_type}")
                differences.append(msg)

print(f"\n\n=== DIFERENCIAS ENCONTRADAS ===\n")
for diff in sorted(differences):
    print(f"  {diff}")

print(f"\nTotal: {len(differences)} diferencias\n")
