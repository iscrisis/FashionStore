"""Pruebas de CU17 -- Agregar prendas a una reserva existente (Cliente).

Reutiliza el mismo escenario y helpers de CU17 (test_crear_reserva_prendas)
en vez de reconstruir producto/variante/sucursal/stock/cliente desde cero.
Énfasis en lo que pide este cambio: la SEGUNDA prenda del mismo cliente en la
misma sucursal se ofrece como "agregar a la reserva existente" en vez de
crear otra cabecera; agregar NUNCA crea una Reserva nueva, solo un
ReservaDetalle (o incrementa uno ya existente para la misma variante);
stock_reservado sube exactamente lo agregado; una reserva que ya no está
PENDIENTE (PREPARADA en adelante) no aparece como compatible ni acepta
agregados; y CU18 (GET /reservas/mias) sigue mostrando una sola tarjeta
agrupada.
"""

import uuid
from decimal import Decimal

from tests.test_crear_reserva_prendas import (
    _auth_headers,
    _create_test_user,
    _delete_test_user,
    _Escenario,
    _payload,
)
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva, ReservaDetalle

client = TestClient(app)


def _otra_variante(escenario: _Escenario, *, stock_inicial: int = 5) -> ProductoVariante:
    """Otra talla del MISMO producto (misma sucursal) con su propio stock --
    "Polera"/"Pantalón" del enunciado son, en este dominio, otra
    ProductoVariante del mismo producto.

    Un solo commit al final (flush en el medio, solo para obtener los ids
    autogenerados que necesitan las filas siguientes) + un refresh antes de
    cerrar la sesión: con expire_on_commit=True (default), CUALQUIER commit
    expira TODOS los objetos de la sesión, no solo el que se acaba de
    guardar -- con más de un commit, `variante` quedaba expirada y luego
    detached al cerrar `db`, y leer variante.id más adelante (en el test o en
    _limpiar_variante) fallaba con DetachedInstanceError."""
    db = SessionLocal()
    try:
        sufijo = uuid.uuid4().hex[:8]
        talla = Talla(nombre=f"Talla-{sufijo}", is_active=True)
        db.add(talla)
        db.flush()
        variante = ProductoVariante(
            producto_id=escenario.producto.id, talla_id=talla.id, color_id=escenario.color.id, is_active=True
        )
        db.add(variante)
        db.flush()
        db.add(
            StockSucursal(sucursal_id=escenario.sucursal.id, producto_variante_id=variante.id, cantidad=stock_inicial)
        )
        db.commit()
        db.refresh(variante)
        return variante
    finally:
        db.close()


def _limpiar_variante(variante: ProductoVariante) -> None:
    db = SessionLocal()
    try:
        db.query(ReservaDetalle).filter(ReservaDetalle.producto_variante_id == variante.id).delete(
            synchronize_session=False
        )
        db.commit()
        db.query(StockSucursal).filter(StockSucursal.producto_variante_id == variante.id).delete(
            synchronize_session=False
        )
        db.commit()
        talla_id = variante.talla_id
        obj = db.get(ProductoVariante, variante.id)
        if obj is not None:
            db.delete(obj)
        db.commit()
        talla = db.get(Talla, talla_id)
        if talla is not None:
            db.delete(talla)
        db.commit()
    finally:
        db.close()


def _stock_reservado_de(sucursal_id: int, variante_id: int) -> int:
    db = SessionLocal()
    try:
        fila = (
            db.query(StockSucursal)
            .filter(StockSucursal.sucursal_id == sucursal_id, StockSucursal.producto_variante_id == variante_id)
            .first()
        )
        return fila.stock_reservado if fila else 0
    finally:
        db.close()


# --------------------------------------------------------------------------
# 1/2. Primera prenda crea RS-XXXXX; segunda (misma sucursal) aparece como
# compatible.
# --------------------------------------------------------------------------


def test_primera_reserva_no_aparece_compatible_para_otra_sucursal():
    escenario = _Escenario(stock_inicial=5)
    try:
        creada = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        assert creada.status_code == 201

        db = SessionLocal()
        try:
            from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
            from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal

            ciudad_b = Ciudad(nombre=f"Ciudad {uuid.uuid4().hex[:8]}", departamento="Depto", is_active=True)
            db.add(ciudad_b)
            db.commit()
            sucursal_b = Sucursal(
                nombre=f"Sucursal {uuid.uuid4().hex[:8]}",
                ciudad_id=ciudad_b.id,
                direccion="Otra Av. 1",
                telefono="70055555",
                is_active=True,
            )
            db.add(sucursal_b)
            db.commit()
            db.refresh(sucursal_b)
            sucursal_b_id = sucursal_b.id
        finally:
            db.close()

        compatibles = client.get(
            "/api/v1/reservas/compatibles",
            params={"sucursal_id": sucursal_b_id},
            headers=escenario.headers(),
        )
        assert compatibles.status_code == 200
        assert compatibles.json() == []
    finally:
        escenario.cleanup()


