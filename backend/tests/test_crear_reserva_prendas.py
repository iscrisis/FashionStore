"""Pruebas de CU17 -- Crear reserva de prendas (Cliente).

Arma el escenario a mano (producto -> variante -> stock por sucursal) igual
que test_movimientos_inventario.py: bypassa los endpoints administrativos de
CU08/CU06/CU14 y construye directamente las mismas entidades que ellos ya
administran, sin duplicar su lógica.

Énfasis en: el Cliente elige la sucursal (a diferencia de CU14/15/16, no sale
de su cuenta), la reserva NUNCA descuenta StockSucursal, solo valida
disponibilidad al crearla, un Cliente solo ve sus propias reservas, la
fecha/horario del bloque de 1h respeta la ventana de 7 días y el horario de
atención (lun-sáb 10-20, DOMINGO SIN ATENCIÓN) -- ver constantes en CU17
service.py -- y el modelo agrupado: cada respuesta es una CABECERA
(`codigo_reserva`, `estado_general`) con sus prendas anidadas en `detalles`
(ver Models/reserva.py).
"""

import threading
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P4_ReservasYAtencion.CU17_CrearReservaPrendas.service import (
    DOMINGO_WEEKDAY,
    HORA_APERTURA,
    HORA_CIERRE_LUN_A_SAB,
)
from modules.P4_ReservasYAtencion.Models.reserva import Reserva, ReservaDetalle

client = TestClient(app)


# --------------------------------------------------------------------------
# Fecha/hora seguras -- ver CU17 service.py para las reglas reales
# --------------------------------------------------------------------------


def _hoy() -> date:
    return datetime.now(timezone.utc).date()


def _fecha_hora_segura() -> tuple[date, time]:
    """mañana (o pasado mañana si mañana cae domingo, que ahora está
    cerrado) a mediodía -- dentro de la ventana de 7 días y del horario de
    atención de cualquier día hábil, para tests que no verifican la regla
    de fecha/horario en sí, sin importar cuándo corra la suite."""
    candidata = _hoy() + timedelta(days=1)
    if candidata.weekday() == DOMINGO_WEEKDAY:
        candidata += timedelta(days=1)
    return candidata, time(12, 0)


def _fecha_con_dia_semana(objetivo_weekday: int) -> date:
    """Primera fecha, dentro de la ventana válida hoy..hoy+7 (8 días
    consecutivos), cuyo weekday() coincida -- cualquier día de la semana
    aparece al menos una vez en 8 días seguidos, así que esto nunca falla
    ni depende de qué día se ejecute la suite."""
    hoy = _hoy()
    for delta in range(8):
        candidata = hoy + timedelta(days=delta)
        if candidata.weekday() == objetivo_weekday:
            return candidata
    raise AssertionError("inalcanzable: 8 días consecutivos cubren toda la semana")


def _payload(escenario: "_Escenario", **overrides) -> dict:
    fecha, hora = _fecha_hora_segura()
    base = {
        "producto_variante_id": escenario.variante.id,
        "sucursal_id": escenario.sucursal.id,
        "cantidad": 1,
        "fecha_reserva": fecha.isoformat(),
        "hora_inicio": hora.isoformat(),
    }
    base.update(overrides)
    return base


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
    """Un producto con una variante y stock inicial conocido en una sucursal
    activa, más un Cliente (sin sucursal propia -- CU17 no la necesita)."""

    def __init__(self, *, stock_inicial: int = 10, sucursal_activa: bool = True):
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
            is_active=sucursal_activa,
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

        self.cliente = _create_test_user(RolUsuario.CLIENTE)

    def headers(self) -> dict:
        return _auth_headers(self.cliente)

    def _fila_stock(self) -> StockSucursal | None:
        # Sesión NUEVA (no self.db) a propósito: self.db mantiene en su
        # identity map el objeto StockSucursal ya cargado durante el setup, y
        # una query repetida sobre esa misma sesión puede devolver ese mismo
        # objeto en caché en vez de reflejar cambios ya confirmados por OTRA
        # sesión (la que abre cada request real vía get_db) -- justo lo que
        # stock_actual()/stock_reservado_actual() necesitan ver.
        db = SessionLocal()
        try:
            return (
                db.query(StockSucursal)
                .filter(
                    StockSucursal.sucursal_id == self.sucursal.id,
                    StockSucursal.producto_variante_id == self.variante.id,
                )
                .first()
            )
        finally:
            db.close()

    def stock_actual(self) -> int:
        fila = self._fila_stock()
        return fila.cantidad if fila else 0

    def stock_reservado_actual(self) -> int:
        fila = self._fila_stock()
        return fila.stock_reservado if fila else 0

    def cleanup(self) -> None:
        try:
            # Los detalles no cascadean "hacia arriba" -- se borran primero
            # por producto_variante_id; las cabeceras (por cliente/sucursal)
            # se borran después y arrastran en cascada (ON DELETE CASCADE,
            # ver Models/reserva.py) cualquier detalle que haya quedado.
            self.db.query(ReservaDetalle).filter(
                ReservaDetalle.producto_variante_id == self.variante.id
            ).delete(synchronize_session=False)
            self.db.commit()
            self.db.query(Reserva).filter(
                (Reserva.cliente_id == self.cliente.id) | (Reserva.sucursal_id == self.sucursal.id)
            ).delete(synchronize_session=False)
            self.db.commit()
            _delete_test_user(self.cliente.id)
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


