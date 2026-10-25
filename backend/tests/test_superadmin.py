"""Pruebas de SUPERADMIN — Rol de plataforma global."""

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario

client = TestClient(app)


def _limpiar_usuarios() -> None:
    """Eliminar todos los usuarios de prueba de la BD."""
    db = SessionLocal()
    try:
        usuarios = db.query(Usuario).all()
        for usuario in usuarios:
            db.delete(usuario)
        db.commit()
    finally:
        db.close()


def test_superadmin_empresa_id_null():
    """Caso: SUPERADMIN tiene empresa_id = NULL."""
    _limpiar_usuarios()

    from app.core.security import hash_password

    db = SessionLocal()
    try:
        superadmin = Usuario(
            nombre="Test SuperAdmin",
            correo="test-superadmin@fashionstore.com",
            password_hash=hash_password("testpass123"),
            rol=RolUsuario.SUPERADMIN,
            is_active=True,
            empresa_id=None,  # ← CRÍTICO
        )
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)

        # Verificar que se guardó correctamente
        assert superadmin.id is not None
        assert superadmin.rol == RolUsuario.SUPERADMIN
        assert superadmin.empresa_id is None
        assert superadmin.is_active is True
    finally:
        db.close()


def test_superadmin_login():
    """Caso: SUPERADMIN puede iniciar sesión."""
    _limpiar_usuarios()

    from app.core.security import hash_password

    db = SessionLocal()
    try:
        password_plain = "superadmin123"
        superadmin = Usuario(
            nombre="Test SuperAdmin",
            correo="superadmin@test.com",
            password_hash=hash_password(password_plain),
            rol=RolUsuario.SUPERADMIN,
            is_active=True,
            empresa_id=None,
        )
        db.add(superadmin)
        db.commit()
    finally:
        db.close()

    # Intentar login
    response = client.post("/api/v1/auth/login", json={
        "correo": "superadmin@test.com",
        "password": password_plain,
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "usuario" in data
    assert data["usuario"]["rol"] == "SUPERADMIN"


def test_administrador_no_es_superadmin():
    """Caso: ADMINISTRADOR existente no se convierte en SUPERADMIN."""
    _limpiar_usuarios()

    from app.core.security import hash_password
    from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa

    db = SessionLocal()
    try:
        # Crear empresa
        empresa = Empresa(
            nombre="Test Enterprise",
            slug="test-enterprise",
            razon_social="Test Enterprise Corp",
            correo="empresa@test.com",
            telefono="+591 123456789",
        )
        db.add(empresa)
        db.commit()
        db.refresh(empresa)

        # Crear ADMINISTRADOR asociado a la empresa
        admin = Usuario(
            nombre="Test Admin",
            correo="admin@test.com",
            password_hash=hash_password("admin123"),
            rol=RolUsuario.ADMINISTRADOR,
            is_active=True,
            empresa_id=empresa.id,  # ← Asociado a empresa
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        # Verificar
        assert admin.rol == RolUsuario.ADMINISTRADOR
        assert admin.empresa_id == empresa.id
        assert admin.empresa_id is not None
    finally:
        db.close()


def test_superadmin_vs_administrador():
    """Caso: Diferencia entre SUPERADMIN y ADMINISTRADOR."""
    _limpiar_usuarios()

    from app.core.security import hash_password
    from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa

    db = SessionLocal()
    try:
        # Crear empresa
        empresa = Empresa(
            nombre="Enterprise X",
            slug="enterprise-x",
            razon_social="Enterprise X Corp",
            correo="enterprisex@test.com",
            telefono="+591 999999999",
        )
        db.add(empresa)
        db.commit()
        db.refresh(empresa)

        # Crear SUPERADMIN
        superadmin = Usuario(
            nombre="SuperAdmin",
            correo="superadmin@test.com",
            password_hash=hash_password("super123"),
            rol=RolUsuario.SUPERADMIN,
            is_active=True,
            empresa_id=None,
        )

        # Crear ADMINISTRADOR de la empresa
        admin = Usuario(
            nombre="Admin Enterprise X",
            correo="admin-x@test.com",
            password_hash=hash_password("admin123"),
            rol=RolUsuario.ADMINISTRADOR,
            is_active=True,
            empresa_id=empresa.id,
        )

        db.add(superadmin)
        db.add(admin)
        db.commit()

        # Verificar diferencias
        db.refresh(superadmin)
        db.refresh(admin)

        # SUPERADMIN: sin empresa
        assert superadmin.rol == RolUsuario.SUPERADMIN
        assert superadmin.empresa_id is None

        # ADMINISTRADOR: con empresa
        assert admin.rol == RolUsuario.ADMINISTRADOR
        assert admin.empresa_id == empresa.id
    finally:
        db.close()


def test_superadmin_active_by_default():
    """Caso: SUPERADMIN se crea activo."""
    _limpiar_usuarios()

    from app.core.security import hash_password

    db = SessionLocal()
    try:
        superadmin = Usuario(
            nombre="Active SuperAdmin",
            correo="active-superadmin@test.com",
            password_hash=hash_password("pass123"),
            rol=RolUsuario.SUPERADMIN,
            is_active=True,
            empresa_id=None,
        )
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)

        assert superadmin.is_active is True
    finally:
        db.close()
