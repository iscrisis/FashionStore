"""Pruebas de CU05 - Gestionar usuarios y roles."""

import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P2_UsuariosYAccesos.CU05_GestionarUsuariosRoles.repository import (
    UsuariosRolesRepository,
)
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

client = TestClient(app)


def _create_test_user(rol: RolUsuario, is_active: bool = True) -> Usuario:
    db = SessionLocal()
    try:
        usuario = Usuario(
            nombre="Usuario de prueba",
            correo=f"test-{uuid.uuid4().hex[:10]}@fashionstore.com",
            password_hash=hash_password("ClaveSegura123!"),
            rol=rol,
            is_active=is_active,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    finally:
        db.close()


def _delete_test_user(usuario_id: int) -> None:
    db = SessionLocal()
    try:
        usuario = db.get(Usuario, usuario_id)
        if usuario is not None:
            db.delete(usuario)
            db.commit()
    finally:
        db.close()


def _auth_headers(usuario: Usuario) -> dict:
    token = create_access_token(subject=str(usuario.id), extra_claims={"rol": usuario.rol.value})
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_listar_usuarios_sin_token_es_rechazado():
    response = client.get("/api/v1/usuarios")
    assert response.status_code == 401


def test_listar_usuarios_con_rol_no_autorizado_es_rechazado():
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.get("/api/v1/usuarios", headers=_auth_headers(cajero))
        assert response.status_code == 403
    finally:
        _delete_test_user(cajero.id)


def test_administrador_autorizado_si_puede_listar():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get("/api/v1/usuarios", headers=_auth_headers(admin))
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Listado / búsqueda / filtros
# --------------------------------------------------------------------------


def test_listar_usuarios_filtra_por_rol_y_busqueda():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        headers = _auth_headers(admin)

        respuesta_rol = client.get("/api/v1/usuarios?rol=CAJERO", headers=headers)
        assert respuesta_rol.status_code == 200
        correos = [u["correo"] for u in respuesta_rol.json()]
        assert cajero.correo in correos
        assert admin.correo not in correos

        respuesta_busqueda = client.get(
            f"/api/v1/usuarios?search={cajero.correo.split('@')[0]}", headers=headers
        )
        assert respuesta_busqueda.status_code == 200
        assert any(u["correo"] == cajero.correo for u in respuesta_busqueda.json())
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(cajero.id)


# --------------------------------------------------------------------------
# Crear usuario interno
# --------------------------------------------------------------------------


def test_crear_usuario_interno_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    correo_nuevo = f"nuevo-{uuid.uuid4().hex[:8]}@fashionstore.com"
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Juan Pérez",
                "correo": correo_nuevo,
                "password": "ClaveSegura123!",
                "rol": "ENCARGADO_SUCURSAL",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["correo"] == correo_nuevo
        assert body["rol"] == "ENCARGADO_SUCURSAL"
        assert body["is_active"] is True
        assert "password" not in body
        assert "password_hash" not in body
    finally:
        _delete_test_user(admin.id)
        creado = SessionLocal()
        try:
            existente = UsuariosRolesRepository(creado).get_by_correo(correo_nuevo)
            if existente:
                _delete_test_user(existente.id)
        finally:
            creado.close()


def test_crear_usuario_con_correo_duplicado_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    existente = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Duplicado",
                "correo": existente.correo,
                "password": "ClaveSegura123!",
                "rol": "CAJERO",
            },
        )
        assert response.status_code == 409
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(existente.id)


def test_crear_usuario_con_rol_cliente_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Cliente Intento",
                "correo": f"cliente-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "ClaveSegura123!",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Editar datos básicos
# --------------------------------------------------------------------------


def test_editar_datos_basicos_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    objetivo = _create_test_user(RolUsuario.CAJERO)
    try:
        nuevo_correo = f"editado-{uuid.uuid4().hex[:8]}@fashionstore.com"
        response = client.put(
            f"/api/v1/usuarios/{objetivo.id}",
            headers=_auth_headers(admin),
            json={"nombre": "Nombre Editado", "correo": nuevo_correo},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["nombre"] == "Nombre Editado"
        assert body["correo"] == nuevo_correo
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)


# --------------------------------------------------------------------------
# Cambiar rol
# --------------------------------------------------------------------------


def test_cambiar_rol_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    objetivo = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.patch(
            f"/api/v1/usuarios/{objetivo.id}/rol",
            headers=_auth_headers(admin),
            json={"rol": "ENCARGADO_SUCURSAL"},
        )
        assert response.status_code == 200
        assert response.json()["rol"] == "ENCARGADO_SUCURSAL"
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)


def test_auto_degradarse_siendo_el_unico_administrador_activo_es_rechazado(monkeypatch):
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    monkeypatch.setattr(
        "modules.P2_UsuariosYAccesos.CU05_GestionarUsuariosRoles.repository."
        "UsuariosRolesRepository.contar_administradores_activos",
        lambda self, excluyendo_id=None: 0,
    )
    try:
        response = client.patch(
            f"/api/v1/usuarios/{admin.id}/rol",
            headers=_auth_headers(admin),
            json={"rol": "CAJERO"},
        )
        assert response.status_code == 400
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Activar / desactivar
# --------------------------------------------------------------------------


def test_activar_desactivar_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    objetivo = _create_test_user(RolUsuario.CAJERO)
    try:
        desactivar = client.patch(
            f"/api/v1/usuarios/{objetivo.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert desactivar.status_code == 200
        assert desactivar.json()["is_active"] is False

        activar = client.patch(
            f"/api/v1/usuarios/{objetivo.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": True},
        )
        assert activar.status_code == 200
        assert activar.json()["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)


def test_no_puede_desactivar_su_propia_cuenta():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.patch(
            f"/api/v1/usuarios/{admin.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert response.status_code == 400
    finally:
        _delete_test_user(admin.id)


def test_usuario_desactivado_no_puede_iniciar_sesion_luego_de_cu05():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    objetivo = _create_test_user(RolUsuario.CAJERO)
    try:
        client.patch(
            f"/api/v1/usuarios/{objetivo.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"correo": objetivo.correo, "password": "ClaveSegura123!"},
        )
        assert login.status_code == 403
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)