def test_segunda_prenda_misma_sucursal_ofrece_reserva_compatible():
    escenario = _Escenario(stock_inicial=5)
    try:
        creada = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        assert creada.status_code == 201
        codigo = creada.json()["codigo_reserva"]

        compatibles = client.get(
            "/api/v1/reservas/compatibles",
            params={"sucursal_id": escenario.sucursal.id},
            headers=escenario.headers(),
        )
        assert compatibles.status_code == 200
        cuerpo = compatibles.json()
        assert len(cuerpo) == 1
        assert cuerpo[0]["codigo_reserva"] == codigo
        assert cuerpo[0]["estado_general"] == "PENDIENTE"
        assert len(cuerpo[0]["detalles"]) == 1
    finally:
        escenario.cleanup()


def test_compatibles_sin_token_es_rechazada():
    response = client.get("/api/v1/reservas/compatibles", params={"sucursal_id": 1})
    assert response.status_code == 401


# --------------------------------------------------------------------------
# 3/4. Agregar NO crea cabecera nueva -- la reserva existente pasa a tener 2
# detalles.
# --------------------------------------------------------------------------


def test_agregar_detalle_no_crea_nueva_cabecera_y_suma_2_detalles():
    escenario = _Escenario(stock_inicial=5)
    otra = _otra_variante(escenario, stock_inicial=5)
    try:
        creada = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        assert creada.status_code == 201
        reserva = creada.json()
        codigo_original = reserva["codigo_reserva"]
        reserva_id = reserva["id"]

        respuesta = client.post(
            f"/api/v1/reservas/{reserva_id}/detalles",
            headers=escenario.headers(),
            json={"producto_variante_id": otra.id, "cantidad": 1},
        )
        assert respuesta.status_code == 201
        actualizada = respuesta.json()

        # Misma cabecera -- mismo id, mismo código.
        assert actualizada["id"] == reserva_id
        assert actualizada["codigo_reserva"] == codigo_original
        assert len(actualizada["detalles"]) == 2
        variantes = {d["variante"]["id"] for d in actualizada["detalles"]}
        assert variantes == {escenario.variante.id, otra.id}

        # GET /reservas/mias confirma UNA sola tarjeta con las 2 prendas.
        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert len(mias) == 1
        assert mias[0]["id"] == reserva_id
        assert len(mias[0]["detalles"]) == 2
    finally:
        _limpiar_variante(otra)
        escenario.cleanup()


def test_agregar_la_misma_variante_dos_veces_fusiona_cantidad_sin_duplicar_detalle():
    escenario = _Escenario(stock_inicial=5)
    otra = _otra_variante(escenario, stock_inicial=5)
    try:
        creada = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        reserva_id = creada.json()["id"]

        primera = client.post(
            f"/api/v1/reservas/{reserva_id}/detalles",
            headers=escenario.headers(),
            json={"producto_variante_id": otra.id, "cantidad": 1},
        )
        assert primera.status_code == 201

        segunda = client.post(
            f"/api/v1/reservas/{reserva_id}/detalles",
            headers=escenario.headers(),
            json={"producto_variante_id": otra.id, "cantidad": 2},
        )
        assert segunda.status_code == 201
        detalles = segunda.json()["detalles"]
        # Sigue habiendo 2 detalles (chaqueta original + la otra variante) --
        # NO 3: la segunda llamada fusionó cantidad en el mismo detalle.
        assert len(detalles) == 2
        detalle_otra = next(d for d in detalles if d["variante"]["id"] == otra.id)
        assert detalle_otra["cantidad"] == 3
        assert _stock_reservado_de(escenario.sucursal.id, otra.id) == 3
    finally:
        _limpiar_variante(otra)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 5. stock_reservado sube exactamente lo agregado, stock_actual intacto.
# --------------------------------------------------------------------------


def test_agregar_detalle_sube_stock_reservado_sin_tocar_stock_actual():
    escenario = _Escenario(stock_inicial=5)
    otra = _otra_variante(escenario, stock_inicial=5)
    try:
        creada = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        reserva_id = creada.json()["id"]
        assert _stock_reservado_de(escenario.sucursal.id, otra.id) == 0

        client.post(
            f"/api/v1/reservas/{reserva_id}/detalles",
            headers=escenario.headers(),
            json={"producto_variante_id": otra.id, "cantidad": 1},
        )

        db = SessionLocal()
        try:
            fila = (
                db.query(StockSucursal)
                .filter(
                    StockSucursal.sucursal_id == escenario.sucursal.id,
                    StockSucursal.producto_variante_id == otra.id,
                )
                .first()
            )
            assert fila.cantidad == 5  # stock_actual NUNCA cambia.
            assert fila.stock_reservado == 1
        finally:
            db.close()
    finally:
        _limpiar_variante(otra)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 6. Sin stock disponible, no se agrega el detalle.
