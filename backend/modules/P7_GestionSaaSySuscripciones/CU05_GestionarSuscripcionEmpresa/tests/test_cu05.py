"""Tests de CU05 — Gestionar suscripción de empresa."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
from modules.P7_GestionSaaSySuscripciones.Models.plan import Plan
from modules.P7_GestionSaaSySuscripciones.Models.suscripcion import Suscripcion
from modules.P7_GestionSaaSySuscripciones.CU05_GestionarSuscripcionEmpresa.service import SuscripcionesService


def test_obtener_suscripcion_empresa_no_existe(db: Session):
    """Test: obtener suscripción de empresa inexistente."""
    service = SuscripcionesService(db)

    from modules.P7_GestionSaaSySuscripciones.CU05_GestionarSuscripcionEmpresa.service import EmpresaNoEncontradaError
    with pytest.raises(EmpresaNoEncontradaError):
        service.obtener_suscripcion_empresa(9999)


def test_asignar_plan_a_empresa(db: Session):
    """Test: asignar plan a empresa."""
    from modules.P7_GestionSaaSySuscripciones.CU05_GestionarSuscripcionEmpresa.schemas import SuscripcionCrear

    empresa = Empresa(nombre="Test Company", razon_social="Test S.A.")
    db.add(empresa)
    db.commit()

    plan = Plan(
        nombre="Test Plan",
        slug="test-plan",
        descripcion="Test Plan Description",
        precio=100.00,
        limite_sucursales=5,
        limite_usuarios=10,
    )
    db.add(plan)
    db.commit()

    service = SuscripcionesService(db)
    datos = SuscripcionCrear(
        empresa_id=empresa.id,
        plan_id=plan.id,
        fecha_inicio=datetime.now(),
        fecha_vencimiento=datetime.now() + timedelta(days=365),
    )

    suscripcion = service.asignar_plan(datos)
    assert suscripcion.empresa_id == empresa.id
    assert suscripcion.plan_id == plan.id
    assert suscripcion.activa is True
