"""Pruebas del modelo de dominio de Reservas -- una reserva agrupa varias
prendas (Reserva = cabecera, ReservaDetalle = una prenda dentro de ella, ver
Models/reserva.py).

CU17 (Crear reserva) todavía NO expone un carrito -- el Cliente sigue
reservando una prenda a la vez desde la ficha de producto (CU21, fuera de
alcance). Por eso, para probar que la ARQUITECTURA sí soporta varias prendas
por reserva, este archivo arma ese escenario directo contra el modelo
(`_reserva_con_varios_detalles`, más abajo) -- exactamente lo que produciría
un futuro carrito, o lo que ya produjo la migración de datos (cada reserva
antigua = 1 cabecera + 1 detalle, ver
alembic/versions/*_split_reserva_cabecera_detalle.py) para una reserva que
después crezca a más de un detalle.

Cubre lo que pide la migración estructural:
  1. Una reserva puede contener múltiples detalles (varias prendas).
  2. El Cliente ve UNA sola reserva agrupada (GET /reservas/mias), no una
     tarjeta por prenda.
  3. El Encargado ve el panel agrupado igual (GET /reservas/panel).
  4. Cancelar una prenda libera solo su stock, sin afectar a las demás.
  5. Atender una prenda (CU20) no afecta al estado de las demás.
  6. La migración conserva cada reserva antigua -- round-trip completo
     "cabecera con 1 detalle" (la forma exacta que dejó la migración de
     datos) a través de los endpoints reales de CU17/CU18.
"""

import uuid
from datetime import date, time, timedelta

from tests.test_crear_reserva_prendas import (
    _auth_headers,
    _create_test_user,
    _delete_test_user,
    _fecha_hora_segura,
    _Escenario,
)
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva, Reserva, ReservaDetalle

client = TestClient(app)


class _EscenarioMultiple(_Escenario):
    """Mismo escenario de CU17 (producto/sucursal/cliente), más N variantes
    adicionales (tallas distintas del mismo producto) con su propio stock --
    "Chaqueta negra M", "Camisa blanca S", "Pantalón azul 36" del enunciado
    son, en este dominio, 3 ProductoVariante distintas reservadas en la
    MISMA visita."""

    def __init__(self, *, n_prendas_extra: int = 2, stock_inicial: int = 5):
        super().__init__(stock_inicial=stock_inicial)
        self.variantes_extra: list[ProductoVariante] = []
        # Usa self.db (la MISMA sesión abierta por _Escenario.__init__, que
        # se mantiene viva hasta cleanup()) en vez de una sesión local que se
        # cierra al salir de este método -- si se cerrara aquí, los objetos
        # quedarían "detached" y expirados, y leer variante.id/.talla_id más
        # adelante (todas_las_variantes(), cleanup()) fallaría con
        # DetachedInstanceError.
        for _ in range(n_prendas_extra):
            sufijo = uuid.uuid4().hex[:8]
            talla = Talla(nombre=f"Talla-{sufijo}", is_active=True)
            color = Color(nombre=f"Color-{sufijo}", is_active=True)
            self.db.add_all([talla, color])
            self.db.commit()
            variante = ProductoVariante(
                producto_id=self.producto.id, talla_id=talla.id, color_id=color.id, is_active=True
            )
            self.db.add(variante)
            self.db.commit()
            self.db.refresh(variante)
            self.db.add(
                StockSucursal(
                    sucursal_id=self.sucursal.id, producto_variante_id=variante.id, cantidad=stock_inicial
                )
            )
            self.db.commit()
            self.variantes_extra.append(variante)

    def todas_las_variantes(self) -> list[ProductoVariante]:
        return [self.variante, *self.variantes_extra]

    def stock_reservado_de(self, variante: ProductoVariante) -> int:
        db = SessionLocal()
        try:
            fila = (
                db.query(StockSucursal)
                .filter(
                    StockSucursal.sucursal_id == self.sucursal.id,
                    StockSucursal.producto_variante_id == variante.id,
                )
                .first()
            )
            return fila.stock_reservado if fila else 0
        finally:
            db.close()

    def cleanup(self) -> None:
        # Sigue usando self.db (todavía abierta) -- super().cleanup() es
        # quien la cierra al final, después de que esta limpieza propia ya
        # terminó de usarla.
        variante_ids = [v.id for v in self.variantes_extra]
        if variante_ids:
            self.db.query(ReservaDetalle).filter(
                ReservaDetalle.producto_variante_id.in_(variante_ids)
            ).delete(synchronize_session=False)
            self.db.commit()
            self.db.query(StockSucursal).filter(
                StockSucursal.producto_variante_id.in_(variante_ids)
            ).delete(synchronize_session=False)
            self.db.commit()
            for variante in self.variantes_extra:
                talla_id, color_id = variante.talla_id, variante.color_id
                self.db.delete(variante)
                self.db.commit()
                talla = self.db.get(Talla, talla_id)
                if talla is not None:
                    self.db.delete(talla)
                color = self.db.get(Color, color_id)
                if color is not None:
                    self.db.delete(color)
                self.db.commit()
        super().cleanup()