def test_crear_reserva_sin_token_es_rechazada():
    fecha, hora = _fecha_hora_segura()
    response = client.post(
        "/api/v1/reservas",
        json={
            "producto_variante_id": 1,
            "sucursal_id": 1,
            "cantidad": 1,
            "fecha_reserva": fecha.isoformat(),
            "hora_inicio": hora.isoformat(),
        },
    )
    assert response.status_code == 401


def test_encargado_no_puede_crear_reserva():
    escenario = _Escenario()
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)
    try:
        response = client.post(
            "/api/v1/reservas", headers=_auth_headers(encargado), json=_payload(escenario)
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# Creación -- cabecera + 1 detalle, disponibilidad y estado inicial
# --------------------------------------------------------------------------


def test_cliente_autenticado_puede_crear_reserva():
    escenario = _Escenario(stock_inicial=10)
    try:
        fecha, hora = _fecha_hora_segura()
        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, cantidad=3),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["estado_general"] == "PENDIENTE"
        assert body["sucursal"]["id"] == escenario.sucursal.id
        assert body["fecha_reserva"] == fecha.isoformat()
        assert body["hora_inicio"].startswith(hora.isoformat())
        assert len(body["detalles"]) == 1
        assert body["detalles"][0]["cantidad"] == 3
        assert body["detalles"][0]["estado"] == "PENDIENTE"
        assert body["detalles"][0]["variante"]["id"] == escenario.variante.id
    finally:
        escenario.cleanup()


def test_reserva_genera_codigo_visible_con_formato_rs():
    escenario = _Escenario(stock_inicial=5)
    try:
        response = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        assert response.status_code == 201
        body = response.json()
        assert body["codigo_reserva"].startswith("RS-")
        assert len(body["codigo_reserva"]) == len("RS-00001")
        # El código no es el id crudo de Postgres reinterpretado al azar --
        # es "RS-" + el propio id, con padding de 5 dígitos.
        assert body["codigo_reserva"] == f"RS-{body['id']:05d}"

        # Es único: una segunda reserva (otra unidad, mismo cliente) recibe
        # otro código distinto.
        segunda = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, fecha_reserva=_fecha_con_dia_semana(2).isoformat(), hora_inicio="11:00:00"),
        )
        assert segunda.status_code == 201
        assert segunda.json()["codigo_reserva"] != body["codigo_reserva"]
    finally:
        escenario.cleanup()


def test_reserva_no_descuenta_stock():
    escenario = _Escenario(stock_inicial=10)
    try:
        client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=4))
        # El stock real de StockSucursal debe seguir igual -- CU17 no lo toca.
        assert escenario.stock_actual() == 10
    finally:
        escenario.cleanup()


def test_cantidad_cero_es_rechazada():
    escenario = _Escenario()
    try:
        response = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=0)
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_cantidad_negativa_es_rechazada():
    escenario = _Escenario()
    try:
        response = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=-2)
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_variante_inexistente_es_rechazada():
    escenario = _Escenario()
    try:
        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, producto_variante_id=9_999_999),
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_sucursal_inexistente_es_rechazada():
    escenario = _Escenario()
    try:
        response = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, sucursal_id=9_999_999)
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_sucursal_inactiva_es_rechazada():
    escenario = _Escenario(sucursal_activa=False)
    try:
        response = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_cantidad_mayor_al_stock_disponible_es_rechazada():
    escenario = _Escenario(stock_inicial=3)
    try:
        response = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=5)
        )
        assert response.status_code == 422
        # No debe quedar ninguna reserva registrada.
        historial = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert historial == []
    finally:
        escenario.cleanup()


