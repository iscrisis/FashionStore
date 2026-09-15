"""Pruebas de CU16 -- Registrar movimientos de inventario (Panel del Encargado).

Arma el escenario a mano (producto -> variante -> stock por sucursal) igual
que test_consultar_disponibilidad_por_sucursal.py: bypassa los endpoints
administrativos de CU08/CU06/CU14 y construye directamente las mismas
entidades que ellos ya administran, sin duplicar su lógica.

Énfasis en: la suma/resta ocurre en backend, nunca se permite stock negativo,
la sucursal siempre sale del usuario autenticado, y solo ENCARGADO_SUCURSAL
puede usar este panel.
"""

import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.movimiento_inventario import MovimientoInventario
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

client = TestClient(app)


def _create_test_user(rol: RolUsuario, sucursal_id: int | None = None) -> Usuario:
    db = SessionLocal()
    try:
        usuario = Usuario(
            nombre="Usuario de prueba",
            correo=f"test-{uuid.uuid4().hex[:10]}@fashionstore.com",
            password_hash=hash_password("ClaveSegura123!"),
            rol=rol,
            is_active=True,
            sucursal_id=sucursal_id,
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


class _Escenario:
    """Un producto con una variante y stock inicial conocido en una sucursal,
    más un usuario ENCARGADO_SUCURSAL vinculado a esa misma sucursal."""

    def __init__(self, *, stock_inicial: int = 10):
        self.db = SessionLocal()
        sufijo = uuid.uuid4().hex[:8]

        self.proveedor = Proveedor(
            razon_social=f"Proveedor {sufijo}",
            nombre_contacto="Ana",
            correo=f"ana-{sufijo}@textiles.com",
            telefono="70011111",
            is_active=True,
        )
        self.categoria = Categoria(nombre=f"Categoria {sufijo}", is_active=True)
        self.temporada = Temporada(
            nombre=f"Temporada {sufijo}",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 3, 31),
            is_active=True,
        )
        self.talla = Talla(nombre=f"M-{sufijo}", is_active=True)
        self.color = Color(nombre=f"Negro-{sufijo}", is_active=True)
        self.ciudad = Ciudad(nombre=f"Ciudad {sufijo}", departamento="Depto", is_active=True)
        self.db.add_all(
            [self.proveedor, self.categoria, self.temporada, self.talla, self.color, self.ciudad]
        )
        self.db.commit()

        self.coleccion = Coleccion(
            nombre=f"Coleccion {sufijo}", temporada_id=self.temporada.id, is_active=True
        )
        self.sucursal = Sucursal(
            nombre=f"Sucursal {sufijo}",
            ciudad_id=self.ciudad.id,
            direccion="Av. Siempre Viva 123",
            telefono="70022222",
            is_active=True,
        )
        self.db.add_all([self.coleccion, self.sucursal])
        self.db.commit()

        self.producto = Producto(
            nombre=f"Chaqueta Denim {sufijo}",
            proveedor_id=self.proveedor.id,
            categoria_id=self.categoria.id,
            temporada_id=self.temporada.id,
            coleccion_id=self.coleccion.id,
            precio_venta=Decimal("149.90"),
            is_active=True,
            tallas=[self.talla],
            colores=[self.color],
        )
        self.db.add(self.producto)
        self.db.commit()
        self.db.refresh(self.producto)

        self.variante = ProductoVariante(
            producto_id=self.producto.id, talla_id=self.talla.id, color_id=self.color.id, is_active=True
        )
        self.db.add(self.variante)
        self.db.commit()
        self.db.refresh(self.variante)

        self.db.add(
            StockSucursal(
                sucursal_id=self.sucursal.id, producto_variante_id=self.variante.id, cantidad=stock_inicial
            )
        )
        self.db.commit()

        self.encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=self.sucursal.id)

    def headers(self) -> dict:
        return _auth_headers(self.encargado)

    def stock_actual(self) -> int:
        fila = (
            self.db.query(StockSucursal)
            .filter(
                StockSucursal.sucursal_id == self.sucursal.id,
                StockSucursal.producto_variante_id == self.variante.id,
            )
            .first()
        )
        return fila.cantidad if fila else 0

    def cleanup(self) -> None:
        try:
            # Los movimientos referencian usuario_id, sucursal_id y
            # producto_variante_id -- deben borrarse antes que el usuario, la
            # sucursal y la variante/stock. Algunas pruebas cruzan sucursales
            # a propósito (un Encargado de A intentando afectar la variante de
            # B), así que el filtro no puede limitarse a self.variante.id: hay
            # que barrer por sucursal_id / usuario_id también.
            self.db.query(MovimientoInventario).filter(
                (MovimientoInventario.usuario_id == self.encargado.id)
                | (MovimientoInventario.sucursal_id == self.sucursal.id)
                | (MovimientoInventario.producto_variante_id == self.variante.id)
            ).delete(synchronize_session=False)
            self.db.commit()
            _delete_test_user(self.encargado.id)
            self.db.query(StockSucursal).filter(
                (StockSucursal.sucursal_id == self.sucursal.id)
                | (StockSucursal.producto_variante_id == self.variante.id)
            ).delete(synchronize_session=False)
            self.db.commit()
            self.db.delete(self.producto)
            self.db.commit()
            self.db.delete(self.sucursal)
            self.db.delete(self.coleccion)
            self.db.delete(self.temporada)
            self.db.delete(self.categoria)
            self.db.delete(self.talla)
            self.db.delete(self.color)
            self.db.delete(self.proveedor)
            self.db.commit()
            self.db.delete(self.ciudad)
            self.db.commit()
        finally:
            self.db.close()


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_registrar_sin_token_es_rechazado():
    response = client.post(
        "/api/v1/movimientos-inventario/panel",
        json={"producto_variante_id": 1, "tipo": "AJUSTE_POSITIVO", "cantidad": 1, "motivo": "prueba"},
    )
    assert response.status_code == 401