def _reserva_con_varios_detalles(
    escenario: _EscenarioMultiple, *, cantidad_por_detalle: int = 1
) -> Reserva:
    """Arma UNA Reserva (cabecera) con un ReservaDetalle por cada variante de
    `escenario.todas_las_variantes()` -- exactamente la forma que dejaría un
    futuro carrito de CU17 (o la migración de datos, para una reserva con
    más de un detalle), incrementando `stock_reservado` fila por fila igual
    que hace CrearReservaService.crear() para una sola prenda.

    Usa escenario.db (la sesión larga del escenario) en vez de abrir y
    cerrar una propia -- los tests llaman a esta función y después siguen
    leyendo `reserva.detalles` directamente sobre el objeto devuelto; si la
    sesión que lo cargó ya estuviera cerrada, esa lectura (lazy load)
    fallaría con DetachedInstanceError."""
    fecha, hora = _fecha_hora_segura()
    db = escenario.db
    detalles = []
    for variante in escenario.todas_las_variantes():
        stock = (
            db.query(StockSucursal)
            .filter(
                StockSucursal.sucursal_id == escenario.sucursal.id,
                StockSucursal.producto_variante_id == variante.id,
            )
            # of=StockSucursal: StockSucursal.sucursal/.producto_variante son
            # relationship(lazy="joined") -- sin restringir el FOR UPDATE a
            # esta tabla, Postgres intenta bloquear también las filas del
            # JOIN (lado "nullable" de un LEFT OUTER JOIN) y falla. Mismo
            # criterio que StockSucursalRepository.bloquear_para_reservar.
            .with_for_update(of=StockSucursal)
            .one()
        )
        stock.stock_reservado += cantidad_por_detalle
        detalles.append(
            ReservaDetalle(
                producto_variante_id=variante.id,
                cantidad=cantidad_por_detalle,
                estado=EstadoReserva.PENDIENTE,
            )
        )
    reserva = Reserva(
        # codigo_reserva es NOT NULL -- placeholder temporal descartado
        # por el flush de abajo, mismo patrón que ReservaRepository.crear.
        codigo_reserva=uuid.uuid4().hex[:20],
        cliente_id=escenario.cliente.id,
        sucursal_id=escenario.sucursal.id,
        fecha_reserva=fecha,
        hora_inicio=hora,
        estado_general=EstadoReserva.PENDIENTE,
        detalles=detalles,
    )
    db.add(reserva)
    db.flush()
    reserva.codigo_reserva = f"RS-{reserva.id:05d}"
    db.commit()
    db.refresh(reserva)
    return reserva


# --------------------------------------------------------------------------
# 1/2. Una reserva puede contener múltiples detalles -- el Cliente ve UNA
# sola reserva agrupada, con todas sus prendas anidadas.
# --------------------------------------------------------------------------


def test_una_reserva_puede_contener_multiples_detalles():
    escenario = _EscenarioMultiple(n_prendas_extra=2)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        assert len(reserva.detalles) == 3
        assert len({d.producto_variante_id for d in reserva.detalles}) == 3
    finally:
        escenario.cleanup()


def test_cliente_ve_una_sola_reserva_con_varias_prendas():
    escenario = _EscenarioMultiple(n_prendas_extra=2)
    try:
        reserva = _reserva_con_varios_detalles(escenario)

        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        # UNA sola tarjeta -- no una fila por prenda.
        assert len(mias) == 1
        assert mias[0]["id"] == reserva.id
        assert mias[0]["codigo_reserva"] == reserva.codigo_reserva
        assert len(mias[0]["detalles"]) == 3
        variantes_en_detalles = {d["variante"]["id"] for d in mias[0]["detalles"]}
        assert variantes_en_detalles == {v.id for v in escenario.todas_las_variantes()}
    finally:
        escenario.cleanup()


