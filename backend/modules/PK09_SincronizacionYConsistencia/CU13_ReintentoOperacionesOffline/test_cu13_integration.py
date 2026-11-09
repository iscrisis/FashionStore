"""Pruebas de integración para CU13 — Validación funcional completa.

Tests con mocks para validar:
- Flujo de reintento con fallo temporal recuperable
- Preservación de UUID
- Consulta de CU12 (no duplicar)
- Reutilización de CU11
- Registro en auditoría
- Sin duplicación de ventas/reservas
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.Models.operacion_sincronizacion_log import OperacionSincronizacionLog

from .service import ReintentoService
from .repository import ReintentoRepository
from .schemas import ReintentoRequest, BackoffConfig


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def usuario_cajero() -> Usuario:
    """Usuario CAJERO para pruebas."""
    usuario = Mock(spec=Usuario)
    usuario.id = 1
    usuario.empresa_id = 1
    usuario.sucursal_id = 1
    usuario.rol = "CAJERO"
    usuario.email = "cajero@test.com"
    return usuario


@pytest.fixture
def usuario_cliente() -> Usuario:
    """Usuario CLIENTE para pruebas."""
    usuario = Mock(spec=Usuario)
    usuario.id = 2
    usuario.empresa_id = 1
    usuario.sucursal_id = 1
    usuario.rol = "CLIENTE"
    usuario.email = "cliente@test.com"
    return usuario


@pytest.fixture
def mock_db() -> Mock:
    """Mock de sesión de BD."""
    db = Mock(spec=Session)
    db.commit = Mock()
    db.add = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def request_venta() -> ReintentoRequest:
    """Request para reintentar venta."""
    return ReintentoRequest(empresa_id=1)


# ============================================================================
# TESTS: Validación de Backoff
# ============================================================================

class TestBackoffPolicy:
    """Validar política de backoff exponencial."""

    def test_backoff_exponencial_correcto(self):
        """Verificar esperas en ms: 1s, 2s, 5s, 10s, 30s."""
        config = BackoffConfig()

        assert config.obtener_espera_ms(1) == 1000
        assert config.obtener_espera_ms(2) == 2000
        assert config.obtener_espera_ms(3) == 5000
        assert config.obtener_espera_ms(4) == 10000
        assert config.obtener_espera_ms(5) == 30000

    def test_max_intentos_es_5(self):
        """Verificar límite máximo."""
        config = BackoffConfig()
        assert config.max_intentos == 5


# ============================================================================
# TESTS: Repository — Auditoría
# ============================================================================

class TestAuditoriaRepository:
    """Validar registro en operaciones_sincronizacion_log."""

    def test_registrar_intento_venta(self, mock_db: Mock):
        """Registrar intento de venta en auditoría."""
        repo = ReintentoRepository(mock_db)

        # Mock de la tabla
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Registrar
        repo.registrar_intento(
            empresa_id=1,
            uuid_operacion="uuid-venta-001",
            tipo_operacion="VENTA_OFFLINE",
            numero_intento=1,
            estado_resultado="RECHAZADA",
            motivo="Stock insuficiente",
            error_tipo=None,
            http_status=200,
            tiempo_respuesta_ms=150,
            usuario_id=1,
        )

        # Verificar que se agregó a BD
        mock_db.add.assert_called_once()
        log_registrado = mock_db.add.call_args[0][0]

        assert log_registrado.uuid_operacion_offline == "uuid-venta-001"
        assert log_registrado.tipo_operacion == "VENTA_OFFLINE"
        assert log_registrado.numero_intento == 1
        assert log_registrado.estado_resultado == "RECHAZADA"
        assert log_registrado.motivo == "Stock insuficiente"
        assert log_registrado.usuario_id == 1

    def test_registrar_intento_reserva(self, mock_db: Mock):
        """Registrar intento de reserva en auditoría."""
        repo = ReintentoRepository(mock_db)
        mock_db.add = Mock()

        repo.registrar_intento(
            empresa_id=1,
            uuid_operacion="uuid-reserva-001",
            tipo_operacion="RESERVA_OFFLINE",
            numero_intento=2,
            estado_resultado="CONFIRMADA",
            usuario_id=2,
        )

        log_registrado = mock_db.add.call_args[0][0]
        assert log_registrado.uuid_operacion_offline == "uuid-reserva-001"
        assert log_registrado.tipo_operacion == "RESERVA_OFFLINE"
        assert log_registrado.numero_intento == 2
        assert log_registrado.estado_resultado == "CONFIRMADA"


# ============================================================================
# TESTS: Elegibilidad y Backoff
# ============================================================================

class TestElegibilidadReintento:
    """Validar lógica de elegibilidad y backoff."""

    def test_reintento_bloqueado_por_backoff(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """Reintento bloqueado si no pasó el backoff."""
        service = ReintentoService(mock_db)

        # Mock: último intento hace 500ms (necesita 2000ms)
        intento_anterior = Mock(spec=OperacionSincronizacionLog)
        intento_anterior.fecha_intento = datetime.utcnow() - timedelta(milliseconds=500)

        with patch.object(service.repo, 'obtener_historial_intento', return_value=[intento_anterior]):
            with patch.object(service.repo, 'obtener_venta_por_uuid', return_value=None):
                resultado = service.reintentar_venta(usuario_cajero, "uuid-001", request_venta)

        assert resultado.estado == "RECHAZADA"
        assert "esperar" in resultado.motivo.lower()
        assert resultado.proximo_reintento_en_ms > 0

    def test_reintento_rechazado_max_intentos(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """Reintento rechazado si se alcanzó máximo de intentos."""
        service = ReintentoService(mock_db)

        # Mock: 5 intentos anteriores (máximo)
        intentos_anteriores = [Mock(spec=OperacionSincronizacionLog) for _ in range(5)]

        with patch.object(service.repo, 'obtener_historial_intento', return_value=intentos_anteriores):
            resultado = service.reintentar_venta(usuario_cajero, "uuid-max", request_venta)

        assert resultado.estado == "RECHAZADA"
        assert "Máximo de reintentos" in resultado.motivo
        assert resultado.numero_intento == 6


# ============================================================================
# TESTS: Flujo de Reintento — Venta
# ============================================================================

class TestReintentoVenta:
    """Validar flujo completo de reintento de venta."""

    def test_reintento_venta_fallido_primera_vez(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """Primer intento falla (stock insuficiente)."""
        service = ReintentoService(mock_db)
        uuid_venta = "uuid-venta-fallida-001"

        # Mock: Sin intentos anteriores (primer reintento)
        # Mock: CU12 retorna venta no confirmada
        # Mock: CU11 retorna error de stock
        mock_venta = Mock()
        mock_venta.sucursal_id = 1
        mock_venta.fecha_creacion = datetime.utcnow()
        mock_venta.total = 150.00

        resultado_cu12 = Mock()
        resultado_cu12.estado = "RECHAZADA"
        resultado_cu12.motivo = "Stock insuficiente"

        resultado_cu11 = Mock()
        resultado_cu11.estado = "RECHAZADA"
        resultado_cu11.motivo = "Stock insuficiente para producto_variante_id=5"
        resultado_cu11.venta_id = None
        resultado_cu11.codigo_venta = None
        resultado_cu11.total = 150.00

        with patch.object(service.repo, 'obtener_historial_intento', return_value=[]):
            with patch.object(service.repo, 'obtener_venta_por_uuid', return_value=mock_venta):
                with patch.object(service.consultar_service, 'consultar_resultado_venta', return_value=None):
                    with patch.object(service.repo, 'obtener_detalles_venta_offline', return_value=[]):
                        with patch.object(service.sincronizar_service, 'sincronizar_venta_offline', return_value=resultado_cu11):
                            resultado = service.reintentar_venta(usuario_cajero, uuid_venta, request_venta)

        # Verificar resultado
        assert resultado.uuid_local == uuid_venta
        assert resultado.tipo_operacion == "VENTA_OFFLINE"
        assert resultado.estado == "RECHAZADA"
        assert resultado.motivo == "Stock insuficiente para producto_variante_id=5"
        assert resultado.numero_intento == 1
        assert resultado.proximo_reintento_en_ms == 1000  # Backoff para intento 2

    def test_reintento_venta_exitoso_segundo_intento(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """Segundo intento exitoso (fallo temporal recuperado)."""
        service = ReintentoService(mock_db)
        uuid_venta = "uuid-venta-ok-001"

        # Mock: Un intento anterior que falló hace >2000ms
        intento_anterior = Mock(spec=OperacionSincronizacionLog)
        intento_anterior.fecha_intento = datetime.utcnow() - timedelta(seconds=3)
        intento_anterior.estado_resultado = "RECHAZADA"

        mock_venta = Mock()
        mock_venta.sucursal_id = 1
        mock_venta.fecha_creacion = datetime.utcnow()
        mock_venta.total = 250.00

        resultado_cu11 = Mock()
        resultado_cu11.estado = "CONFIRMADA"
        resultado_cu11.motivo = None
        resultado_cu11.venta_id = 123
        resultado_cu11.codigo_venta = "V-001"
        resultado_cu11.total = 250.00

        with patch.object(service.repo, 'obtener_historial_intento', return_value=[intento_anterior]):
            with patch.object(service.repo, 'obtener_venta_por_uuid', return_value=mock_venta):
                with patch.object(service.consultar_service, 'consultar_resultado_venta', return_value=None):
                    with patch.object(service.repo, 'obtener_detalles_venta_offline', return_value=[]):
                        with patch.object(service.sincronizar_service, 'sincronizar_venta_offline', return_value=resultado_cu11):
                            resultado = service.reintentar_venta(usuario_cajero, uuid_venta, request_venta)

        # Verificar resultado
        assert resultado.uuid_local == uuid_venta
        assert resultado.estado == "CONFIRMADA"
        assert resultado.venta_id == 123
        assert resultado.codigo_venta == "V-001"
        assert resultado.numero_intento == 2
        assert resultado.proximo_reintento_en_ms == 0

    def test_reintento_venta_ya_sincronizada(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """Venta ya estaba sincronizada en intento anterior (CU12)."""
        service = ReintentoService(mock_db)
        uuid_venta = "uuid-venta-sync-001"

        resultado_cu12 = Mock()
        resultado_cu12.estado = "CONFIRMADA"
        resultado_cu12.venta_id = 100
        resultado_cu12.codigo_venta = "V-100"

        with patch.object(service.repo, 'obtener_historial_intento', return_value=[]):
            with patch.object(service.consultar_service, 'consultar_resultado_venta', return_value=resultado_cu12):
                resultado = service.reintentar_venta(usuario_cajero, uuid_venta, request_venta)

        # Verificar que NO se llamó CU11 (ya estaba sincronizada)
        assert resultado.estado == "CONFIRMADA"
        assert resultado.motivo == "Ya fue sincronizada en intento anterior"
        assert resultado.venta_id == 100


# ============================================================================
# TESTS: Flujo de Reintento — Reserva
# ============================================================================

class TestReintentoReserva:
    """Validar flujo completo de reintento de reserva."""

    def test_reintento_reserva_fallido(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """Reintento de reserva falla."""
        service = ReintentoService(mock_db)
        uuid_reserva = "uuid-reserva-001"

        mock_reserva = Mock()
        mock_reserva.sucursal_id = 1
        mock_reserva.fecha_creacion = datetime.utcnow()
        mock_reserva.total = 300.00

        resultado_cu11 = Mock()
        resultado_cu11.estado = "RECHAZADA"
        resultado_cu11.motivo = "Cliente sin saldo"
        resultado_cu11.reserva_id = None

        with patch.object(service.repo, 'obtener_historial_intento', return_value=[]):
            with patch.object(service.repo, 'obtener_reserva_por_uuid', return_value=mock_reserva):
                with patch.object(service.consultar_service, 'consultar_resultado_reserva', return_value=None):
                    with patch.object(service.repo, 'obtener_detalles_reserva_offline', return_value=[]):
                        with patch.object(service.sincronizar_service, 'sincronizar_reserva_offline', return_value=resultado_cu11):
                            resultado = service.reintentar_reserva(usuario_cajero, uuid_reserva, request_venta)

        assert resultado.estado == "RECHAZADA"
        assert resultado.motivo == "Cliente sin saldo"
        assert resultado.numero_intento == 1


# ============================================================================
# TESTS: Reutilización de CU11 (Sin Duplicación)
# ============================================================================

class TestReutilizacionCU11:
    """Validar que CU13 reutiliza CU11 sin duplicar lógica."""

    def test_cu13_llama_cu11_una_sola_vez(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """CU13 llama CU11 exactamente una vez por reintento."""
        service = ReintentoService(mock_db)
        uuid_venta = "uuid-cu11-call-001"

        mock_venta = Mock()
        mock_venta.sucursal_id = 1
        mock_venta.fecha_creacion = datetime.utcnow()
        mock_venta.total = 150.00

        resultado_cu11 = Mock()
        resultado_cu11.estado = "CONFIRMADA"
        resultado_cu11.motivo = None
        resultado_cu11.venta_id = 50
        resultado_cu11.codigo_venta = "V-50"
        resultado_cu11.total = 150.00

        with patch.object(service.repo, 'obtener_historial_intento', return_value=[]):
            with patch.object(service.repo, 'obtener_venta_por_uuid', return_value=mock_venta):
                with patch.object(service.consultar_service, 'consultar_resultado_venta', return_value=None):
                    with patch.object(service.repo, 'obtener_detalles_venta_offline', return_value=[]):
                        with patch.object(service.sincronizar_service, 'sincronizar_venta_offline', return_value=resultado_cu11) as mock_cu11:
                            service.reintentar_venta(usuario_cajero, uuid_venta, request_venta)

        # Verificar que CU11 se llamó exactamente una vez
        assert mock_cu11.call_count == 1

    def test_cu13_consulta_cu12_antes_de_cu11(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """CU13 consulta CU12 ANTES de llamar CU11 (evitar trabajo innecesario)."""
        service = ReintentoService(mock_db)
        uuid_venta = "uuid-cu12-first-001"

        # Ya fue sincronizada en CU12
        resultado_cu12 = Mock()
        resultado_cu12.estado = "CONFIRMADA"
        resultado_cu12.venta_id = 200
        resultado_cu12.codigo_venta = "V-200"

        with patch.object(service.repo, 'obtener_historial_intento', return_value=[]):
            with patch.object(service.consultar_service, 'consultar_resultado_venta', return_value=resultado_cu12) as mock_cu12:
                with patch.object(service.sincronizar_service, 'sincronizar_venta_offline') as mock_cu11:
                    service.reintentar_venta(usuario_cajero, uuid_venta, request_venta)

        # CU12 se llamó
        assert mock_cu12.call_count == 1
        # CU11 NO se llamó (porque ya estaba sincronizada)
        assert mock_cu11.call_count == 0


# ============================================================================
# TESTS: Preservación de UUID
# ============================================================================

class TestPreservacionUUID:
    """Validar que UUID se preserva en toda la cadena."""

    def test_uuid_preservado_en_auditori(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """UUID se mantiene igual en registro de auditoría."""
        service = ReintentoService(mock_db)
        uuid_original = "uuid-preserve-12345"

        mock_venta = Mock()
        mock_venta.sucursal_id = 1
        mock_venta.fecha_creacion = datetime.utcnow()
        mock_venta.total = 100.00

        resultado_cu11 = Mock()
        resultado_cu11.estado = "CONFIRMADA"
        resultado_cu11.motivo = None
        resultado_cu11.venta_id = 10
        resultado_cu11.codigo_venta = "V-10"
        resultado_cu11.total = 100.00

        with patch.object(service.repo, 'obtener_historial_intento', return_value=[]):
            with patch.object(service.repo, 'obtener_venta_por_uuid', return_value=mock_venta):
                with patch.object(service.consultar_service, 'consultar_resultado_venta', return_value=None):
                    with patch.object(service.repo, 'obtener_detalles_venta_offline', return_value=[]):
                        with patch.object(service.sincronizar_service, 'sincronizar_venta_offline', return_value=resultado_cu11):
                            with patch.object(service.repo, 'registrar_intento') as mock_audit:
                                service.reintentar_venta(usuario_cajero, uuid_original, request_venta)

        # Verificar que UUID se pasó a auditoría
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args.kwargs['uuid_operacion'] == uuid_original

    def test_uuid_retornado_en_resultado(
        self, mock_db: Mock, usuario_cajero: Usuario, request_venta: ReintentoRequest
    ):
        """UUID se retorna en ReintentoResultado."""
        service = ReintentoService(mock_db)
        uuid_original = "uuid-result-xyz"

        mock_venta = Mock()
        mock_venta.sucursal_id = 1
        mock_venta.fecha_creacion = datetime.utcnow()
        mock_venta.total = 75.00

        resultado_cu11 = Mock()
        resultado_cu11.estado = "CONFIRMADA"
        resultado_cu11.motivo = None
        resultado_cu11.venta_id = 5
        resultado_cu11.codigo_venta = "V-5"
        resultado_cu11.total = 75.00

        with patch.object(service.repo, 'obtener_historial_intento', return_value=[]):
            with patch.object(service.repo, 'obtener_venta_por_uuid', return_value=mock_venta):
                with patch.object(service.consultar_service, 'consultar_resultado_venta', return_value=None):
                    with patch.object(service.repo, 'obtener_detalles_venta_offline', return_value=[]):
                        with patch.object(service.sincronizar_service, 'sincronizar_venta_offline', return_value=resultado_cu11):
                            resultado = service.reintentar_venta(usuario_cajero, uuid_original, request_venta)

        assert resultado.uuid_local == uuid_original


# ============================================================================
# TESTS: Autenticación y Autorización
# ============================================================================

class TestAutenticacionAutorizacion:
    """Validar restricciones de acceso."""

    def test_empresa_no_autorizada(
        self, mock_db: Mock, usuario_cajero: Usuario
    ):
        """Rechazar si empresa_id no coincide."""
        service = ReintentoService(mock_db)
        usuario_cajero.empresa_id = 1
        request_otra_empresa = ReintentoRequest(empresa_id=2)

        with pytest.raises(PermissionError, match="Empresa no autorizada"):
            service.reintentar_venta(usuario_cajero, "uuid", request_otra_empresa)

    def test_rol_no_autorizado(self, mock_db: Mock, usuario_cliente: Usuario):
        """CLIENTE no puede reintentar ventas."""
        service = ReintentoService(mock_db)
        request_venta = ReintentoRequest(empresa_id=1)

        with pytest.raises(PermissionError, match="no autorizado"):
            service.reintentar_venta(usuario_cliente, "uuid", request_venta)


if __name__ == "__main__":
    # Ejecutar: pytest test_cu13_integration.py -v
    pytest.main([__file__, "-v", "--tb=short"])