def test_cantidad_igual_al_stock_disponible_es_aceptada():
    escenario = _Escenario(stock_inicial=5)
    try:
        response = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=5)
        )
        assert response.status_code == 201
    finally:
        escenario.cleanup()


def test_sin_stock_en_esa_sucursal_es_rechazada():
    escenario = _Escenario(stock_inicial=0)
    try:
        response = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        assert response.status_code == 422
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Fecha -- ventana de hoy hasta hoy + 7 días, ambos inclusive
# --------------------------------------------------------------------------


def test_fecha_pasada_es_rechazada():
    escenario = _Escenario()
    try:
        ayer = _hoy() - timedelta(days=1)
        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, fecha_reserva=ayer.isoformat(), hora_inicio="12:00:00"),
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_fecha_dentro_de_7_dias_es_aceptada():
    escenario = _Escenario()
    try:
        # Busca un día entre +2 y +6 que no sea domingo (cerrado) -- con 5
        # candidatos consecutivos siempre hay al menos uno hábil.
        dentro_del_rango = next(
            _hoy() + timedelta(days=delta)
            for delta in range(2, 7)
            if (_hoy() + timedelta(days=delta)).weekday() != DOMINGO_WEEKDAY
        )
        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, fecha_reserva=dentro_del_rango.isoformat(), hora_inicio="12:00:00"),
        )
        assert response.status_code == 201
    finally:
        escenario.cleanup()


def test_fecha_exactamente_dia_7_es_aceptada():
    escenario = _Escenario()
    try:
        dia_7 = _hoy() + timedelta(days=7)
        if dia_7.weekday() == DOMINGO_WEEKDAY:
            pytest.skip(
                "El día exacto +7 cae en domingo (sin atención) en la fecha de ejecución -- "
                "no se puede probar el límite de 7 días de forma aislada de esa regla hoy."
            )
        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, fecha_reserva=dia_7.isoformat(), hora_inicio="12:00:00"),
        )
        assert response.status_code == 201
    finally:
        escenario.cleanup()


def test_fecha_mayor_a_7_dias_es_rechazada():
    escenario = _Escenario()
    try:
        dia_8 = _hoy() + timedelta(days=8)
        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, fecha_reserva=dia_8.isoformat(), hora_inicio="12:00:00"),
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Horario -- atención por día de la semana, bloques de 1h, anticipación
# --------------------------------------------------------------------------


def test_horario_fuera_de_atencion_entre_semana_es_rechazado():
    escenario = _Escenario()
    try:
        # Lunes (weekday 0): abre a las 10:00, 09:00 es antes de abrir.
        fecha = _fecha_con_dia_semana(0)
        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, fecha_reserva=fecha.isoformat(), hora_inicio="09:00:00"),
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_domingo_sin_atencion_es_rechazado_aunque_la_hora_sea_valida():
    escenario = _Escenario()
    try:
        # Domingo no hay atención -- se rechaza cualquier horario, incluso
        # uno que sería perfectamente válido cualquier otro día (10:00, la
        # propia hora de apertura entre semana).
        domingo = _fecha_con_dia_semana(DOMINGO_WEEKDAY)
        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, fecha_reserva=domingo.isoformat(), hora_inicio="10:00:00"),
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_horario_pasado_para_hoy_es_rechazado():
    escenario = _Escenario()
    try:
        # La hora truncada de "ahora" siempre queda en el pasado respecto a
        # la anticipación mínima de 1h, sin importar en qué momento corra la
        # suite -- no depende de si es horario de atención o no.
        ahora = datetime.now(timezone.utc)
        hora_ya_pasada = ahora.replace(minute=0, second=0, microsecond=0).time()
        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(
                escenario, fecha_reserva=_hoy().isoformat(), hora_inicio=hora_ya_pasada.isoformat()
            ),
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