def test_encargado_ve_reservas_agrupadas_en_el_panel():
    escenario = _EscenarioMultiple(n_prendas_extra=2)
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)
    try:
        reserva = _reserva_con_varios_detalles(escenario)

        panel = client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado)).json()
        assert len(panel) == 1
        fila = panel[0]
        assert fila["id"] == reserva.id
        assert fila["cliente"]["nombre"] == escenario.cliente.nombre
        assert len(fila["detalles"]) == 3
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 3. Cancelar una prenda libera solo su stock -- las demás siguen intactas.
# --------------------------------------------------------------------------


def test_cancelar_una_prenda_libera_solo_su_stock_sin_afectar_a_las_demas():
    escenario = _EscenarioMultiple(n_prendas_extra=2, stock_inicial=5)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        chaqueta, camisa, pantalon = reserva.detalles
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 1

        # Rechaza SOLO la camisa.
        response = client.patch(
            f"/api/v1/reservas/detalles/{camisa.id}/cancelar", headers=escenario.headers()
        )
        assert response.status_code == 200
        assert response.json()["estado"] == "CANCELADA"

        # Stock de la camisa liberado; chaqueta y pantalón intactos.
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 0
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[0]) == 1
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[2]) == 1

        # La reserva agrupada refleja: 2 activas, 1 cancelada -- estado
        # general sigue PENDIENTE (todavía hay prendas por atender).
        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()[0]
        estados = {d["id"]: d["estado"] for d in mias["detalles"]}
        assert estados[chaqueta.id] == "PENDIENTE"
        assert estados[camisa.id] == "CANCELADA"
        assert estados[pantalon.id] == "PENDIENTE"
        assert mias["estado_general"] == "PENDIENTE"
    finally:
        escenario.cleanup()


def test_cancelar_la_reserva_completa_cancela_solo_los_detalles_activos():
    escenario = _EscenarioMultiple(n_prendas_extra=2, stock_inicial=5)
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        chaqueta, camisa, pantalon = reserva.detalles

        # El Encargado ya resolvió la chaqueta (preparada -> reserva
        # EN_ATENCION -> decidida "enviar a caja") -- ya no debe poder
        # cancelarse junto con el resto, que sigue PENDIENTE.
        client.patch(
            f"/api/v1/reservas/detalles/{chaqueta.id}/preparar", headers=_auth_headers(encargado)
        )
        client.patch(
            f"/api/v1/reservas/{reserva.id}/confirmar-llegada", headers=_auth_headers(encargado)
        )
        client.patch(
            f"/api/v1/reservas/detalles/{chaqueta.id}/enviar-a-caja", headers=_auth_headers(encargado)
        )

        response = client.patch(f"/api/v1/reservas/{reserva.id}/cancelar", headers=escenario.headers())
        assert response.status_code == 200
        body = response.json()
        estados = {d["id"]: d["estado"] for d in body["detalles"]}
        assert estados[chaqueta.id] == "LISTA_PARA_CAJA"  # intacta -- ya no era cancelable.
        assert estados[camisa.id] == "CANCELADA"
        assert estados[pantalon.id] == "CANCELADA"
        # La cabecera sigue EN_ATENCION -- CU19 no la recalcula una vez que
        # ya avanzó más allá de la fase previa a la llegada.
        assert body["estado_general"] == "EN_ATENCION"

        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[0]) == 1  # chaqueta, intacta.
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 0  # camisa, liberada.
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[2]) == 0  # pantalón, liberado.
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 4. Atender una prenda no afecta a las demás.
# --------------------------------------------------------------------------


