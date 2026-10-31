"""Tests de CU03 — Asociar usuarios y sucursales a empresa."""

import pytest
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal

from .service import (
    AsociacionesEmpresaService,
    UsuarioSinEmpresaError,
    RolNoAutorizadoParaAsociacionError,
    TenantViolationError,
)


def test_obtener_empresa_id_del_actor_administrador(db: Session):
    """Test: ADMINISTRADOR puede obtener su empresa_id."""
    admin = Usuario(
        nombre="Admin Test",
        correo="admin@test.com",
        password_hash="fake_hash",
        rol=RolUsuario.ADMINISTRADOR,
        empresa_id=1,
        is_active=True,
    )
    db.add(admin)
    db.commit()

    service = AsociacionesEmpresaService(db)
    empresa_id = service.obtener_empresa_id_del_actor(admin)

    assert empresa_id == 1


def test_obtener_empresa_id_del_actor_no_administrador(db: Session):
    """Test: Usuario no-ADMINISTRADOR no puede obtener empresa_id para asociación."""
    vendedor = Usuario(
        nombre="Vendedor Test",
        correo="vendedor@test.com",
        password_hash="fake_hash",
        rol=RolUsuario.ENCARGADO_SUCURSAL,
        empresa_id=1,
        is_active=True,
    )
    db.add(vendedor)
    db.commit()

    service = AsociacionesEmpresaService(db)

    with pytest.raises(RolNoAutorizadoParaAsociacionError):
        service.obtener_empresa_id_del_actor(vendedor)


def test_obtener_empresa_id_del_actor_sin_empresa(db: Session):
    """Test: ADMINISTRADOR sin empresa asignada no puede asociar recursos."""
    admin_sin_empresa = Usuario(
        nombre="Admin Sin Empresa",
        correo="admin_sinem@test.com",
        password_hash="fake_hash",
        rol=RolUsuario.ADMINISTRADOR,
        empresa_id=None,
        is_active=True,
    )
    db.add(admin_sin_empresa)
    db.commit()

    service = AsociacionesEmpresaService(db)

    with pytest.raises(UsuarioSinEmpresaError):
        service.obtener_empresa_id_del_actor(admin_sin_empresa)


def test_validar_empresa_id_correcto(db: Session):
    """Test: Validación tenant pasa cuando empresa_id coincide."""
    service = AsociacionesEmpresaService(db)
    # No debe lanzar excepción
    service.validar_empresa_id(1, 1)


def test_validar_empresa_id_incorrecto(db: Session):
    """Test: Validación tenant falla cuando empresa_id no coincide."""
    service = AsociacionesEmpresaService(db)

    with pytest.raises(TenantViolationError):
        service.validar_empresa_id(1, 2)


def test_validar_empresa_id_none(db: Session):
    """Test: Validación tenant falla si recurso no tiene empresa."""
    service = AsociacionesEmpresaService(db)

    with pytest.raises(TenantViolationError):
        service.validar_empresa_id(None, 1)


def test_asignar_empresa_al_usuario(db: Session):
    """Test: Asignar empresa a usuario nuevo."""
    usuario = Usuario(
        nombre="Usuario Nuevo",
        correo="nuevo@test.com",
        password_hash="fake_hash",
        rol=RolUsuario.CAJERO,
        is_active=True,
    )

    service = AsociacionesEmpresaService(db)
    service.asignar_empresa_al_usuario(usuario, 2)

    assert usuario.empresa_id == 2


def test_asignar_empresa_a_sucursal(db: Session):
    """Test: Asignar empresa a sucursal nueva."""
    sucursal = Sucursal(
        nombre="Sucursal Nueva",
        ciudad_id=1,
        direccion="Calle 123",
        telefono="555-1234",
        is_active=True,
    )

    service = AsociacionesEmpresaService(db)
    service.asignar_empresa_a_sucursal(sucursal, 3)

    assert sucursal.empresa_id == 3