def test_fecha_hoy_con_horario_valido_es_aceptada():
    escenario = _Escenario()
    try:
        ahora = datetime.now(timezone.utc)
        hoy = ahora.date()
        if hoy.weekday() == DOMINGO_WEEKDAY:
            pytest.skip("Hoy es domingo (sin atención) en la fecha de ejecución -- no hay ningún bloque válido.")
        ultimo_bloque = (datetime.combine(date.min, HORA_CIERRE_LUN_A_SAB) - timedelta(hours=1)).time()

        # Primer bloque en punto que arranca al menos 1h+1min después de
        # ahora (margen de 1 minuto para que el request no cruce el límite
        # exacto mientras viaja), o la apertura (10:00) si esa hora ya pasó
        # -- ej. de madrugada, el próximo bloque válido sigue siendo 10:00,
        # no antes.
        umbral = ahora + timedelta(hours=1, minutes=1)
        siguiente_hora_en_punto = umbral.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if siguiente_hora_en_punto.date() != hoy:
            pytest.skip("La próxima hora disponible ya cae en el día siguiente a esta hora de ejecución.")

        hora_candidata = max(siguiente_hora_en_punto.time(), HORA_APERTURA)
        if hora_candidata > ultimo_bloque:
            pytest.skip(
                "No queda un bloque horario válido para 'hoy' a esta hora de ejecución -- "
                "regla dependiente de la hora real, no de la lógica bajo prueba."
            )

        response = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, fecha_reserva=hoy.isoformat(), hora_inicio=hora_candidata.isoformat()),
        )
        assert response.status_code == 201
    finally:
        escenario.cleanup()


def test_bloque_que_no_empieza_en_punto_es_rechazado():
    escenario = _Escenario()
    try:
        response = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, hora_inicio="12:30:00")
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Reservas del mismo cliente en distintas sucursales
# --------------------------------------------------------------------------


def test_reserva_en_distintas_sucursales_para_el_mismo_cliente():
    escenario_a = _Escenario(stock_inicial=5)
    try:
        # Segunda sucursal, mismo cliente: se reutiliza el cliente del
        # primer escenario en vez de crear otro _Escenario (que traería su
        # propio cliente nuevo).
        db = SessionLocal()
        try:
            ciudad_b = Ciudad(nombre=f"Ciudad {uuid.uuid4().hex[:8]}", departamento="Depto", is_active=True)
            db.add(ciudad_b)
            db.commit()
            sucursal_b = Sucursal(
                nombre=f"Sucursal {uuid.uuid4().hex[:8]}",
                ciudad_id=ciudad_b.id,
                direccion="Otra Av. 456",
                telefono="70033333",
                is_active=True,
            )
            db.add(sucursal_b)
            db.commit()
            db.add(
                StockSucursal(
                    sucursal_id=sucursal_b.id, producto_variante_id=escenario_a.variante.id, cantidad=5
                )
            )
            db.commit()
            db.refresh(sucursal_b)
        finally:
            db.close()

        try:
            resp_a = client.post(
                "/api/v1/reservas",
                headers=escenario_a.headers(),
                json=_payload(escenario_a, sucursal_id=escenario_a.sucursal.id),
            )
            resp_b = client.post(
                "/api/v1/reservas",
                headers=escenario_a.headers(),
                json=_payload(escenario_a, sucursal_id=sucursal_b.id),
            )
            assert resp_a.status_code == 201
            assert resp_b.status_code == 201
            assert resp_a.json()["sucursal"]["id"] != resp_b.json()["sucursal"]["id"]

            mias = client.get("/api/v1/reservas/mias", headers=escenario_a.headers()).json()
            sucursales_reservadas = {r["sucursal"]["id"] for r in mias}
            assert {escenario_a.sucursal.id, sucursal_b.id} == sucursales_reservadas
        finally:
            db = SessionLocal()
            try:
                db.query(ReservaDetalle).filter(
                    ReservaDetalle.producto_variante_id == escenario_a.variante.id
                ).delete(synchronize_session=False)
                db.commit()
                db.query(Reserva).filter(Reserva.sucursal_id == sucursal_b.id).delete(
                    synchronize_session=False
                )
                db.commit()
                db.query(StockSucursal).filter(StockSucursal.sucursal_id == sucursal_b.id).delete(
                    synchronize_session=False
                )
                db.commit()
                sucursal_b_obj = db.get(Sucursal, sucursal_b.id)
                if sucursal_b_obj is not None:
                    db.delete(sucursal_b_obj)
                db.commit()
                ciudad_b_obj = db.get(Ciudad, ciudad_b.id)
                if ciudad_b_obj is not None:
                    db.delete(ciudad_b_obj)
                db.commit()
            finally:
                db.close()
    finally:
        escenario_a.cleanup()


# --------------------------------------------------------------------------
# GET /reservas/mias -- aislamiento por cliente
# --------------------------------------------------------------------------


