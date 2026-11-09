"""Tests para CU11 — Sincronizar operaciones pendientes.

Casos de prueba:
1. Venta válida sincroniza y crea Venta + Pago
2. UUID duplicado retorna resultado anterior (idempotencia)
3. Stock insuficiente retorna CONFLICTO
4. Empresa no autorizada rechaza
5. Sucursal no autorizada rechaza
6. Detalles vacíos rechaza
7. Total negativo rechaza
8. Transacción rollback en error
9. Pago en efectivo procesado correctamente
10. Contacto multitenant con empresa_id diferente rechaza
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P5_ComprasVentasYPagos.CU24_RegistrarVentaPresencial.service import (
    StockInsuficienteError,
    VarianteNoEncontradaError,
)
from modules.PK09_SincronizacionYConsistencia.CU11_SincronizarOperacionesPendientes.schemas import (
    ResultadoSincronizacionVenta,
    SincronizarVentaOfflineDetalleIn,
    SincronizarVentaOfflineIn,
)
from modules.PK09_SincronizacionYConsistencia.CU11_SincronizarOperacionesPendientes.service import (
    SincronizarOperacionesPendientesService,
    ValidacionError,
)


@pytest.fixture
def mock_db():
    """Mock Session para SQLAlchemy."""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def actor_autorizado():
    """Usuario autorizado como Cajero."""
    return Usuario(
        id=1,
        empresa_id=100,
        sucursal_id=10,
        rol="CAJERO",
    )


@pytest.fixture
def actor_otra_empresa():
    """Usuario de otra empresa."""
    return Usuario(
        id=2,
        empresa_id=999,
        sucursal_id=99,
        rol="CAJERO",
    )


@pytest.fixture
def detalle_venta():
    """Detalle de venta válido."""
    return SincronizarVentaOfflineDetalleIn(
        producto_variante_id=50,
        cantidad=2,
        precio_unitario=100.0,
        subtotal=200.0,
    )


@pytest.fixture
def venta_offline_valida(detalle_venta):
    """Venta presencial offline válida."""
    return SincronizarVentaOfflineIn(
        uuid="uuid-venta-001",
        tipo_operacion="VENTA_OFFLINE",
        empresa_id=100,
        sucursal_id=10,
        fecha_operacion_local="2026-11-08T12:00:00Z",
        detalles=[detalle_venta],
        metodo_pago="EFECTIVO",
        monto_recibido=250.0,
        total=200.0,
    )


class TestSincronizarVentaOffline:
    """Suite de pruebas para sincronización de ventas offline."""

    def test_venta_valida_se_sincroniza(self, mock_db, actor_autorizado, venta_offline_valida):
        """Caso 1: Venta válida sincroniza exitosamente."""
        service = SincronizarOperacionesPendientesService(mock_db)

        # Mock repo.obtener_venta_por_uuid_origen retorna None (no existe)
        service.repo.obtener_venta_por_uuid_origen = MagicMock(return_value=None)

        # Mock venta_service.crear_venta_directa retorna Venta mock
        venta_mock = MagicMock()
        venta_mock.id = 1001
        venta_mock.codigo_venta = "V-20261108-001"
        venta_mock.total = Decimal("200.00")
        venta_mock.uuid_operacion_offline = None

        service.venta_service.crear_venta_directa = MagicMock(return_value=venta_mock)

        # Mock pago_service.confirmar_pago
        service.pago_service.confirmar_pago = MagicMock(return_value=None)

        resultado = service.sincronizar_venta_offline(actor_autorizado, venta_offline_valida)

        # Debug: imprimir motivo si es rechazada
        if resultado.estado != "CONFIRMADA":
            print(f"\nMotivo de rechazo: {resultado.motivo}")

        assert resultado.estado == "CONFIRMADA", f"Motivo: {resultado.motivo}"
        assert resultado.venta_id == 1001
        assert resultado.codigo_venta == "V-20261108-001"
        assert mock_db.commit.called

    def test_uuid_duplicado_retorna_anterior(self, mock_db, actor_autorizado, venta_offline_valida):
        """Caso 2: UUID duplicado (idempotencia) retorna resultado previo."""
        service = SincronizarOperacionesPendientesService(mock_db)

        # Mock repo.obtener_venta_por_uuid_origen retorna venta existente
        venta_existente = MagicMock()
        venta_existente.id = 2001
        venta_existente.codigo_venta = "V-PREV-001"
        venta_existente.total = Decimal("200.00")

        service.repo.obtener_venta_por_uuid_origen = MagicMock(return_value=venta_existente)
        service.venta_service.crear_venta_directa = MagicMock()

        resultado = service.sincronizar_venta_offline(actor_autorizado, venta_offline_valida)

        assert resultado.estado == "CONFIRMADA"
        assert resultado.venta_id == 2001
        assert resultado.motivo == "Reenvío idempotente (ya procesada)"
        assert not service.venta_service.crear_venta_directa.called

    def test_stock_insuficiente_retorna_conflicto(self, mock_db, actor_autorizado, venta_offline_valida):
        """Caso 3: Stock insuficiente retorna CONFLICTO."""
        service = SincronizarOperacionesPendientesService(mock_db)

        service.repo.obtener_venta_por_uuid_origen = MagicMock(return_value=None)
        service.venta_service.crear_venta_directa = MagicMock(
            side_effect=StockInsuficienteError("Stock insuficiente")
        )

        resultado = service.sincronizar_venta_offline(actor_autorizado, venta_offline_valida)

        assert resultado.estado == "CONFLICTO"
        assert resultado.motivo == "Stock insuficiente en servidor"
        assert mock_db.rollback.called

    def test_empresa_no_autorizada_rechaza(self, mock_db, actor_otra_empresa, venta_offline_valida):
        """Caso 4: Empresa diferente rechaza operación."""
        service = SincronizarOperacionesPendientesService(mock_db)

        resultado = service.sincronizar_venta_offline(actor_otra_empresa, venta_offline_valida)

        assert resultado.estado == "RECHAZADA"
        assert resultado.motivo == "Empresa no autorizada"
        assert mock_db.rollback.called

    def test_sucursal_no_autorizada_rechaza(self, mock_db, actor_autorizado, venta_offline_valida):
        """Caso 5: Sucursal diferente rechaza operación."""
        venta_otra_sucursal = SincronizarVentaOfflineIn(
            uuid="uuid-venta-002",
            tipo_operacion="VENTA_OFFLINE",
            empresa_id=100,
            sucursal_id=999,  # Diferente
            fecha_operacion_local="2026-11-08T12:00:00Z",
            detalles=[SincronizarVentaOfflineDetalleIn(
                producto_variante_id=50,
                cantidad=2,
                precio_unitario=100.0,
                subtotal=200.0,
            )],
            total=200.0,
        )

        service = SincronizarOperacionesPendientesService(mock_db)

        resultado = service.sincronizar_venta_offline(actor_autorizado, venta_otra_sucursal)

        assert resultado.estado == "RECHAZADA"
        assert resultado.motivo == "Sucursal no autorizada"
        assert mock_db.rollback.called

    def test_detalles_vacios_rechaza(self, mock_db, actor_autorizado):
        """Caso 6: Venta sin detalles rechaza."""
        venta_sin_detalles = SincronizarVentaOfflineIn(
            uuid="uuid-venta-003",
            tipo_operacion="VENTA_OFFLINE",
            empresa_id=100,
            sucursal_id=10,
            fecha_operacion_local="2026-11-08T12:00:00Z",
            detalles=[],
            total=0.0,
        )

        service = SincronizarOperacionesPendientesService(mock_db)
        service.repo.obtener_venta_por_uuid_origen = MagicMock(return_value=None)

        resultado = service.sincronizar_venta_offline(actor_autorizado, venta_sin_detalles)

        assert resultado.estado == "RECHAZADA"
        assert resultado.motivo == "Venta sin detalles"

    def test_total_negativo_rechaza(self, mock_db, actor_autorizado, detalle_venta):
        """Caso 7: Total negativo rechaza."""
        venta_negativa = SincronizarVentaOfflineIn(
            uuid="uuid-venta-004",
            tipo_operacion="VENTA_OFFLINE",
            empresa_id=100,
            sucursal_id=10,
            fecha_operacion_local="2026-11-08T12:00:00Z",
            detalles=[detalle_venta],
            total=-100.0,  # Negativo
        )

        service = SincronizarOperacionesPendientesService(mock_db)
        service.repo.obtener_venta_por_uuid_origen = MagicMock(return_value=None)

        resultado = service.sincronizar_venta_offline(actor_autorizado, venta_negativa)

        assert resultado.estado == "RECHAZADA"
        assert resultado.motivo == "Total debe ser positivo"

    def test_transaccion_rollback_en_error(self, mock_db, actor_autorizado, venta_offline_valida):
        """Caso 8: Transacción rollback en error."""
        service = SincronizarOperacionesPendientesService(mock_db)

        service.repo.obtener_venta_por_uuid_origen = MagicMock(return_value=None)
        service.venta_service.crear_venta_directa = MagicMock(
            side_effect=Exception("Error inesperado")
        )

        resultado = service.sincronizar_venta_offline(actor_autorizado, venta_offline_valida)

        assert resultado.estado == "RECHAZADA"
        assert mock_db.rollback.called

    def test_variante_no_encontrada_rechaza(self, mock_db, actor_autorizado, venta_offline_valida):
        """Caso adicional: Variante no encontrada."""
        service = SincronizarOperacionesPendientesService(mock_db)

        service.repo.obtener_venta_por_uuid_origen = MagicMock(return_value=None)
        service.venta_service.crear_venta_directa = MagicMock(
            side_effect=VarianteNoEncontradaError("Variante 999 no existe")
        )

        resultado = service.sincronizar_venta_offline(actor_autorizado, venta_offline_valida)

        assert resultado.estado == "RECHAZADA"
        assert resultado.motivo == "Variante no encontrada"
