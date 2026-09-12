"""Pruebas de CU03 - Recuperar contraseña.

El envío SMTP real se mockea (monkeypatch sobre enviar_correo) para que la
suite automatizada no dependa de un servidor de correo real ni de
credenciales -- el envío real se prueba manualmente (ver checklist de
pruebas manuales entregado junto con esta implementación).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password, verify_password
from app.db.session import SessionLocal
from app.main import app
from modules.P2_UsuariosYAccesos.CU03_RecuperarContrasena import service as reset_service
from modules.P2_UsuariosYAccesos.Models.password_reset_token import PasswordResetToken
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

client = TestClient(app)


@pytest.fixture(autouse=True)
def _mock_envio_correo(monkeypatch):
    enviados: list[dict] = []

    def _fake_enviar_correo(destinatario, asunto, cuerpo_html, cuerpo_texto):
        enviados.append({"destinatario": destinatario, "asunto": asunto, "cuerpo": cuerpo_texto})

    monkeypatch.setattr(reset_service, "enviar_correo", _fake_enviar_correo)
    return enviados


def _create_test_user(correo: str, password: str, is_active: bool = True) -> Usuario:
    db = SessionLocal()
    try:
        usuario = Usuario(
            nombre="Usuario de prueba",
            correo=correo,
            password_hash=hash_password(password),
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
        db.query(PasswordResetToken).filter(PasswordResetToken.usuario_id == usuario_id).delete()
        usuario = db.get(Usuario, usuario_id)
        if usuario is not None:
            db.delete(usuario)
        db.commit()
    finally:
        db.close()


def _extraer_token_del_correo(cuerpo_texto: str) -> str:
    for linea in cuerpo_texto.splitlines():
        if "token=" in linea:
            return linea.split("token=", 1)[1].strip()
    raise AssertionError("El correo simulado no contiene un enlace con token.")


def test_forgot_password_con_correo_existente_responde_mensaje_generico_y_envia_correo(
    _mock_envio_correo,
):
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario = _create_test_user(correo, "ClaveSegura123!")

    try:
        response = client.post("/api/v1/auth/forgot-password", json={"correo": correo})

        assert response.status_code == 200
        assert "Si existe una cuenta" in response.json()["message"]
        assert len(_mock_envio_correo) == 1
        assert _mock_envio_correo[0]["destinatario"] == correo
    finally:
        _delete_test_user(usuario.id)


def test_forgot_password_con_correo_inexistente_responde_el_mismo_mensaje_generico_sin_enviar_correo(
    _mock_envio_correo,
):
    response = client.post(
        "/api/v1/auth/forgot-password", json={"correo": "no-existe@fashionstore.com"}
    )

    assert response.status_code == 200
    assert "Si existe una cuenta" in response.json()["message"]
    assert len(_mock_envio_correo) == 0


def test_flujo_completo_reset_password_permite_login_con_la_nueva_contrasena(_mock_envio_correo):
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    password_original = "ClaveOriginal123!"
    password_nueva = "ClaveNueva456!"
    usuario = _create_test_user(correo, password_original)

    try:
        client.post("/api/v1/auth/forgot-password", json={"correo": correo})
        token = _extraer_token_del_correo(_mock_envio_correo[0]["cuerpo"])

        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": password_nueva,
                "confirmar_password": password_nueva,
            },
        )
        assert response.status_code == 200

        # CU01 debe aceptar la nueva contraseña...
        login_ok = client.post(
            "/api/v1/auth/login", json={"correo": correo, "password": password_nueva}
        )
        assert login_ok.status_code == 200

        # ...y la anterior debe dejar de funcionar.
        login_viejo = client.post(
            "/api/v1/auth/login", json={"correo": correo, "password": password_original}
        )
        assert login_viejo.status_code == 401

        # La contraseña se guarda con el mismo hash que usa CU01/CU02/CU05.
        db = SessionLocal()
        try:
            actualizado = db.get(Usuario, usuario.id)
            assert verify_password(password_nueva, actualizado.password_hash)
        finally:
            db.close()
    finally:
        _delete_test_user(usuario.id)


def test_reset_password_con_token_ya_usado_es_rechazado(_mock_envio_correo):
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario = _create_test_user(correo, "ClaveOriginal123!")

    try:
        client.post("/api/v1/auth/forgot-password", json={"correo": correo})
        token = _extraer_token_del_correo(_mock_envio_correo[0]["cuerpo"])

        primero = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "ClaveNueva456!", "confirmar_password": "ClaveNueva456!"},
        )
        assert primero.status_code == 200

        segundo = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "OtraClave789!", "confirmar_password": "OtraClave789!"},
        )
        assert segundo.status_code == 400
    finally:
        _delete_test_user(usuario.id)


def test_reset_password_con_token_expirado_es_rechazado(_mock_envio_correo):
    from datetime import datetime, timedelta, timezone

    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario = _create_test_user(correo, "ClaveOriginal123!")

    try:
        client.post("/api/v1/auth/forgot-password", json={"correo": correo})
        token = _extraer_token_del_correo(_mock_envio_correo[0]["cuerpo"])

        # Simula el paso del tiempo forzando la expiración del token recién creado.
        db = SessionLocal()
        try:
            registro = db.query(PasswordResetToken).filter(
                PasswordResetToken.usuario_id == usuario.id
            ).one()
            registro.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()

        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "ClaveNueva456!", "confirmar_password": "ClaveNueva456!"},
        )
        assert response.status_code == 400
    finally:
        _delete_test_user(usuario.id)


def test_reset_password_con_token_inexistente_es_rechazado():
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "token-que-no-existe",
            "new_password": "ClaveNueva456!",
            "confirmar_password": "ClaveNueva456!",
        },
    )
    assert response.status_code == 400


def test_reset_password_con_contrasenas_que_no_coinciden_es_rechazado_por_el_esquema():
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "cualquiera",
            "new_password": "ClaveNueva456!",
            "confirmar_password": "OtraDistinta789!",
        },
    )
    assert response.status_code == 422