# --------------------------------------------------------------------------


def test_agregar_detalle_sin_stock_disponible_es_rechazado():
    escenario = _Escenario(stock_inicial=5)
    otra = _otra_variante(escenario, stock_inicial=1)
    try:
        creada = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        reserva_id = creada.json()["id"]

        respuesta = client.post(
            f"/api/v1/reservas/{reserva_id}/detalles",
            headers=escenario.headers(),
            json={"producto_variante_id": otra.id, "cantidad": 5},
        )
        assert respuesta.status_code == 422

        # No debe haberse agregado nada ni tocado el stock.
        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert len(mias[0]["detalles"]) == 1
        assert _stock_reservado_de(escenario.sucursal.id, otra.id) == 0
    finally:
        _limpiar_variante(otra)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 7. PREPARADA/EN_ATENCION/etc. no son compatibles ni aceptan agregados.
# --------------------------------------------------------------------------


def test_reserva_preparada_no_aparece_como_compatible():
    escenario = _Escenario(stock_inicial=5)
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)
    otra = _otra_variante(escenario, stock_inicial=5)
    try:
        creada = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        reserva = creada.json()
        detalle_id = reserva["detalles"][0]["id"]

        preparar = client.patch(
            f"/api/v1/reservas/detalles/{detalle_id}/preparar", headers=_auth_headers(encargado)
        )
        assert preparar.status_code == 200

        compatibles = client.get(
            "/api/v1/reservas/compatibles",
            params={"sucursal_id": escenario.sucursal.id},
            headers=escenario.headers(),
        )
        assert compatibles.json() == []

        agregar = client.post(
            f"/api/v1/reservas/{reserva['id']}/detalles",
            headers=escenario.headers(),
            json={"producto_variante_id": otra.id, "cantidad": 1},
        )
        assert agregar.status_code == 422
    finally:
        _delete_test_user(encargado.id)
        _limpiar_variante(otra)
        escenario.cleanup()


def test_reserva_cancelada_no_aparece_como_compatible():
    escenario = _Escenario(stock_inicial=5)
    otra = _otra_variante(escenario, stock_inicial=5)
    try:
        creada = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        reserva = creada.json()

        cancelar = client.patch(f"/api/v1/reservas/{reserva['id']}/cancelar", headers=escenario.headers())
        assert cancelar.status_code == 200

        compatibles = client.get(
            "/api/v1/reservas/compatibles",
            params={"sucursal_id": escenario.sucursal.id},
            headers=escenario.headers(),
        )
        assert compatibles.json() == []

        agregar = client.post(
            f"/api/v1/reservas/{reserva['id']}/detalles",
            headers=escenario.headers(),
            json={"producto_variante_id": otra.id, "cantidad": 1},
        )
        assert agregar.status_code == 422
    finally:
        _limpiar_variante(otra)
        escenario.cleanup()


def test_otro_cliente_no_puede_agregar_a_una_reserva_ajena():
    escenario = _Escenario(stock_inicial=5)
    otro_cliente = _create_test_user(RolUsuario.CLIENTE)
    otra = _otra_variante(escenario, stock_inicial=5)
    try:
        creada = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        reserva_id = creada.json()["id"]

        respuesta = client.post(
            f"/api/v1/reservas/{reserva_id}/detalles",
            headers=_auth_headers(otro_cliente),
            json={"producto_variante_id": otra.id, "cantidad": 1},
        )
        assert respuesta.status_code == 404
    finally:
        _delete_test_user(otro_cliente.id)
        _limpiar_variante(otra)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 8. "Programar otra visita" (POST /reservas de siempre) sigue creando un
# código nuevo, incluso con una reserva PENDIENTE ya abierta en la sucursal.
# --------------------------------------------------------------------------


def test_crear_reserva_de_nuevo_genera_otro_codigo_aunque_haya_una_pendiente():
    escenario = _Escenario(stock_inicial=5)
    otra = _otra_variante(escenario, stock_inicial=5)
    try:
        primera = client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        assert primera.status_code == 201
        codigo_primera = primera.json()["codigo_reserva"]

        segunda = client.post(
            "/api/v1/reservas",
            headers=escenario.headers(),
            json=_payload(escenario, producto_variante_id=otra.id),
        )
        assert segunda.status_code == 201
        codigo_segunda = segunda.json()["codigo_reserva"]

        assert codigo_segunda != codigo_primera

        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert len(mias) == 2
        assert {r["codigo_reserva"] for r in mias} == {codigo_primera, codigo_segunda}
    finally:
        _limpiar_variante(otra)
        escenario.cleanup()
