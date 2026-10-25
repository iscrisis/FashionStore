"""Pruebas de CU01 - Registrar empresa contratante."""

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa

client = TestClient(app)


def _limpiar_empresas() -> None:
    """Eliminar todas las empresas de prueba de la BD."""
    db = SessionLocal()
    try:
        empresas = db.query(Empresa).all()
        for empresa in empresas:
            db.delete(empresa)
        db.commit()
    finally:
        db.close()


def test_registrar_empresa_exitoso():
    """Caso de éxito: Registrar una empresa correctamente."""
    _limpiar_empresas()

    datos = {
        "nombre": "FashionCorp SA",
        "slug": "fashioncorp-sa",
        "razon_social": "FashionCorp Sociedad Anónima",
        "correo": "admin@fashioncorp.com",
        "telefono": "+591 2 1234567",
    }

    response = client.post("/api/v1/empresas", json=datos)

    assert response.status_code == 201
    json_response = response.json()
    assert json_response["nombre"] == "FashionCorp SA"
    assert json_response["slug"] == "fashioncorp-sa"
    assert json_response["razon_social"] == "FashionCorp Sociedad Anónima"
    assert json_response["correo"] == "admin@fashioncorp.com"
    assert json_response["telefono"] == "+591 2 1234567"
    assert json_response["is_active"] is True
    assert "id" in json_response
    assert "created_at" in json_response
    assert "updated_at" in json_response


def test_registrar_empresa_nombre_duplicado():
    """Caso de error: Intentar registrar con nombre duplicado."""
    _limpiar_empresas()

    datos1 = {
        "nombre": "UniqueCoorp SA",
        "slug": "uniquecorp-sa-1",
        "razon_social": "UniqueCoorp Sociedad Anónima",
        "correo": "admin@uniquecorp1.com",
        "telefono": "+591 2 1111111",
    }

    datos2 = {
        "nombre": "UniqueCoorp SA",  # Mismo nombre
        "slug": "uniquecorp-sa-2",
        "razon_social": "Otra Razón Social",
        "correo": "admin@uniquecorp2.com",
        "telefono": "+591 2 2222222",
    }

    # Registrar la primera
    response1 = client.post("/api/v1/empresas", json=datos1)
    assert response1.status_code == 201

    # Intentar registrar la segunda con nombre duplicado
    response2 = client.post("/api/v1/empresas", json=datos2)
    assert response2.status_code == 409
    assert "nombre" in response2.json()["detail"].lower()


def test_registrar_empresa_slug_duplicado():
    """Caso de error: Intentar registrar con slug duplicado."""
    _limpiar_empresas()

    datos1 = {
        "nombre": "EliteShop SA",
        "slug": "eliteshop-sa",
        "razon_social": "EliteShop Sociedad Anónima",
        "correo": "admin@eliteshop1.com",
        "telefono": "+591 2 3333333",
    }

    datos2 = {
        "nombre": "Elite Shop SRL",  # Nombre diferente
        "slug": "eliteshop-sa",  # Mismo slug
        "razon_social": "Elite Shop Sociedad de Responsabilidad Limitada",
        "correo": "admin@eliteshop2.com",
        "telefono": "+591 2 4444444",
    }

    # Registrar la primera
    response1 = client.post("/api/v1/empresas", json=datos1)
    assert response1.status_code == 201

    # Intentar registrar la segunda con slug duplicado
    response2 = client.post("/api/v1/empresas", json=datos2)
    assert response2.status_code == 409
    assert "slug" in response2.json()["detail"].lower()


def test_registrar_empresa_nombre_vacio():
    """Caso de validación: Nombre vacío o muy corto."""
    _limpiar_empresas()

    datos = {
        "nombre": "A",  # Menos de 2 caracteres
        "slug": "a-shop",
        "razon_social": "A Shop",
        "correo": "admin@ashop.com",
        "telefono": "+591 2 5555555",
    }

    response = client.post("/api/v1/empresas", json=datos)
    assert response.status_code == 422  # Validación fallida


def test_registrar_empresa_slug_invalido():
    """Caso de validación: Slug con caracteres inválidos."""
    _limpiar_empresas()

    datos = {
        "nombre": "ProShop SA",
        "slug": "pro shop!",  # Espacios y símbolos no permitidos
        "razon_social": "Pro Shop",
        "correo": "admin@proshop.com",
        "telefono": "+591 2 6666666",
    }

    response = client.post("/api/v1/empresas", json=datos)
    assert response.status_code == 422  # Validación fallida


def test_registrar_empresa_correo_invalido():
    """Caso de validación: Email inválido."""
    _limpiar_empresas()

    datos = {
        "nombre": "TechStore SA",
        "slug": "techstore-sa",
        "razon_social": "Tech Store",
        "correo": "not-an-email",  # Email inválido
        "telefono": "+591 2 7777777",
    }

    response = client.post("/api/v1/empresas", json=datos)
    assert response.status_code == 422  # Validación fallida


def test_registrar_empresa_telefono_invalido():
    """Caso de validación: Teléfono inválido."""
    _limpiar_empresas()

    datos = {
        "nombre": "MediaShop SA",
        "slug": "mediashop-sa",
        "razon_social": "Media Shop",
        "correo": "admin@mediashop.com",
        "telefono": "abc",  # Teléfono con menos de 6 caracteres
    }

    response = client.post("/api/v1/empresas", json=datos)
    assert response.status_code == 422  # Validación fallida


def test_registrar_empresa_persistencia():
    """Caso de integración: Verificar que la empresa se persista en BD."""
    _limpiar_empresas()

    datos = {
        "nombre": "DataCorp SA",
        "slug": "datacorp-sa",
        "razon_social": "Data Corporation",
        "correo": "admin@datacorp.com",
        "telefono": "+591 2 8888888",
    }

    response = client.post("/api/v1/empresas", json=datos)
    assert response.status_code == 201
    empresa_id = response.json()["id"]

    # Verificar en BD
    db = SessionLocal()
    try:
        empresa = db.get(Empresa, empresa_id)
        assert empresa is not None
        assert empresa.nombre == "DataCorp SA"
        assert empresa.slug == "datacorp-sa"
        assert empresa.is_active is True
    finally:
        db.close()


def test_registrar_empresa_response_estructura():
    """Caso de validación: Estructura de respuesta."""
    _limpiar_empresas()

    datos = {
        "nombre": "ResponseTest SA",
        "slug": "responsetest-sa",
        "razon_social": "Response Test Corp",
        "correo": "admin@responsetest.com",
        "telefono": "+591 2 9999999",
    }

    response = client.post("/api/v1/empresas", json=datos)
    assert response.status_code == 201

    json_response = response.json()
    requeridos = ["id", "nombre", "slug", "razon_social", "correo", "telefono", "is_active", "created_at", "updated_at"]
    for campo in requeridos:
        assert campo in json_response, f"Campo '{campo}' faltante en respuesta"
