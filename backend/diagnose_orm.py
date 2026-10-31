import sys
from sqlalchemy import inspect, create_engine, select, and_
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad

DATABASE_URL = "postgresql://postgres:postgres@db:5432/fashionstore"

try:
    print("\n" + "=" * 80)
    print("DIAGNOSTICO ORM SUCURSAL.CIUDAD")
    print("=" * 80)

    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        print("\n1. MAPPER DE SUCURSAL")
        print("-" * 80)

        mapper = inspect(Sucursal)
        print(f"PK: {mapper.primary_key}")
        print(f"Relaciones: {list(mapper.relationships.keys())}")

        rel = mapper.relationships.get('ciudad')
        if rel:
            print(f"\nDetalles de relacion 'ciudad':")
            print(f"  lazy: {rel.lazy}")
            print(f"  uselist: {rel.uselist}")
            print(f"  viewonly: {rel.viewonly}")
            print(f"  foreign_keys ({len(rel.foreign_keys)}): {rel.foreign_keys}")
            print(f"  primaryjoin: {rel.primaryjoin}")

        print("\n2. OBTENER SUCURSAL")
        print("-" * 80)

        sucursal = session.execute(
            select(Sucursal).limit(1)
        ).scalar_one_or_none()

        if not sucursal:
            print("No hay sucursales en BD")
            sys.exit(0)

        print(f"Sucursal ID: {sucursal.id}")
        print(f"Empresa ID: {sucursal.empresa_id}")
        print(f"Ciudad ID: {sucursal.ciudad_id}")

        print("\n3. ACCEDER A sucursal.ciudad")
        print("-" * 80)

        ciudad_orm = sucursal.ciudad
        print(f"sucursal.ciudad = {ciudad_orm}")

        if ciudad_orm is None:
            print("**PROBLEMA**: RELACION DEVUELVE None")
        else:
            print(f"**OK**: Relacion cargada: {ciudad_orm.nombre}")

        print("\n4. OBTENER CIUDAD MANUALMENTE")
        print("-" * 80)

        ciudad_manual = session.query(Ciudad).filter(
            (Ciudad.id == sucursal.ciudad_id) &
            (Ciudad.empresa_id == sucursal.empresa_id)
        ).first()

        if ciudad_manual:
            print(f"**OK**: Ciudad encontrada: {ciudad_manual.nombre}")
            print(f"  ID: {ciudad_manual.id}, Empresa: {ciudad_manual.empresa_id}")
        else:
            print("**ERROR**: Ciudad no encontrada")

        print("\n5. QUERY CON JOIN EXPLICITO")
        print("-" * 80)

        result = session.execute(
            select(Sucursal).outerjoin(
                Ciudad,
                and_(
                    Sucursal.ciudad_id == Ciudad.id,
                    Sucursal.empresa_id == Ciudad.empresa_id
                )
            ).where(Sucursal.id == sucursal.id)
        ).unique().scalar_one()

        print(f"JOIN ejecutado")
        print(f"result.ciudad despues del JOIN: {result.ciudad}")

        print("\n" + "=" * 80)

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
