"""Tests para CU12 — Consultar resultado de sincronización."""

from unittest.mock import MagicMock

import pytest

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from .service import ConsultarResultadoService


@pytest.fixture
def mock_db():
    """Mock Session para SQLAlchemy."""
    db = MagicMock()
    return db


@pytest.fixture
def actor_cajero():
    """Usuario Cajero autorizado."""
    return Usuario(
        id=2,
        empresa_id=100,
        sucursal_id=10,
        rol="CAJERO",
    )


@pytest.fixture
def actor_cliente():
    """Usuario Cliente."""
    return Usuario(
        id=1,
        empresa_id=100,
        sucursal_id=None,
        rol="CLIENTE",
    )


@pytest.fixture
def actor_otra_empresa():
    """Usuario de otra empresa."""
    return Usuario(
        id=99,
        empresa_id=999,
        sucursal_id=99,
        rol="CAJERO",
    )


class TestConsultarResultado:
    """Suite de pruebas para consultar resultados de sincronización."""

    def test_consultar_venta_autorizada(self, mock_db, actor_cajero):
        """Caso 1: Consultar venta sincronizada autorizada."""
        service = ConsultarResultadoService(mock_db)

        # Mock venta
        venta_mock = MagicMock()
        venta_mock.id = 1001
        venta_mock.codigo_venta = "V-001"
        venta_mock.total = 200.00
        venta_mock.created_at = MagicMock()
        venta_mock.empresa_id = 100
        venta_mock.sucursal_id = 10

        service.repo.obtener_venta_por_uuid_origen = MagicMock(return_value=venta_mock)

        resultado = service.consultar_resultado_venta(actor_cajero, "uuid-test-001")

        assert resultado is not None
        assert resultado.venta_id == 1001
        assert resultado.codigo_venta == "V-001"
        assert resultado.estado == "CONFIRMADA"

    def test_consultar_venta_no_existe(self, mock_db, actor_cajero):
        """Caso 2: Consultar venta que no existe."""
        service = ConsultarResultadoService(mock_db)

        service.repo.obtener_venta_por_uuid_origen = MagicMock(return_value=None)

        resultado = service.consultar_resultado_venta(actor_cajero, "uuid-inexistente")

        assert resultado is None

    def test_consultar_venta_otra_empresa(self, mock_db, actor_otra_empresa):
        """Caso 3: No autorizado para otra empresa."""
        service = ConsultarResultadoService(mock_db)

        resultado = service.consultar_resultado_venta(actor_otra_empresa, "uuid-test-001")

        assert resultado is None

    def test_consultar_reserva_cliente_propio(self, mock_db, actor_cliente):
        """Caso 4: Cliente consulta su propia reserva."""
        service = ConsultarResultadoService(mock_db)

        # Mock reserva
        reserva_mock = MagicMock()
        reserva_mock.id = 2001
        reserva_mock.cliente_id = 1  # Mismo cliente
        reserva_mock.created_at = MagicMock()
        reserva_mock.empresa_id = 100
        reserva_mock.sucursal_id = 10
        reserva_mock.codigo_reserva = "RES-001"

        service.repo.obtener_reserva_por_uuid_origen = MagicMock(
            return_value=reserva_mock
        )

        resultado = service.consultar_resultado_reserva(actor_cliente, "uuid-res-001")

        assert resultado is not None
        assert resultado.reserva_id == 2001
        assert resultado.estado == "CONFIRMADA"

    def test_consultar_reserva_cliente_ajena(self, mock_db, actor_cliente):
        """Caso 5: Cliente no puede consultar reserva ajena."""
        service = ConsultarResultadoService(mock_db)

        # Mock reserva de otro cliente
        reserva_mock = MagicMock()
        reserva_mock.cliente_id = 999  # Otro cliente

        service.repo.obtener_reserva_por_uuid_origen = MagicMock(
            return_value=reserva_mock
        )

        resultado = service.consultar_resultado_reserva(actor_cliente, "uuid-res-ajena")

        assert resultado is None

    def test_listar_ventas_autorizado(self, mock_db, actor_cajero):
        """Caso 6: Listar ventas sincronizadas autorizadas."""
        service = ConsultarResultadoService(mock_db)

        # Mock lista de ventas
        ventas_mock = [MagicMock(), MagicMock()]
        for i, v in enumerate(ventas_mock):
            v.uuid_operacion_offline = f"uuid-{i}"
            v.id = 1000 + i
            v.codigo_venta = f"V-{i:03d}"
            v.total = 100 * (i + 1)
            v.created_at = MagicMock()
            v.empresa_id = 100
            v.sucursal_id = 10

        service.repo.listar_ventas_sincronizadas = MagicMock(return_value=ventas_mock)

        resultados = service.listar_resultados_venta(actor_cajero)

        assert len(resultados) == 2
        assert resultados[0].venta_id == 1000

    def test_resumen_conteos(self, mock_db, actor_cajero):
        """Caso 7: Obtener resumen de conteos."""
        service = ConsultarResultadoService(mock_db)

        # Mock listas
        service.repo.listar_ventas_sincronizadas = MagicMock(return_value=[])
        service.repo.listar_reservas_sincronizadas = MagicMock(return_value=[])

        resumen = service.obtener_resumen(actor_cajero)

        assert resumen.confirmadas >= 0
        assert resumen.rechazadas >= 0
        assert resumen.conflictos >= 0
