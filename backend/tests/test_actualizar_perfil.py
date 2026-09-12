"""Pruebas de CU04 - Actualizar perfil."""

import uuid

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

client = TestClient(app)


def _create_test_user(
    correo: str,
    password: str = "ClaveSegura123!",
    rol: RolUsuario = RolUsuario.CLIENTE,
    telefono: str | None = "70011111",
    nombre: str = "Usuario de prueba",
) -> Usuario:
    db = SessionLocal()
    try:
        usuario = Usuario(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            password_hash=hash_password(password),
            rol=rol,
            is_active=True,
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


def _login(correo: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"correo": correo, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_obtener_mi_perfil_devuelve_los_datos_reales_del_usuario_autenticado():
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario = _create_test_user(correo, nombre="Cliente Real", telefono="71122334")

    try:
        token = _login(correo, "ClaveSegura123!")
        response = client.get("/api/v1/auth/me", headers=_auth_headers(token))

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == usuario.id
        assert body["nombre"] == "Cliente Real"
        assert body["correo"] == correo
        assert body["telefono"] == "71122334"
        assert body["rol"] == "CLIENTE"
        assert "password" not in body
        assert "password_hash" not in body
    finally:
        _delete_test_user(usuario.id)


def test_obtener_mi_perfil_sin_autenticacion_es_rechazado():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_actualizar_mi_perfil_persiste_los_cambios_permitidos():
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario = _create_test_user(correo)

    try:
        token = _login(correo, "ClaveSegura123!")
        nuevo_correo = f"actualizado-{uuid.uuid4().hex[:8]}@fashionstore.com"

        response = client.put(
            "/api/v1/auth/me",
            headers=_auth_headers(token),
            json={"nombre": "Nombre Actualizado", "correo": nuevo_correo, "telefono": "70099999"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["nombre"] == "Nombre Actualizado"
        assert body["correo"] == nuevo_correo
        assert body["telefono"] == "70099999"

        # Recargar (nueva petición GET) y comprobar persistencia real en BD.
        recargado = client.get("/api/v1/auth/me", headers=_auth_headers(token))
        assert recargado.status_code == 200
        assert recargado.json()["nombre"] == "Nombre Actualizado"
        assert recargado.json()["correo"] == nuevo_correo
        assert recargado.json()["telefono"] == "70099999"

        # CU01 sigue permitiendo iniciar sesión (la contraseña no cambió).
        login_ok = client.post(
            "/api/v1/auth/login", json={"correo": nuevo_correo, "password": "ClaveSegura123!"}
        )
        assert login_ok.status_code == 200
    finally:
        _delete_test_user(usuario.id)


def test_actualizar_mi_perfil_no_modifica_a_otro_usuario():
    correo_a = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    correo_b = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario_a = _create_test_user(correo_a, nombre="Usuario A")
    usuario_b = _create_test_user(correo_b, nombre="Usuario B")

    try:
        token_a = _login(correo_a, "ClaveSegura123!")
        client.put(
            "/api/v1/auth/me",
            headers=_auth_headers(token_a),
            json={"nombre": "A Modificado", "correo": correo_a, "telefono": "70011111"},
        )

        db = SessionLocal()
        try:
            b_sin_tocar = db.get(Usuario, usuario_b.id)
            assert b_sin_tocar.nombre == "Usuario B"
            assert b_sin_tocar.correo == correo_b
        finally:
            db.close()
    finally:
        _delete_test_user(usuario_a.id)
        _delete_test_user(usuario_b.id)


def test_actualizar_mi_perfil_ignora_intentos_de_manipular_id_rol_o_permisos():
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    otro_correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario = _create_test_user(correo)
    otro_usuario = _create_test_user(otro_correo, nombre="Otro usuario")

    try:
        token = _login(correo, "ClaveSegura123!")

        # Intenta inyectar id de otro usuario, rol, sucursal_id, is_active,
        # etc. -- ninguno de estos campos existe en ActualizarPerfilRequest,
        # así que Pydantic los descarta silenciosamente.
        response = client.put(
            "/api/v1/auth/me",
            headers=_auth_headers(token),
            json={
                "id": otro_usuario.id,
                "nombre": "Nombre válido",
                "correo": correo,
                "telefono": "70011111",
                "rol": "ADMINISTRADOR",
                "is_active": False,
                "sucursal_id": 1,
                "proveedor_id": 1,
            },
        )

        assert response.status_code == 200
        body = response.json()
        # Se editó SU propio perfil (mismo id de siempre), no el de "otro_usuario".
        assert body["id"] == usuario.id
        assert body["rol"] == "CLIENTE"

        db = SessionLocal()
        try:
            propio = db.get(Usuario, usuario.id)
            ajeno = db.get(Usuario, otro_usuario.id)
            assert propio.rol == RolUsuario.CLIENTE
            assert propio.is_active is True
            assert ajeno.nombre == "Otro usuario"  # intacto
        finally:
            db.close()
    finally:
        _delete_test_user(usuario.id)
        _delete_test_user(otro_usuario.id)


def test_actualizar_mi_perfil_con_correo_de_otro_usuario_es_rechazado():
    correo_a = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    correo_b = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario_a = _create_test_user(correo_a)
    usuario_b = _create_test_user(correo_b)

    try:
        token_a = _login(correo_a, "ClaveSegura123!")
        response = client.put(
            "/api/v1/auth/me",
            headers=_auth_headers(token_a),
            json={"nombre": "Usuario A", "correo": correo_b, "telefono": "70011111"},
        )
        assert response.status_code == 409
    finally:
        _delete_test_user(usuario_a.id)
        _delete_test_user(usuario_b.id)


def test_actualizar_mi_perfil_puede_conservar_su_propio_correo():
    correo = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    usuario = _create_test_user(correo)

    try:
        token = _login(correo, "ClaveSegura123!")
        response = client.put(
            "/api/v1/auth/me",
            headers=_auth_headers(token),
            json={"nombre": "Nombre Nuevo", "correo": correo, "telefono": "70011111"},
        )
        assert response.status_code == 200
        assert response.json()["correo"] == correo
    finally:
        _delete_test_user(usuario.id)


def test_admin_y_encargado_siguen_pudiendo_usar_mi_perfil_normalmente():
    correo_admin = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    correo_encargado = f"test-{uuid.uuid4().hex[:8]}@fashionstore.com"
    admin = _create_test_user(correo_admin, rol=RolUsuario.ADMINISTRADOR, telefono=None)
    encargado = _create_test_user(correo_encargado, rol=RolUsuario.ENCARGADO_SUCURSAL, telefono=None)

    try:
        token_admin = _login(correo_admin, "ClaveSegura123!")
        token_encargado = _login(correo_encargado, "ClaveSegura123!")

        r1 = client.get("/api/v1/auth/me", headers=_auth_headers(token_admin))
        r2 = client.get("/api/v1/auth/me", headers=_auth_headers(token_encargado))

        assert r1.status_code == 200
        assert r1.json()["rol"] == "ADMINISTRADOR"
        assert r2.status_code == 200
        assert r2.json()["rol"] == "ENCARGADO_SUCURSAL"
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(encargado.id)