def test_atender_una_prenda_no_afecta_el_estado_de_las_demas():
    escenario = _EscenarioMultiple(n_prendas_extra=2, stock_inicial=5)
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        chaqueta, camisa, pantalon = reserva.detalles

        # Ejemplo del enunciado: Chaqueta -> LISTA_PARA_CAJA (decisión, sin
        # finalizar todavía), Camisa -> CANCELADA (por el Cliente, CU19),
        # Pantalón -> sigue PENDIENTE, sin tocar.
        client.patch(
            f"/api/v1/reservas/detalles/{chaqueta.id}/preparar", headers=_auth_headers(encargado)
        )
        client.patch(
            f"/api/v1/reservas/{reserva.id}/confirmar-llegada", headers=_auth_headers(encargado)
        )
        respuesta_chaqueta = client.patch(
            f"/api/v1/reservas/detalles/{chaqueta.id}/enviar-a-caja", headers=_auth_headers(encargado)
        )
        assert respuesta_chaqueta.status_code == 200
        assert respuesta_chaqueta.json()["estado"] == "LISTA_PARA_CAJA"

        respuesta_camisa = client.patch(
            f"/api/v1/reservas/detalles/{camisa.id}/cancelar", headers=escenario.headers()
        )
        assert respuesta_camisa.status_code == 200

        panel = client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado)).json()
        fila = next(f for f in panel if f["id"] == reserva.id)
        estados = {d["id"]: d["estado"] for d in fila["detalles"]}
        assert estados[chaqueta.id] == "LISTA_PARA_CAJA"
        assert estados[camisa.id] == "CANCELADA"
        assert estados[pantalon.id] == "PENDIENTE"  # nunca tocado.

        # Stock: chaqueta sigue reservada (decisión "a caja", stock se
        # libera/confirma recién al finalizar atención), camisa liberada,
        # pantalón sigue reservado (todavía activo).
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[0]) == 1
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 0
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[2]) == 1
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 5. Migración conserva reservas antiguas -- round-trip de la forma exacta
# que dejó la migración de datos: 1 reserva vieja = 1 cabecera + 1 detalle.
# --------------------------------------------------------------------------


def test_migracion_conserva_reservas_antiguas_como_cabecera_con_un_detalle():
    """No re-ejecuta Alembic (no es lo que un test de pytest debe hacer) --
    verifica que la FORMA que la migración garantiza para cada fila vieja
    (ver alembic/versions/*_split_reserva_cabecera_detalle.py, paso 3: "1
    reserva vieja = 1 cabecera + 1 detalle") sigue siendo consultable y
    correcta end-to-end a través de los endpoints reales de CU17/CU18,
    preservando cliente, sucursal, producto, cantidad, fecha, hora y
    estado."""
    escenario = _Escenario(stock_inicial=5)
    try:
        fecha = date.today() + timedelta(days=3)
        db = SessionLocal()
        try:
            stock = (
                db.query(StockSucursal)
                .filter(
                    StockSucursal.sucursal_id == escenario.sucursal.id,
                    StockSucursal.producto_variante_id == escenario.variante.id,
                )
                .one()
            )
            stock.stock_reservado += 2
            detalle = ReservaDetalle(
                producto_variante_id=escenario.variante.id, cantidad=2, estado=EstadoReserva.ATENDIDA
            )
            reserva = Reserva(
                codigo_reserva=uuid.uuid4().hex[:20],
                cliente_id=escenario.cliente.id,
                sucursal_id=escenario.sucursal.id,
                fecha_reserva=fecha,
                hora_inicio=time(15, 0),
                estado_general=EstadoReserva.ATENDIDA,
                detalles=[detalle],
            )
            db.add(reserva)
            db.flush()
            reserva.codigo_reserva = f"RS-{reserva.id:05d}"
            db.commit()
            db.refresh(reserva)
            reserva_id = reserva.id
        finally:
            db.close()

        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert len(mias) == 1
        migrada = mias[0]
        assert migrada["id"] == reserva_id
        assert migrada["sucursal"]["id"] == escenario.sucursal.id
        assert migrada["fecha_reserva"] == fecha.isoformat()
        assert migrada["hora_inicio"].startswith("15:00")
        assert migrada["estado_general"] == "ATENDIDA"
        assert len(migrada["detalles"]) == 1
        assert migrada["detalles"][0]["cantidad"] == 2
        assert migrada["detalles"][0]["estado"] == "ATENDIDA"
        assert migrada["detalles"][0]["variante"]["id"] == escenario.variante.id
        assert migrada["detalles"][0]["producto"]["nombre"] == escenario.producto.nombre
    finally:
        escenario.cleanup()
