"""Servicio de CU11 — Sincronizar operaciones pendientes.

Garantías críticas:
- Idempotencia: UUID único, sin duplicados
- Atomicidad: Venta + pago + inventario en transacción
- Sin doble cobro: Reutiliza CU24/CU25
- Aislamiento: Valida empresa/sucursal/usuario
"""

import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P5_ComprasVentasYPagos.Models.venta import Venta
from modules.P4_ReservasYAtencion.Models.reserva import Reserva
from modules.P5_ComprasVentasYPagos.CU24_RegistrarVentaPresencial.schemas import (
    CrearVentaDirectaRequest,
    ItemVentaDirectaRequest,
)
from modules.P5_ComprasVentasYPagos.CU24_RegistrarVentaPresencial.service import (
    VentaPresencialService,
    StockInsuficienteError,
    VarianteNoEncontradaError,
)
from modules.P5_ComprasVentasYPagos.CU25_ProcesarPagoPresencial.schemas import (
    ConfirmarPagoEfectivoRequest,
)
from modules.P5_ComprasVentasYPagos.CU25_ProcesarPagoPresencial.service import (
    PagoPresencialService,
)

from modules.P4_ReservasYAtencion.CU17_CrearReservaPrendas.service import (
    CrearReservaService,
)
from modules.P4_ReservasYAtencion.CU17_CrearReservaPrendas.schemas import CrearReservaRequest

from .repository import RegistroSincronizacionRepository
from .schemas import (
    ResultadoSincronizacionVenta,
    ResultadoSincronizacionReserva,
    SincronizarVentaOfflineIn,
    SincronizarReservaOfflineIn,
)


class ValidacionError(Exception):
    """Datos incompletos o inválidos."""
    pass