def test_mis_reservas_incluye_la_reserva_creada():
    escenario = _Escenario(stock_inicial=10)
    try:
        client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=2))
        response = client.get("/api/v1/reservas/mias", headers=escenario.headers())
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["detalles"][0]["cantidad"] == 2
        assert body[0]["estado_general"] == "PENDIENTE"
    finally:
        escenario.cleanup()


def test_mis_reservas_no_incluye_reservas_de_otro_cliente():
    escenario_a = _Escenario(stock_inicial=10)
    escenario_b = _Escenario(stock_inicial=10)
    try:
        client.post("/api/v1/reservas", headers=escenario_b.headers(), json=_payload(escenario_b))
        mias_a = client.get("/api/v1/reservas/mias", headers=escenario_a.headers()).json()
        assert mias_a == []
    finally:
        escenario_a.cleanup()
        escenario_b.cleanup()


def test_mis_reservas_sin_token_es_rechazada():
    response = client.get("/api/v1/reservas/mias")
    assert response.status_code == 401


# --------------------------------------------------------------------------
# stock_reservado -- disponible = stock_actual - stock_reservado. Una reserva
# PENDIENTE compromete stock_reservado, NUNCA el físico (cantidad); dos
# reservas no pueden compartir la última unidad (ver CrearReservaService.crear
# y StockSucursalRepository.bloquear_para_reservar).
# --------------------------------------------------------------------------


def test_con_una_sola_unidad_la_primera_reserva_funciona():
    escenario = _Escenario(stock_inicial=1)
    try:
        response = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=1)
        )
        assert response.status_code == 201
    finally:
        escenario.cleanup()


def test_reservar_no_baja_stock_actual_y_sube_stock_reservado_en_exactamente_1():
    escenario = _Escenario(stock_inicial=1)
    try:
        client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=1))
        assert escenario.stock_actual() == 1
        assert escenario.stock_reservado_actual() == 1
    finally:
        escenario.cleanup()


def test_segunda_reserva_sobre_la_misma_variante_y_sucursal_es_rechazada():
    escenario = _Escenario(stock_inicial=1)
    try:
        primera = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=1)
        )
        assert primera.status_code == 201

        segunda = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=1)
        )
        assert segunda.status_code == 422
        # No debe haber quedado una segunda reserva ni un segundo incremento.
        assert escenario.stock_reservado_actual() == 1
        assert escenario.stock_actual() == 1
        historial = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert len(historial) == 1
    finally:
        escenario.cleanup()


def test_otra_sucursal_con_stock_sigue_permitiendo_reservar_la_misma_variante():
    escenario = _Escenario(stock_inicial=1)
    try:
        primera = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=1)
        )
        assert primera.status_code == 201

        db = SessionLocal()
        try:
            ciudad_b = Ciudad(nombre=f"Ciudad {uuid.uuid4().hex[:8]}", departamento="Depto", is_active=True)
            db.add(ciudad_b)
            db.commit()
            sucursal_b = Sucursal(
                nombre=f"Sucursal {uuid.uuid4().hex[:8]}",
                ciudad_id=ciudad_b.id,
                direccion="Otra Av. 789",
                telefono="70044444",
                is_active=True,
            )
            db.add(sucursal_b)
            db.commit()
            db.add(
                StockSucursal(
                    sucursal_id=sucursal_b.id, producto_variante_id=escenario.variante.id, cantidad=1
                )
            )
            db.commit()
            db.refresh(sucursal_b)
        finally:
            db.close()

        try:
            segunda = client.post(
                "/api/v1/reservas",
                headers=escenario.headers(),
                json=_payload(escenario, sucursal_id=sucursal_b.id, cantidad=1),
            )
            assert segunda.status_code == 201
        finally:
            db = SessionLocal()
            try:
                db.query(ReservaDetalle).filter(
                    ReservaDetalle.producto_variante_id == escenario.variante.id
                ).delete(synchronize_session=False)
                db.commit()
                db.query(Reserva).filter(Reserva.sucursal_id == sucursal_b.id).delete(
                    synchronize_session=False
                )
                db.commit()
                db.query(StockSucursal).filter(StockSucursal.sucursal_id == sucursal_b.id).delete(
                    synchronize_session=False
                )
                db.commit()
                sucursal_b_obj = db.get(Sucursal, sucursal_b.id)
                if sucursal_b_obj is not None:
                    db.delete(sucursal_b_obj)
                db.commit()
                ciudad_b_obj = db.get(Ciudad, ciudad_b.id)
                if ciudad_b_obj is not None:
                    db.delete(ciudad_b_obj)
                db.commit()
            finally:
                db.close()
    finally:
        escenario.cleanup()


