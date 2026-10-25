"""Pruebas de CU02 — Gestionar administrador de empresa."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.main import app
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario


client = TestClient(app)


@pytest.fixture
def db_session(monkeypatch):
    """Fixture de sesión de BD para tests."""
    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def setup_data(db_session: Session):
    """Setup: crear empresa, administrador y SUPERADMIN para tests."""

    # Crear SUPERADMIN
    superadmin = Usuario(
        nombre="Admin Plataforma",
        correo="superadmin@platform.com",
        password_hash=hash_password("password123"),
        rol=RolUsuario.SUPERADMIN,
        empresa_id=None,
        is_active=True,
    )
    db_session.add(superadmin)
    db_session.flush()

    # Crear empresa
    empresa = Empresa(
        nombre="Test Company",
        slug="test-company",
        razon_social="Test Company SA",
        correo="contact@testco.com",
        telefono="+591 1234567",
        is_active=True,
    )
    db_session.add(empresa)
    db_session.flush()

    # Crear administrador de la empresa
    admin_empresa = Usuario(
        nombre="Admin Empresa",
        correo="admin@testco.com",
        password_hash=hash_password("password123"),
        rol=RolUsuario.ADMINISTRADOR,
        empresa_id=empresa.id,
        is_active=True,
    )
    db_session.add(admin_empresa)
    db_session.commit()

    return {
        "superadmin": superadmin,
        "empresa": empresa,
        "administrador": admin_empresa,
    }


class TestConsultarAdministrador:
    """Pruebas para GET /empresas/{empresa_id}/administrador."""

    def test_consultar_administrador_exitoso(self, setup_data):
        """Test: SUPERADMIN consulta administrador de una empresa."""
        data = setup_data
        empresa_id = data["empresa"].id

        # Obtener token JWT para SUPERADMIN
        response = client.post(
            "/api/v1/auth/login",
            json={
                "correo": "superadmin@platform.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Consultar administrador
        response = client.get(
            f"/api/v1/empresas/{empresa_id}/administrador",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data_resp = response.json()
        assert data_resp["empresa"]["id"] == empresa_id
        assert data_resp["administrador"]["rol"] == "ADMINISTRADOR"
        assert data_resp["administrador"]["empresa_id"] == empresa_id

    def test_consultar_empresa_no_existe(self, setup_data):
        """Test: Consultar administrador de empresa inexistente."""
        data = setup_data

        response = client.post(
            "/api/v1/auth/login",
            json={
                "correo": "superadmin@platform.com",
                "password": "password123",
            },
        )
        token = response.json()["access_token"]

        response = client.get(
            "/api/v1/empresas/9999/administrador",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "empresa no existe" in response.json()["detail"].lower()

    def test_consultar_sin_autenticacion(self, setup_data):
        """Test: Intento sin token de autenticación."""
        data = setup_data
        empresa_id = data["empresa"].id

        response = client.get(f"/api/v1/empresas/{empresa_id}/administrador")

        assert response.status_code == 401

    def test_consultar_sin_ser_superadmin(self, setup_data):
        """Test: ADMINISTRADOR intenta consultar (no SUPERADMIN)."""
        data = setup_data
        empresa_id = data["empresa"].id

        response = client.post(
            "/api/v1/auth/login",
            json={
                "correo": "admin@testco.com",
                "password": "password123",
            },
        )
        token = response.json()["access_token"]

        response = client.get(
            f"/api/v1/empresas/{empresa_id}/administrador",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403


class TestActualizarAdministrador:
    """Pruebas para PUT /empresas/{empresa_id}/administrador."""

    def test_actualizar_administrador_exitoso(self, setup_data):
        """Test: SUPERADMIN actualiza datos permitidos del administrador."""
        data = setup_data
        empresa_id = data["empresa"].id

        response = client.post(
            "/api/v1/auth/login",
            json={
                "correo": "superadmin@platform.com",
                "password": "password123",
            },
        )
        token = response.json()["access_token"]

        # Actualizar administrador
        response = client.put(
            f"/api/v1/empresas/{empresa_id}/administrador",
            json={
                "nombre": "Admin Empresa Actualizado",
                "correo": "newemail@testco.com",
                "is_active": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data_resp = response.json()
        assert data_resp["administrador"]["nombre"] == "Admin Empresa Actualizado"
        assert data_resp["administrador"]["correo"] == "newemail@testco.com"
        assert data_resp["administrador"]["empresa_id"] == empresa_id  # No cambió

    def test_actualizar_preserva_empresa_id(self, setup_data):
        """Test: empresa_id se preserva después de actualización."""
        data = setup_data
        empresa_id = data["empresa"].id
        admin_original_empresa = data["administrador"].empresa_id

        response = client.post(
            "/api/v1/auth/login",
            json={
                "correo": "superadmin@platform.com",
                "password": "password123",
            },
        )
        token = response.json()["access_token"]

        client.put(
            f"/api/v1/empresas/{empresa_id}/administrador",
            json={
                "nombre": "Nombre Nueva",
                "correo": "otra@testco.com",
                "is_active": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Verificar que empresa_id no cambió
        response = client.get(
            f"/api/v1/empresas/{empresa_id}/administrador",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["administrador"]["empresa_id"] == admin_original_empresa

    def test_actualizar_correo_duplicado(self, setup_data, db_session: Session):
        """Test: Intento de usar correo que ya existe."""
        data = setup_data
        empresa_id = data["empresa"].id

        # Crear otro usuario con correo que intenta reutilizarse
        otro_usuario = Usuario(
            nombre="Otro Usuario",
            correo="otrousuario@domain.com",
            password_hash=hash_password("password123"),
            rol=RolUsuario.CLIENTE,
            empresa_id=None,
            is_active=True,
        )
        db_session.add(otro_usuario)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "correo": "superadmin@platform.com",
                "password": "password123",
            },
        )
        token = response.json()["access_token"]

        response = client.put(
            f"/api/v1/empresas/{empresa_id}/administrador",
            json={
                "nombre": "Admin",
                "correo": "otrousuario@domain.com",
                "is_active": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 409
        assert "correo" in response.json()["detail"].lower()

    def test_actualizar_sin_ser_superadmin(self, setup_data):
        """Test: ADMINISTRADOR intenta actualizar (no SUPERADMIN)."""
        data = setup_data
        empresa_id = data["empresa"].id

        response = client.post(
            "/api/v1/auth/login",
            json={
                "correo": "admin@testco.com",
                "password": "password123",
            },
        )
        token = response.json()["access_token"]

        response = client.put(
            f"/api/v1/empresas/{empresa_id}/administrador",
            json={
                "nombre": "Nuevo Nombre",
                "correo": "nuevo@testco.com",
                "is_active": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    def test_actualizar_nombre_inválido(self, setup_data):
        """Test: Validación de nombre (mínimo 2 caracteres)."""
        data = setup_data
        empresa_id = data["empresa"].id

        response = client.post(
            "/api/v1/auth/login",
            json={
                "correo": "superadmin@platform.com",
                "password": "password123",
            },
        )
        token = response.json()["access_token"]

        response = client.put(
            f"/api/v1/empresas/{empresa_id}/administrador",
            json={
                "nombre": "A",  # Muy corto
                "correo": "admin@testco.com",
                "is_active": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_actualizar_empresa_inexistente(self, setup_data):
        """Test: Actualizar administrador de empresa que no existe."""
        data = setup_data

        response = client.post(
            "/api/v1/auth/login",
            json={
                "correo": "superadmin@platform.com",
                "password": "password123",
            },
        )
        token = response.json()["access_token"]

        response = client.put(
            "/api/v1/empresas/9999/administrador",
            json={
                "nombre": "Nombre",
                "correo": "email@domain.com",
                "is_active": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
