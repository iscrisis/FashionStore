"""
Endpoint temporal de diagnóstico ORM para Sucursal.ciudad relación.
Se añade al router de CU06 temporalmente.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import inspect, select, and_
from sqlalchemy.orm import Session

from app.db.database import get_db
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad

diagnostic_router = APIRouter(prefix="/diag", tags=["Diagnostic"])

@diagnostic_router.get("/orm-relation")
def diagnose_orm_relation(db: Session = Depends(get_db)):
    """Diagnóstico de la relación Sucursal.ciudad"""

    result = {
        "stage": [],
        "error": None
    }

    try:
        # 1. Analizar mapper
        result["stage"].append({
            "name": "Mapper Analysis",
            "mapper": {
                "pk": str(inspect(Sucursal).primary_key),
                "relations": list(inspect(Sucursal).relationships.keys())
            }
        })

        rel = inspect(Sucursal).relationships.get('ciudad')
        if rel:
            result["stage"].append({
                "name": "Relation Details",
                "relation": {
                    "lazy": rel.lazy,
                    "uselist": rel.uselist,
                    "viewonly": rel.viewonly,
                    "foreign_keys_count": len(rel.foreign_keys),
                    "foreign_keys": [str(fk) for fk in rel.foreign_keys],
                }
            })

        # 2. Obtener sucursal
        sucursal = db.execute(
            select(Sucursal).limit(1)
        ).scalar_one_or_none()

        if not sucursal:
            result["stage"].append({
                "name": "Query",
                "status": "No sucursales en BD"
            })
            return result

        result["stage"].append({
            "name": "Sucursal Found",
            "sucursal": {
                "id": sucursal.id,
                "empresa_id": sucursal.empresa_id,
                "ciudad_id": sucursal.ciudad_id
            }
        })

        # 3. Acceder a relación
        ciudad_orm = sucursal.ciudad
        result["stage"].append({
            "name": "ORM Relation Access",
            "ciudad_orm": {
                "value": str(ciudad_orm),
                "is_none": ciudad_orm is None,
                "type": type(ciudad_orm).__name__ if ciudad_orm else "None"
            }
        })

        # 4. Obtener ciudad manualmente
        ciudad_manual = db.query(Ciudad).filter(
            (Ciudad.id == sucursal.ciudad_id) &
            (Ciudad.empresa_id == sucursal.empresa_id)
        ).first()

        result["stage"].append({
            "name": "Manual Query",
            "ciudad_manual": {
                "found": ciudad_manual is not None,
                "nombre": ciudad_manual.nombre if ciudad_manual else None,
                "id": ciudad_manual.id if ciudad_manual else None
            }
        })

        # 5. Join explícito
        result_join = db.execute(
            select(Sucursal).outerjoin(
                Ciudad,
                and_(
                    Sucursal.ciudad_id == Ciudad.id,
                    Sucursal.empresa_id == Ciudad.empresa_id
                )
            ).where(Sucursal.id == sucursal.id)
        ).unique().scalar_one()

        result["stage"].append({
            "name": "Explicit JOIN",
            "after_join": {
                "ciudad_value": str(result_join.ciudad),
                "is_none": result_join.ciudad is None,
                "type": type(result_join.ciudad).__name__ if result_join.ciudad else "None"
            }
        })

        result["conclusion"] = {
            "mapper_correct": rel is not None,
            "orm_loads_relation": ciudad_orm is not None,
            "manual_query_works": ciudad_manual is not None,
            "join_populates_orm": result_join.ciudad is not None,
            "problem": "ORM relation returns None despite manual query working"
                if ciudad_orm is None and ciudad_manual is not None
                else "Unknown"
        }

    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()

    return result
