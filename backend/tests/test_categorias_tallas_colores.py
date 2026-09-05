"""Pruebas de CU09 - Gestionar categorías, tallas y colores.

Las tres entidades comparten la misma API (nombre + estado), así que las
pruebas se parametrizan por prefijo de endpoint en vez de triplicar cada caso.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.image_storage import UPLOADS_ROOT
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

client = TestClient(app)

_MODELOS = {"categorias": Categoria, "tallas": Talla, "colores": Color}


def _create_test_user(rol: RolUsuario) -> Usuario:
    db = SessionLocal()
    try:
        usuario = Usuario(
            nombre="Usuario de prueba",
            correo=f"test-{uuid.uuid4().hex[:10]}@fashionstore.com",
            password_hash=hash_password("ClaveSegura123!"),
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


def _auth_headers(usuario: Usuario) -> dict:
    token = create_access_token(subject=str(usuario.id), extra_claims={"rol": usuario.rol.value})
    return {"Authorization": f"Bearer {token}"}


def _delete_registro(endpoint: str, registro_id: int) -> None:
    db = SessionLocal()
    try:
        registro = db.get(_MODELOS[endpoint], registro_id)
        if registro is not None:
            db.delete(registro)
            db.commit()
    finally:
        db.close()


@pytest.fixture(params=["categorias", "tallas", "colores"])
def endpoint(request) -> str:
    return request.param


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_listar_sin_token_es_rechazado(endpoint):
    response = client.get(f"/api/v1/{endpoint}")
    assert response.status_code == 401


def test_listar_con_rol_no_autorizado_es_rechazado(endpoint):
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.get(f"/api/v1/{endpoint}", headers=_auth_headers(cajero))
        assert response.status_code == 403
    finally:
        _delete_test_user(cajero.id)


def test_administrador_autorizado_si_puede_listar(endpoint):
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get(f"/api/v1/{endpoint}", headers=_auth_headers(admin))
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Registrar
# --------------------------------------------------------------------------


def test_crear_ok(endpoint):
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    nombre = f"Registro {uuid.uuid4().hex[:8]}"
    registro_id = None
    try:
        response = client.post(
            f"/api/v1/{endpoint}", headers=_auth_headers(admin), json={"nombre": nombre}
        )
        assert response.status_code == 201
        body = response.json()
        registro_id = body["id"]
        assert body["nombre"] == nombre
        assert body["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        if registro_id:
            _delete_registro(endpoint, registro_id)


def test_crear_con_nombre_duplicado_es_rechazado(endpoint):
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    nombre = f"Registro {uuid.uuid4().hex[:8]}"
    primero = client.post(f"/api/v1/{endpoint}", headers=_auth_headers(admin), json={"nombre": nombre})
    registro_id = primero.json()["id"]
    try:
        duplicado = client.post(
            f"/api/v1/{endpoint}", headers=_auth_headers(admin), json={"nombre": nombre.upper()}
        )
        assert duplicado.status_code == 409
    finally:
        _delete_test_user(admin.id)
        _delete_registro(endpoint, registro_id)


def test_crear_con_nombre_vacio_es_rechazado(endpoint):
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(f"/api/v1/{endpoint}", headers=_auth_headers(admin), json={"nombre": "   "})
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Editar
# --------------------------------------------------------------------------


def test_editar_ok(endpoint):
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    creado = client.post(
        f"/api/v1/{endpoint}",
        headers=_auth_headers(admin),
        json={"nombre": f"Original {uuid.uuid4().hex[:8]}"},
    )
    registro_id = creado.json()["id"]
    try:
        nuevo_nombre = f"Editado {uuid.uuid4().hex[:8]}"
        response = client.put(
            f"/api/v1/{endpoint}/{registro_id}",
            headers=_auth_headers(admin),
            json={"nombre": nuevo_nombre},
        )
        assert response.status_code == 200
        assert response.json()["nombre"] == nuevo_nombre
    finally:
        _delete_test_user(admin.id)
        _delete_registro(endpoint, registro_id)


def test_editar_inexistente_es_rechazado(endpoint):
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.put(
            f"/api/v1/{endpoint}/9999999",
            headers=_auth_headers(admin),
            json={"nombre": "No existe"},
        )
        assert response.status_code == 404
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Activar / desactivar
# --------------------------------------------------------------------------


def test_activar_desactivar_ok(endpoint):
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    creado = client.post(
        f"/api/v1/{endpoint}",
        headers=_auth_headers(admin),
        json={"nombre": f"Estado {uuid.uuid4().hex[:8]}"},
    )
    registro_id = creado.json()["id"]
    try:
        desactivar = client.patch(
            f"/api/v1/{endpoint}/{registro_id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert desactivar.status_code == 200
        assert desactivar.json()["is_active"] is False

        activar = client.patch(
            f"/api/v1/{endpoint}/{registro_id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": True},
        )
        assert activar.status_code == 200
        assert activar.json()["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        _delete_registro(endpoint, registro_id)


# --------------------------------------------------------------------------
# Búsqueda / filtros
# --------------------------------------------------------------------------


def test_listar_filtra_por_busqueda_y_estado(endpoint):
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    alfa = client.post(
        f"/api/v1/{endpoint}", headers=_auth_headers(admin), json={"nombre": f"Alfa-{uuid.uuid4().hex[:6]}"}
    ).json()
    beta = client.post(
        f"/api/v1/{endpoint}", headers=_auth_headers(admin), json={"nombre": f"Beta-{uuid.uuid4().hex[:6]}"}
    ).json()
    client.patch(
        f"/api/v1/{endpoint}/{beta['id']}/estado", headers=_auth_headers(admin), json={"is_active": False}
    )
    try:
        headers = _auth_headers(admin)

        por_busqueda = client.get(f"/api/v1/{endpoint}?search=alfa", headers=headers)
        nombres = [r["nombre"] for r in por_busqueda.json()]
        assert alfa["nombre"] in nombres
        assert beta["nombre"] not in nombres

        por_estado = client.get(f"/api/v1/{endpoint}?estado=inactive", headers=headers)
        nombres_estado = [r["nombre"] for r in por_estado.json()]
        assert beta["nombre"] in nombres_estado
        assert alfa["nombre"] not in nombres_estado
    finally:
        _delete_test_user(admin.id)
        _delete_registro(endpoint, alfa["id"])
        _delete_registro(endpoint, beta["id"])


# --------------------------------------------------------------------------
# Imagen de categoría (opcional) -- exclusivo de Categoría, no de Talla/Color
# --------------------------------------------------------------------------

_CONTENIDO_IMAGEN_FALSA = b"contenido-de-prueba-no-es-una-imagen-real"


def test_categoria_creada_no_tiene_imagen_por_defecto():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    creada = client.post(
        "/api/v1/categorias", headers=_auth_headers(admin), json={"nombre": f"Cat {uuid.uuid4().hex[:8]}"}
    )
    categoria_id = creada.json()["id"]
    try:
        assert creada.json()["imagen_url"] is None
    finally:
        _delete_test_user(admin.id)
        _delete_registro("categorias", categoria_id)


def test_establecer_y_quitar_imagen_de_categoria_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    creada = client.post(
        "/api/v1/categorias", headers=_auth_headers(admin), json={"nombre": f"Cat {uuid.uuid4().hex[:8]}"}
    )
    categoria_id = creada.json()["id"]
    try:
        establecida = client.post(
            f"/api/v1/categorias/{categoria_id}/imagen",
            headers=_auth_headers(admin),
            files={"archivo": ("foto.png", _CONTENIDO_IMAGEN_FALSA, "image/png")},
        )
        assert establecida.status_code == 200
        url = establecida.json()["imagen_url"]
        assert url is not None
        assert url.startswith("/api/v1/media/categorias/")
        ruta = UPLOADS_ROOT / url.removeprefix("/api/v1/media/")
        assert ruta.exists()

        quitada = client.delete(f"/api/v1/categorias/{categoria_id}/imagen", headers=_auth_headers(admin))
        assert quitada.status_code == 200
        assert quitada.json()["imagen_url"] is None
        assert not ruta.exists()
    finally:
        _delete_test_user(admin.id)
        _delete_registro("categorias", categoria_id)


def test_establecer_imagen_de_categoria_con_formato_invalido_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    creada = client.post(
        "/api/v1/categorias", headers=_auth_headers(admin), json={"nombre": f"Cat {uuid.uuid4().hex[:8]}"}
    )
    categoria_id = creada.json()["id"]
    try:
        response = client.post(
            f"/api/v1/categorias/{categoria_id}/imagen",
            headers=_auth_headers(admin),
            files={"archivo": ("archivo.txt", _CONTENIDO_IMAGEN_FALSA, "text/plain")},
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)
        _delete_registro("categorias", categoria_id)