def test_cliente_no_puede_registrar_movimiento():
    escenario = _Escenario()
    cliente = _create_test_user(RolUsuario.CLIENTE)
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=_auth_headers(cliente),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 1,
                "motivo": "prueba",
            },
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(cliente.id)
        escenario.cleanup()


def test_proveedor_no_puede_registrar_movimiento():
    escenario = _Escenario()
    proveedor_usuario = _create_test_user(RolUsuario.PROVEEDOR)
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=_auth_headers(proveedor_usuario),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 1,
                "motivo": "prueba",
            },
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(proveedor_usuario.id)
        escenario.cleanup()


def test_encargado_sin_sucursal_es_rechazado():
    escenario = _Escenario()
    sin_sucursal = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=None)
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=_auth_headers(sin_sucursal),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 1,
                "motivo": "prueba",
            },
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(sin_sucursal.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# Ajustes -- la suma/resta ocurre en backend
# --------------------------------------------------------------------------


def test_ajuste_positivo_suma_al_stock_actual():
    escenario = _Escenario(stock_inicial=10)
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario.headers(),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 3,
                "motivo": "Conteo físico detectó unidades adicionales",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["stock_anterior"] == 10
        assert body["stock_resultante"] == 13
        assert escenario.stock_actual() == 13
    finally:
        escenario.cleanup()


def test_ajuste_negativo_resta_al_stock_actual():
    escenario = _Escenario(stock_inicial=10)
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario.headers(),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_NEGATIVO",
                "cantidad": 2,
                "motivo": "2 prendas dañadas",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["stock_anterior"] == 10
        assert body["stock_resultante"] == 8
        assert escenario.stock_actual() == 8
    finally:
        escenario.cleanup()


def test_ajuste_negativo_mayor_al_stock_es_rechazado_y_no_modifica_nada():
    escenario = _Escenario(stock_inicial=3)
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario.headers(),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_NEGATIVO",
                "cantidad": 5,
                "motivo": "Intento de retirar más de lo disponible",
            },
        )
        assert response.status_code == 422
        # No debe quedar ni stock modificado ni movimiento registrado.
        assert escenario.stock_actual() == 3
        historial = client.get(
            "/api/v1/movimientos-inventario/panel/historial", headers=escenario.headers()
        ).json()
        assert historial == []
    finally:
        escenario.cleanup()