def test_otra_variante_con_stock_sigue_permitiendo_reservar():
    escenario = _Escenario(stock_inicial=1)
    try:
        primera = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=1)
        )
        assert primera.status_code == 201

        # Otra talla del MISMO producto, en la MISMA sucursal, con su propio
        # stock -- agotar la primera variante no debe afectar esta otra
        # combinación talla/color (cada fila de StockSucursal es independiente).
        db = SessionLocal()
        try:
            otra_talla = Talla(nombre=f"L-{uuid.uuid4().hex[:8]}", is_active=True)
            db.add(otra_talla)
            db.commit()
            otra_variante = ProductoVariante(
                producto_id=escenario.producto.id,
                talla_id=otra_talla.id,
                color_id=escenario.color.id,
                is_active=True,
            )
            db.add(otra_variante)
            db.commit()
            db.add(
                StockSucursal(
                    sucursal_id=escenario.sucursal.id,
                    producto_variante_id=otra_variante.id,
                    cantidad=1,
                )
            )
            db.commit()
            db.refresh(otra_variante)
        finally:
            db.close()

        try:
            segunda = client.post(
                "/api/v1/reservas",
                headers=escenario.headers(),
                json=_payload(escenario, producto_variante_id=otra_variante.id, cantidad=1),
            )
            assert segunda.status_code == 201
        finally:
            db = SessionLocal()
            try:
                db.query(ReservaDetalle).filter(
                    ReservaDetalle.producto_variante_id == otra_variante.id
                ).delete(synchronize_session=False)
                db.commit()
                db.query(StockSucursal).filter(
                    StockSucursal.producto_variante_id == otra_variante.id
                ).delete(synchronize_session=False)
                db.commit()
                variante_obj = db.get(ProductoVariante, otra_variante.id)
                if variante_obj is not None:
                    db.delete(variante_obj)
                db.commit()
                talla_obj = db.get(Talla, otra_talla.id)
                if talla_obj is not None:
                    db.delete(talla_obj)
                db.commit()
            finally:
                db.close()
    finally:
        escenario.cleanup()


def test_dos_clientes_reservando_la_ultima_unidad_solo_uno_gana():
    """Concurrencia real: dos TestClient independientes (cada uno con su
    propio transporte/loop, para no depender de que un único TestClient
    sea seguro entre hilos) disparan la MISMA reserva casi al mismo tiempo
    contra la MISMA fila de stock (1 sola unidad). Sin el SELECT ... FOR
    UPDATE de StockSucursalRepository.bloquear_para_reservar, ambos hilos
    podrían leer stock_reservado=0 antes de que el otro confirme y las dos
    reservas se crearían -- exactamente el bug reportado."""
    escenario = _Escenario(stock_inicial=1)
    cliente_b = _create_test_user(RolUsuario.CLIENTE)
    try:
        payload = _payload(escenario, cantidad=1)
        resultados: list[int] = []
        resultados_lock = threading.Lock()

        def _reservar(headers: dict) -> None:
            cliente_http = TestClient(app)
            respuesta = cliente_http.post("/api/v1/reservas", headers=headers, json=payload)
            with resultados_lock:
                resultados.append(respuesta.status_code)

        hilo_a = threading.Thread(target=_reservar, args=(escenario.headers(),))
        hilo_b = threading.Thread(target=_reservar, args=(_auth_headers(cliente_b),))
        hilo_a.start()
        hilo_b.start()
        hilo_a.join(timeout=30)
        hilo_b.join(timeout=30)

        assert sorted(resultados) == [201, 422]
        assert escenario.stock_reservado_actual() == 1
        assert escenario.stock_actual() == 1
    finally:
        # escenario.cleanup() PRIMERO: si cliente_b ganó la carrera, su
        # reserva quedó con sucursal_id == escenario.sucursal.id (mismo
        # payload) -- el filtro de escenario.cleanup() ya la alcanza y la
        # borra. Si se borrara cliente_b antes, esa reserva (con
        # cliente_id=cliente_b.id) violaría la FK y el propio cleanup fallaría.
        escenario.cleanup()
        _delete_test_user(cliente_b.id)
