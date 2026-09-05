"""Pruebas de CU01 - Iniciar sesión."""

import uuid

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

client = TestClient(app)


def _create_test_user(correo: str, password: str, is_active: bool = True) -> Usuario:
    db = SessionLocal()
    try:
        usuario = Usuario(
            nombre="Usuario de prueba",
            correo=correo,
            password_hash=hash_password(password),
            rol=RolUsuario.ADMINISTRADOR,
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


def test_login_con_credenciales_correctas_devuelve_token_y_usuario():
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    password = "ClaveSegura123!"
    usuario = _create_test_user(correo, password)

    try:
        response = client.post("/api/v1/auth/login", json={"correo": correo, "password": password})

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["usuario"]["correo"] == correo
        assert body["usuario"]["rol"] == "ADMINISTRADOR"
        assert "password" not in body["usuario"]
        assert "password_hash" not in body["usuario"]
    finally:
        _delete_test_user(usuario.id)


def test_login_con_contrasena_incorrecta_es_rechazado():
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario = _create_test_user(correo, "ClaveCorrecta123!")

    try:
        response = client.post("/api/v1/auth/login", json={"correo": correo, "password": "incorrecta"})
        assert response.status_code == 401
    finally:
        _delete_test_user(usuario.id)


def test_login_con_correo_inexistente_es_rechazado():
    response = client.post(
        "/api/v1/auth/login",
        json={"correo": "no-existe@fashionstore.com", "password": "cualquiera"},
    )
    assert response.status_code == 401


def test_login_con_usuario_inactivo_es_rechazado():
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario = _create_test_user(correo, "ClaveSegura123!", is_active=False)

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"correo": correo, "password": "ClaveSegura123!"},
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(usuario.id)
