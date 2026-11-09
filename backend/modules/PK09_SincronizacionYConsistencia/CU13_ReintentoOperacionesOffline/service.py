"""Servicio para CU13 — Reintentar sincronización fallida."""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.PK09_SincronizacionYConsistencia.CU11_SincronizarOperacionesPendientes.service import (
    SincronizarOperacionesPendientesService,
)
from modules.PK09_SincronizacionYConsistencia.CU12_ConsultarResultadoSincronizacion.service import (
    ConsultarResultadoService,
)

from .repository import ReintentoRepository
from .schemas import (
    ReintentoRequest,
    ReintentoResultado,
    OperacionFallidaSummary,
    ResumenOperacionesFallidas,
    BackoffConfig,
)

logger = logging.getLogger(__name__)


class ReintentoService:
    """Orquestación de reintentos para CU13."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReintentoRepository(db)
        self.sincronizar_service = SincronizarOperacionesPendientesService(db)
        self.consultar_service = ConsultarResultadoService(db)
        self.backoff_config = BackoffConfig()

    # ============================================================================
    # REINTENTOS: Venta
    # ============================================================================

    def reintentar_venta(
        self,
        actor: Usuario,
        uuid_operacion: str,
        request: ReintentoRequest,
    ) -> ReintentoResultado:
        """Reintentar sincronización de una venta fallida.

        Flujo:
        1. Validar aislamiento
        2. Verificar elegibilidad (intentos < max, backoff respetado)
        3. Consultar CU12 para confirmar si ya fue sincronizada
        4. Llamar CU11 para reintentar
        5. Registrar en auditoría
        6. Retornar resultado
        """

        # 1. VALIDAR AISLAMIENTO
        if request.empresa_id != actor.empresa_id:
            raise PermissionError("Empresa no autorizada")

        # Solo CAJERO/ADMINISTRADOR pueden reintentar ventas
        if actor.rol not in ["CAJERO", "ADMINISTRADOR"]:
            raise PermissionError(f"Rol {actor.rol} no autorizado para reintentar ventas")

        # 2. VERIFICAR ELEGIBILIDAD
        historial = self.repo.obtener_historial_intento(request.empresa_id, uuid_operacion)
        numero_intento = len(historial) + 1

        if numero_intento > self.backoff_config.max_intentos:
            logger.warning(
                f"[CU13] Reintento rechazado: max intentos alcanzado. UUID={uuid_operacion}, intentos={numero_intento}"
            )
            return ReintentoResultado(
                uuid_local=uuid_operacion,
                tipo_operacion="VENTA_OFFLINE",
                estado="RECHAZADA",
                motivo=f"Máximo de reintentos alcanzado ({self.backoff_config.max_intentos})",
                numero_intento=numero_intento,
                proximo_reintento_en_ms=0,
            )

        # Validar backoff
        if historial:
            ultimo = historial[-1]
            espera_requerida_ms = self.backoff_config.obtener_espera_ms(len(historial))
            tiempo_transcurrido_ms = int((datetime.utcnow() - ultimo.fecha_intento).total_seconds() * 1000)

            if tiempo_transcurrido_ms < espera_requerida_ms:
                ms_falta = espera_requerida_ms - tiempo_transcurrido_ms
                logger.info(f"[CU13] Reintento no elegible aún. UUID={uuid_operacion}, esperar {ms_falta}ms")
                return ReintentoResultado(
                    uuid_local=uuid_operacion,
                    tipo_operacion="VENTA_OFFLINE",
                    estado="RECHAZADA",
                    motivo=f"Reintento disponible en {ms_falta}ms",
                    numero_intento=numero_intento,
                    proximo_reintento_en_ms=ms_falta,
                )

        # 3. CONSULTAR CU12: ¿Ya fue sincronizada?
        resultado_anterior = self.consultar_service.consultar_resultado_venta(actor, uuid_operacion)
        if resultado_anterior and resultado_anterior.estado == "CONFIRMADA":
            logger.info(f"[CU13] Venta ya sincronizada. UUID={uuid_operacion}, venta_id={resultado_anterior.venta_id}")
            return ReintentoResultado(
                uuid_local=uuid_operacion,
                tipo_operacion="VENTA_OFFLINE",
                estado="CONFIRMADA",
                motivo="Ya fue sincronizada en intento anterior",
                venta_id=resultado_anterior.venta_id,
                codigo_venta=resultado_anterior.codigo_venta,
                numero_intento=numero_intento,
                proximo_reintento_en_ms=0,
            )

        # 4. LLAMAR CU11: Reintentar sincronización
        from modules.PK09_SincronizacionYConsistencia.CU11_SincronizarOperacionesPendientes.schemas import (
            SincronizarVentaOfflineIn,
            SincronizarVentaOfflineDetalleIn,
        )

        venta = self.repo.obtener_venta_por_uuid(request.empresa_id, uuid_operacion)
        if not venta:
            logger.error(f"[CU13] Venta no encontrada por UUID. UUID={uuid_operacion}")
            return ReintentoResultado(
                uuid_local=uuid_operacion,
                tipo_operacion="VENTA_OFFLINE",
                estado="RECHAZADA",
                motivo="Venta no encontrada en el servidor",
                numero_intento=numero_intento,
                proximo_reintento_en_ms=0,
            )

        # Obtener detalles de venta local (del repositorio)
        from modules.PK09_SincronizacionYConsistencia.CU11_SincronizarOperacionesPendientes.repository import (
            RegistroSincronizacionRepository,
        )
        repo_cu11 = RegistroSincronizacionRepository(self.db)
        detalles_locales = repo_cu11.obtener_detalles_venta_offline(uuid_operacion)

        # Construir request para CU11
        detalles = [
            SincronizarVentaOfflineDetalleIn(
                producto_variante_id=d.producto_variante_id,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                subtotal=d.subtotal,
            )
            for d in detalles_locales
        ]

        operacion_venta = SincronizarVentaOfflineIn(
            uuid=uuid_operacion,
            tipo_operacion="VENTA_OFFLINE",
            empresa_id=request.empresa_id,
            sucursal_id=venta.sucursal_id,
            fecha_operacion_local=venta.fecha_creacion.isoformat(),
            detalles=detalles,
            total=float(venta.total),
        )

        # Llamar CU11
        resultado_cu11 = self.sincronizar_service.sincronizar_venta_offline(actor, operacion_venta)

        # 5. REGISTRAR EN AUDITORÍA
        self.repo.registrar_intento(
            empresa_id=request.empresa_id,
            uuid_operacion=uuid_operacion,
            tipo_operacion="VENTA_OFFLINE",
            numero_intento=numero_intento,
            estado_resultado=resultado_cu11.estado,
            motivo=resultado_cu11.motivo,
            usuario_id=actor.id,
        )
        self.db.commit()

        # 6. RETORNAR RESULTADO
        proximo_reintento_ms = 0
        # Solo RECHAZADA (error técnico recuperable) se reintenta
        # CONFLICTO (error de negocio) NO se reintenta, requiere intervención
        if resultado_cu11.estado == "RECHAZADA":
            proximo_reintento_ms = self.backoff_config.obtener_espera_ms(numero_intento)

        logger.info(
            f"[CU13] Reintento venta completado. UUID={uuid_operacion}, "
            f"intento={numero_intento}, estado={resultado_cu11.estado}"
        )

        return ReintentoResultado(
            uuid_local=uuid_operacion,
            tipo_operacion="VENTA_OFFLINE",
            estado=resultado_cu11.estado,
            motivo=resultado_cu11.motivo,
            venta_id=resultado_cu11.venta_id,
            codigo_venta=resultado_cu11.codigo_venta,
            total=resultado_cu11.total,
            numero_intento=numero_intento,
            proximo_reintento_en_ms=proximo_reintento_ms,
        )

    # ============================================================================
    # REINTENTOS: Reserva
    # ============================================================================

    def reintentar_reserva(
        self,
        actor: Usuario,
        uuid_operacion: str,
        request: ReintentoRequest,
    ) -> ReintentoResultado:
        """Reintentar sincronización de una reserva fallida."""

        # 1. VALIDAR AISLAMIENTO
        if request.empresa_id != actor.empresa_id:
            raise PermissionError("Empresa no autorizada")

        # CLIENTE solo puede reintentar reservas propias
        # CAJERO/ADMINISTRADOR pueden reintentar cualquiera

        # 2. VERIFICAR ELEGIBILIDAD
        historial = self.repo.obtener_historial_intento(request.empresa_id, uuid_operacion)
        numero_intento = len(historial) + 1

        if numero_intento > self.backoff_config.max_intentos:
            logger.warning(
                f"[CU13] Reintento rechazado: max intentos alcanzado. UUID={uuid_operacion}, intentos={numero_intento}"
            )
            return ReintentoResultado(
                uuid_local=uuid_operacion,
                tipo_operacion="RESERVA_OFFLINE",
                estado="RECHAZADA",
                motivo=f"Máximo de reintentos alcanzado ({self.backoff_config.max_intentos})",
                numero_intento=numero_intento,
                proximo_reintento_en_ms=0,
            )

        # Validar backoff
        if historial:
            ultimo = historial[-1]
            espera_requerida_ms = self.backoff_config.obtener_espera_ms(len(historial))
            tiempo_transcurrido_ms = int((datetime.utcnow() - ultimo.fecha_intento).total_seconds() * 1000)

            if tiempo_transcurrido_ms < espera_requerida_ms:
                ms_falta = espera_requerida_ms - tiempo_transcurrido_ms
                return ReintentoResultado(
                    uuid_local=uuid_operacion,
                    tipo_operacion="RESERVA_OFFLINE",
                    estado="RECHAZADA",
                    motivo=f"Reintento disponible en {ms_falta}ms",
                    numero_intento=numero_intento,
                    proximo_reintento_en_ms=ms_falta,
                )

        # 3. CONSULTAR CU12: ¿Ya fue sincronizada?
        resultado_anterior = self.consultar_service.consultar_resultado_reserva(actor, uuid_operacion)
        if resultado_anterior and resultado_anterior.estado == "CONFIRMADA":
            logger.info(f"[CU13] Reserva ya sincronizada. UUID={uuid_operacion}, reserva_id={resultado_anterior.reserva_id}")
            return ReintentoResultado(
                uuid_local=uuid_operacion,
                tipo_operacion="RESERVA_OFFLINE",
                estado="CONFIRMADA",
                motivo="Ya fue sincronizada en intento anterior",
                reserva_id=resultado_anterior.reserva_id,
                codigo_reserva=resultado_anterior.codigo_reserva,
                numero_intento=numero_intento,
                proximo_reintento_en_ms=0,
            )

        # 4. LLAMAR CU11: Reintentar sincronización
        from modules.PK09_SincronizacionYConsistencia.CU11_SincronizarOperacionesPendientes.schemas import (
            SincronizarReservaOfflineIn,
            SincronizarReservaOfflineDetalleIn,
        )

        reserva = self.repo.obtener_reserva_por_uuid(request.empresa_id, uuid_operacion)
        if not reserva:
            logger.error(f"[CU13] Reserva no encontrada por UUID. UUID={uuid_operacion}")
            return ReintentoResultado(
                uuid_local=uuid_operacion,
                tipo_operacion="RESERVA_OFFLINE",
                estado="RECHAZADA",
                motivo="Reserva no encontrada en el servidor",
                numero_intento=numero_intento,
                proximo_reintento_en_ms=0,
            )

        # Validar si CLIENTE es propietario
        if actor.rol == "CLIENTE" and reserva.cliente_id != actor.id:
            raise PermissionError("No está autorizado para reintentar esta reserva")

        # Obtener detalles
        from modules.PK09_SincronizacionYConsistencia.CU11_SincronizarOperacionesPendientes.repository import (
            RegistroSincronizacionRepository,
        )
        repo_cu11 = RegistroSincronizacionRepository(self.db)
        detalles_locales = repo_cu11.obtener_detalles_reserva_offline(uuid_operacion)

        detalles = [
            SincronizarReservaOfflineDetalleIn(
                producto_variante_id=d.producto_variante_id,
                cantidad=d.cantidad,
            )
            for d in detalles_locales
        ]

        operacion_reserva = SincronizarReservaOfflineIn(
            uuid=uuid_operacion,
            tipo_operacion="RESERVA_OFFLINE",
            empresa_id=request.empresa_id,
            sucursal_id=reserva.sucursal_id,
            cliente_id=reserva.cliente_id,
            fecha_reserva=reserva.fecha_reserva.isoformat(),
            hora_inicio=reserva.hora_inicio.isoformat(),
            detalles=detalles,
        )

        # Llamar CU11
        resultado_cu11 = self.sincronizar_service.sincronizar_reserva_offline(actor, operacion_reserva)

        # 5. REGISTRAR EN AUDITORÍA
        self.repo.registrar_intento(
            empresa_id=request.empresa_id,
            uuid_operacion=uuid_operacion,
            tipo_operacion="RESERVA_OFFLINE",
            numero_intento=numero_intento,
            estado_resultado=resultado_cu11.estado,
            motivo=resultado_cu11.motivo,
            usuario_id=actor.id,
        )
        self.db.commit()

        # 6. RETORNAR RESULTADO
        proximo_reintento_ms = 0
        # Solo RECHAZADA (error técnico recuperable) se reintenta
        # CONFLICTO (error de negocio) NO se reintenta, requiere intervención
        if resultado_cu11.estado == "RECHAZADA":
            proximo_reintento_ms = self.backoff_config.obtener_espera_ms(numero_intento)

        logger.info(
            f"[CU13] Reintento reserva completado. UUID={uuid_operacion}, "
            f"intento={numero_intento}, estado={resultado_cu11.estado}"
        )

        return ReintentoResultado(
            uuid_local=uuid_operacion,
            tipo_operacion="RESERVA_OFFLINE",
            estado=resultado_cu11.estado,
            motivo=resultado_cu11.motivo,
            reserva_id=resultado_cu11.reserva_id,
            codigo_reserva=resultado_cu11.codigo_reserva,
            numero_intento=numero_intento,
            proximo_reintento_en_ms=proximo_reintento_ms,
        )