def test_cantidad_cero_es_rechazada():
    escenario = _Escenario()
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario.headers(),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 0,
                "motivo": "cantidad inválida",
            },
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_cantidad_negativa_es_rechazada():
    escenario = _Escenario()
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario.headers(),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": -4,
                "motivo": "cantidad inválida",
            },
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_motivo_demasiado_corto_es_rechazado():
    escenario = _Escenario()
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario.headers(),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 1,
                "motivo": "ab",
            },
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_variante_inexistente_es_rechazada():
    escenario = _Escenario()
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario.headers(),
            json={
                "producto_variante_id": 9_999_999,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 1,
                "motivo": "variante que no existe",
            },
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Seguridad por sucursal -- un Encargado nunca afecta el stock de otra
# --------------------------------------------------------------------------


def test_encargado_no_puede_afectar_stock_de_otra_sucursal_aunque_lo_intente():
    escenario_a = _Escenario(stock_inicial=10)
    escenario_b = _Escenario(stock_inicial=20)
    try:
        # El encargado de la sucursal A intenta registrar un movimiento sobre
        # la variante de la sucursal B -- el body no tiene forma de indicar
        # otra sucursal (el endpoint no acepta ese campo), así que el ajuste
        # cae en la sucursal A del actor, no en B, y B queda intacto.
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario_a.headers(),
            json={
                "producto_variante_id": escenario_b.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 5,
                "motivo": "intento cruzado",
            },
        )
        assert response.status_code == 201
        assert escenario_b.stock_actual() == 20  # sucursal B sin cambios
        # La sucursal A ahora tiene una fila de stock para la variante de B,
        # partiendo de 0 (nunca tuvo stock ahí) + 5.
        fila = (
            escenario_a.db.query(StockSucursal)
            .filter(
                StockSucursal.sucursal_id == escenario_a.sucursal.id,
                StockSucursal.producto_variante_id == escenario_b.variante.id,
            )
            .first()
        )
        assert fila is not None and fila.cantidad == 5
    finally:
        escenario_a.cleanup()
        escenario_b.cleanup()


def test_sucursal_id_en_el_body_es_ignorado():
    escenario_a = _Escenario(stock_inicial=10)
    escenario_b = _Escenario(stock_inicial=20)
    try:
        response = client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario_a.headers(),
            json={
                "producto_variante_id": escenario_a.variante.id,
                "sucursal_id": escenario_b.sucursal.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 5,
                "motivo": "intento de manipular la sucursal",
            },
        )
        assert response.status_code == 201
        assert response.json()["stock_resultante"] == 15
        assert escenario_a.stock_actual() == 15
        assert escenario_b.stock_actual() == 20
    finally:
        escenario_a.cleanup()
        escenario_b.cleanup()


# --------------------------------------------------------------------------
# Historial
# --------------------------------------------------------------------------


def test_historial_incluye_el_movimiento_registrado():
    escenario = _Escenario(stock_inicial=10)
    try:
        client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario.headers(),
            json={
                "producto_variante_id": escenario.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 3,
                "motivo": "Conteo físico",
            },
        )
        response = client.get(
            "/api/v1/movimientos-inventario/panel/historial", headers=escenario.headers()
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["tipo"] == "AJUSTE_POSITIVO"
        assert body[0]["cantidad"] == 3
        assert body[0]["stock_resultante"] == 13
        assert body[0]["registrado_por"]["id"] == escenario.encargado.id
    finally:
        escenario.cleanup()


def test_historial_no_incluye_movimientos_de_otra_sucursal():
    escenario_a = _Escenario(stock_inicial=10)
    escenario_b = _Escenario(stock_inicial=20)
    try:
        client.post(
            "/api/v1/movimientos-inventario/panel",
            headers=escenario_b.headers(),
            json={
                "producto_variante_id": escenario_b.variante.id,
                "tipo": "AJUSTE_POSITIVO",
                "cantidad": 1,
                "motivo": "movimiento de la sucursal B",
            },
        )
        historial_a = client.get(
            "/api/v1/movimientos-inventario/panel/historial", headers=escenario_a.headers()
        ).json()
        assert historial_a == []
    finally:
        escenario_a.cleanup()
        escenario_b.cleanup()