class SincronizarOperacionesPendientesService:
    """Orquesta sincronización de operaciones offline a PostgreSQL."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = RegistroSincronizacionRepository(db)
        self.venta_service = VentaPresencialService(db)
        self.pago_service = PagoPresencialService(db)
        self.reserva_service = CrearReservaService(db)

    def sincronizar_venta_offline(
        self,
        actor: Usuario,
        operacion: SincronizarVentaOfflineIn,
    ) -> ResultadoSincronizacionVenta:
        """Sincronizar venta presencial offline.

        1. Validar aislamiento (empresa/sucursal/usuario)
        2. Verificar idempotencia (UUID único)
        3. Validar estructura de detalles
        4. Crear venta con CU24 (valida stock)
        5. Procesar pago con CU25 (descuenta inventario)
        6. Retornar resultado
        """

        try:
            # 1. VALIDAR AISLAMIENTO
            if operacion.empresa_id != actor.empresa_id:
                raise ValidacionError("Empresa no autorizada")

            if actor.sucursal_id and operacion.sucursal_id != actor.sucursal_id:
                raise ValidacionError("Sucursal no autorizada")

            # 2. VERIFICAR IDEMPOTENCIA
            venta_existente = self.repo.obtener_venta_por_uuid_origen(
                operacion.empresa_id,
                operacion.uuid,
            )
            if venta_existente:
                # Venta ya sincronizada: retornar resultado previo
                return ResultadoSincronizacionVenta(
                    uuid_local=operacion.uuid,
                    venta_id=venta_existente.id,
                    codigo_venta=venta_existente.codigo_venta,
                    estado="CONFIRMADA",
                    motivo="Reenvío idempotente (ya procesada)",
                    total=float(venta_existente.total) if venta_existente.total else None,
                )

            # 3. VALIDAR ESTRUCTURA
            if not operacion.detalles or len(operacion.detalles) == 0:
                raise ValidacionError("Venta sin detalles")

            if operacion.total <= 0:
                raise ValidacionError("Total debe ser positivo")

            # 4. CREAR VENTA CON CU24 (REUTILIZA VALIDACIONES DE STOCK)
            items = [
                ItemVentaDirectaRequest(
                    producto_variante_id=d.producto_variante_id,
                    cantidad=d.cantidad,
                )
                for d in operacion.detalles
            ]

            crear_venta_request = CrearVentaDirectaRequest(items=items)
            venta_creada_schema = self.venta_service.crear_venta_directa(actor, crear_venta_request)

            # Obtener modelo de venta desde BD para actualizarlo con UUID
            venta_modelo = self.db.query(Venta).filter_by(id=venta_creada_schema.id).first()
            if venta_modelo:
                venta_modelo.uuid_operacion_offline = operacion.uuid

            # 5. PROCESAR PAGO CON CU25 (DESCUENTA INVENTARIO ATÓMICAMENTE)
            # IMPORTANTE: usar venta_creada_schema.total calculado por CU24, NO operacion.total de la request
            pago_request = ConfirmarPagoEfectivoRequest(
                metodo_pago="EFECTIVO",
                monto_recibido=float(operacion.monto_recibido or venta_creada_schema.total),
            )

            self.pago_service.confirmar_pago(actor, venta_creada_schema.id, pago_request)

            # 6. PERSISTIR TRANSACCIONALMENTE
            self.db.commit()

            return ResultadoSincronizacionVenta(
                uuid_local=operacion.uuid,
                venta_id=venta_creada_schema.id,
                codigo_venta=venta_creada_schema.codigo_venta,
                estado="CONFIRMADA",
                motivo=None,
                total=float(venta_creada_schema.total),
            )

        except ValidacionError as e:
            self.db.rollback()
            return ResultadoSincronizacionVenta(
                uuid_local=operacion.uuid,
                venta_id=None,
                codigo_venta=None,
                estado="RECHAZADA",
                motivo=str(e),
            )

        except StockInsuficienteError:
            self.db.rollback()
            return ResultadoSincronizacionVenta(
                uuid_local=operacion.uuid,
                venta_id=None,
                codigo_venta=None,
                estado="CONFLICTO",
                motivo="Stock insuficiente en servidor",
            )

        except VarianteNoEncontradaError:
            self.db.rollback()
            return ResultadoSincronizacionVenta(
                uuid_local=operacion.uuid,
                venta_id=None,
                codigo_venta=None,
                estado="RECHAZADA",
                motivo="Variante no encontrada",
            )

        except Exception as e:
            self.db.rollback()
            logger.exception("[CU11 VENTA] Excepción no manejada. UUID: %s, Error: %s", operacion.uuid, str(e))
            return ResultadoSincronizacionVenta(
                uuid_local=operacion.uuid,
                venta_id=None,
                codigo_venta=None,
                estado="RECHAZADA",
                motivo=str(e)[:100],
            )

    def sincronizar_reserva_offline(
        self,
        actor: Usuario,
        operacion: SincronizarReservaOfflineIn,
    ) -> ResultadoSincronizacionReserva:
        """Sincronizar reserva offline.

        1. Validar aislamiento (empresa/sucursal/cliente del actor)
        2. Verificar idempotencia (UUID único)
        3. Validar estructura de detalles
        4. Crear reserva con CU17 (valida stock y disponibilidad)
        5. Retornar resultado
        """

        try:
            # 1. VALIDAR AISLAMIENTO
            if operacion.empresa_id != actor.empresa_id:
                raise ValidacionError("Empresa no autorizada")

            if actor.sucursal_id and operacion.sucursal_id != actor.sucursal_id:
                raise ValidacionError("Sucursal no autorizada")

            if operacion.cliente_id != actor.id:
                raise ValidacionError("Cliente no autorizado (mismatch con actor)")

            # 2. VERIFICAR IDEMPOTENCIA
            reserva_existente = self.repo.obtener_reserva_por_uuid_origen(
                operacion.empresa_id,
                operacion.uuid,
            )
            if reserva_existente:
                return ResultadoSincronizacionReserva(
                    uuid_local=operacion.uuid,
                    reserva_id=reserva_existente.id,
                    codigo_reserva=getattr(reserva_existente, 'codigo_reserva', None),
                    estado="CONFIRMADA",
                    motivo="Reenvío idempotente (ya procesada)",
                )

            # 3. VALIDAR ESTRUCTURA
            if not operacion.detalles or len(operacion.detalles) == 0:
                raise ValidacionError("Reserva sin detalles")

            # 4. CREAR RESERVA CON CU17 (valida stock y disponibilidad)
            # Para crear reserva, necesito parsear fecha_reserva y hora_inicio
            from datetime import datetime, date, time

            fecha_parts = operacion.fecha_reserva.split("-")
            fecha_reserva = date(int(fecha_parts[0]), int(fecha_parts[1]), int(fecha_parts[2]))

            hora_parts = operacion.hora_inicio.split(":")
            hora_inicio = time(int(hora_parts[0]), int(hora_parts[1]))

            # CU17 solo permite UN detalle por request, pero creamos con el primero
            # Futuro: extender CU17 para múltiples detalles en una reserva
            if len(operacion.detalles) > 1:
                raise ValidacionError("CU11 solo soporta sincronización de 1 detalle por reserva (limitación CU17)")

            detalle = operacion.detalles[0]
            crear_request = CrearReservaRequest(
                producto_variante_id=detalle.producto_variante_id,
                sucursal_id=operacion.sucursal_id,
                cantidad=detalle.cantidad,
                fecha_reserva=fecha_reserva,
                hora_inicio=hora_inicio,
            )

            # Crear reserva usando el cliente como actor de CU17
            usuario_cliente = Usuario(
                id=operacion.cliente_id,
                empresa_id=operacion.empresa_id,
                sucursal_id=operacion.sucursal_id,
                rol="CLIENTE",
            )

            reserva_creada_schema = self.reserva_service.crear(usuario_cliente, crear_request)

            # Obtener modelo de reserva desde BD para actualizarlo con UUID
            reserva_modelo = self.db.query(Reserva).filter_by(id=reserva_creada_schema.id).first()
            if reserva_modelo:
                reserva_modelo.uuid_operacion_offline = operacion.uuid

            # 5. PERSISTIR TRANSACCIONALMENTE
            self.db.commit()

            return ResultadoSincronizacionReserva(
                uuid_local=operacion.uuid,
                reserva_id=reserva_creada_schema.id,
                codigo_reserva=getattr(reserva_creada_schema, 'codigo_reserva', f"RES-{operacion.uuid[:8]}"),
                estado="CONFIRMADA",
                motivo=None,
            )

        except ValidacionError as e:
            self.db.rollback()
            return ResultadoSincronizacionReserva(
                uuid_local=operacion.uuid,
                reserva_id=None,
                codigo_reserva=None,
                estado="RECHAZADA",
                motivo=str(e),
            )

        except Exception as e:
            self.db.rollback()
            logger.exception("[CU11 RESERVA] Excepción no manejada. UUID: %s, Error: %s", operacion.uuid, str(e))
            return ResultadoSincronizacionReserva(
                uuid_local=operacion.uuid,
                reserva_id=None,
                codigo_reserva=None,
                estado="RECHAZADA",
                motivo=str(e)[:100],
            )
