"""Servicio para CU15 — Reconciliar inventario después de operaciones offline."""

import logging
import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from .repository import ReconciliacionInventarioRepository
from .schemas import (
    ResultadoReconciliacion,
    ReconciliacionVarianteDetail,
    ConsultaReconciliacionRequest,
)

logger = logging.getLogger(__name__)


class ReconciliarInventarioService:
    """Orquestación de reconciliación de inventario para CU15."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReconciliacionInventarioRepository(db)

    # ============================================================================
    # RECONCILIACIÓN: Venta offline
    # ============================================================================

    def reconciliar_venta_offline(
        self,
        actor: Usuario,
        request: ConsultaReconciliacionRequest,
    ) -> ResultadoReconciliacion:
        """Reconciliar inventario de una venta offline confirmada.

        Flujo:
        1. Validar aislamiento (empresa)
        2. Obtener venta confirmada por UUID
        3. Si no existe, retornar PENDIENTE_REVISION
        4. Obtener detalles de la venta
        5. Para cada variante:
           - Obtener stock actual del servidor
           - Verificar si movimiento fue registrado
           - Calcular impacto esperado vs. real
           - Detectar diferencias
        6. Registrar resultado en auditoría (idempotente por UUID)
        7. Retornar estado de reconciliación
        """

        # 1. VALIDAR AISLAMIENTO
        if request.empresa_id != actor.empresa_id:
            raise PermissionError("Empresa no autorizada")

        if actor.rol not in ["CAJERO", "ADMINISTRADOR"]:
            raise PermissionError(f"Rol {actor.rol} no autorizado para reconciliar")

        # 2. OBTENER VENTA CONFIRMADA
        venta = self.repo.obtener_venta_offline_confirmada(
            request.empresa_id, request.uuid_operacion_offline
        )

        if not venta:
            logger.warning(
                f"[CU15] Venta no encontrada o no confirmada. UUID={request.uuid_operacion_offline}"
            )
            return ResultadoReconciliacion(
                uuid_operacion_offline=request.uuid_operacion_offline,
                tipo_operacion="VENTA_OFFLINE",
                empresa_id=request.empresa_id,
                sucursal_id=request.empresa_id,  # Usar empresa como fallback
                estado_general="PENDIENTE_REVISION",
                detalles=[],
                motivo_inconsistencia="Venta no encontrada en servidor",
                fecha_reconciliacion=datetime.utcnow(),
                idempotencia_verificada=True,
            )

        # 3. OBTENER DETALLES DE VENTA
        detalles_venta = self.repo.obtener_detalles_venta(venta.id)

        if not detalles_venta:
            logger.warning(
                f"[CU15] Venta sin detalles. UUID={request.uuid_operacion_offline}, venta_id={venta.id}"
            )
            return ResultadoReconciliacion(
                uuid_operacion_offline=request.uuid_operacion_offline,
                tipo_operacion="VENTA_OFFLINE",
                empresa_id=request.empresa_id,
                sucursal_id=venta.sucursal_id,
                estado_general="PENDIENTE_REVISION",
                detalles=[],
                motivo_inconsistencia="Venta sin detalles",
                fecha_reconciliacion=datetime.utcnow(),
                idempotencia_verificada=True,
            )

        # 4. ANALIZAR CADA VARIANTE
        detalles_reconciliacion = []
        estado_general = "CONSISTENTE"
        inconsistencias = []

        for detalle in detalles_venta:
            # Obtener stock actual
            stock_info = self.repo.obtener_stock_sucursal(
                venta.sucursal_id, detalle.producto_variante_id
            )

            if not stock_info:
                logger.warning(
                    f"[CU15] Stock no encontrado. sucursal={venta.sucursal_id}, variante={detalle.producto_variante_id}"
                )
                detalles_reconciliacion.append(
                    ReconciliacionVarianteDetail(
                        producto_variante_id=detalle.producto_variante_id,
                        cantidad_operacion=detalle.cantidad,
                        stock_actual=0,
                        stock_esperado=-detalle.cantidad,
                        diferencia=0,
                        estado="PENDIENTE_REVISION",
                    )
                )
                if estado_general == "CONSISTENTE":
                    estado_general = "PENDIENTE_REVISION"
                inconsistencias.append(f"Stock no encontrado para variante {detalle.producto_variante_id}")
                continue

            # Verificar si movimiento fue registrado
            movimiento = self.repo.obtener_movimiento_por_venta(venta.id, detalle.producto_variante_id)

            if not movimiento:
                logger.warning(
                    f"[CU15] Movimiento no registrado. venta={venta.id}, variante={detalle.producto_variante_id}"
                )
                # Stock actual debería ser igual al esperado (sin descuento)
                # Eso es una DIVERGENCIA: la venta se confirmó pero no se descontó stock
                detalles_reconciliacion.append(
                    ReconciliacionVarianteDetail(
                        producto_variante_id=detalle.producto_variante_id,
                        cantidad_operacion=detalle.cantidad,
                        stock_actual=stock_info.cantidad,
                        stock_esperado=stock_info.cantidad - detalle.cantidad,  # Lo que DEBERÍA ser
                        diferencia=detalle.cantidad,  # Falta descontar
                        estado="DIVERGENCIA_DETECTADA",
                    )
                )
                estado_general = "DIVERGENCIA_DETECTADA"
                inconsistencias.append(
                    f"Movimiento NO registrado para variante {detalle.producto_variante_id}, "
                    f"diferencia: {detalle.cantidad} unidades"
                )
            else:
                # Movimiento existe: verificar consistencia
                stock_esperado = movimiento.stock_resultante
                diferencia = stock_info.cantidad - stock_esperado

                if diferencia == 0:
                    detalles_reconciliacion.append(
                        ReconciliacionVarianteDetail(
                            producto_variante_id=detalle.producto_variante_id,
                            cantidad_operacion=detalle.cantidad,
                            stock_actual=stock_info.cantidad,
                            stock_esperado=stock_esperado,
                            diferencia=0,
                            estado="CONSISTENTE",
                        )
                    )
                else:
                    # Stock no coincide con lo esperado
                    detalles_reconciliacion.append(
                        ReconciliacionVarianteDetail(
                            producto_variante_id=detalle.producto_variante_id,
                            cantidad_operacion=detalle.cantidad,
                            stock_actual=stock_info.cantidad,
                            stock_esperado=stock_esperado,
                            diferencia=diferencia,
                            estado="DIVERGENCIA_DETECTADA",
                        )
                    )
                    estado_general = "DIVERGENCIA_DETECTADA"
                    inconsistencias.append(
                        f"Stock inconsistente para variante {detalle.producto_variante_id}: "
                        f"actual={stock_info.cantidad}, esperado={stock_esperado}, diferencia={diferencia}"
                    )

        # 5. REGISTRAR RESULTADO EN AUDITORÍA
        motivo_general = None
        if inconsistencias:
            motivo_general = "; ".join(inconsistencias[:3])  # Máximo 3 razones

        detalles_json = json.dumps(
            [
                {
                    "producto_variante_id": d.producto_variante_id,
                    "cantidad_operacion": d.cantidad_operacion,
                    "stock_actual": d.stock_actual,
                    "stock_esperado": d.stock_esperado,
                    "diferencia": d.diferencia,
                    "estado": d.estado,
                }
                for d in detalles_reconciliacion
            ]
        )

        self.repo.registrar_reconciliacion(
            empresa_id=request.empresa_id,
            sucursal_id=venta.sucursal_id,
            uuid_operacion=request.uuid_operacion_offline,
            tipo_operacion="VENTA_OFFLINE",
            estado_general=estado_general,
            detalles_json=detalles_json,
            motivo=motivo_general,
        )
        self.db.commit()

        logger.info(
            f"[CU15] Reconciliación venta completada. UUID={request.uuid_operacion_offline}, "
            f"estado={estado_general}"
        )

        # 6. RETORNAR RESULTADO
        return ResultadoReconciliacion(
            uuid_operacion_offline=request.uuid_operacion_offline,
            tipo_operacion="VENTA_OFFLINE",
            empresa_id=request.empresa_id,
            sucursal_id=venta.sucursal_id,
            estado_general=estado_general,
            detalles=detalles_reconciliacion,
            motivo_inconsistencia=motivo_general,
            fecha_reconciliacion=datetime.utcnow(),
            idempotencia_verificada=True,
        )

    # ============================================================================
    # RECONCILIACIÓN: Reserva offline
    # ============================================================================

    def reconciliar_reserva_offline(
        self,
        actor: Usuario,
        request: ConsultaReconciliacionRequest,
    ) -> ResultadoReconciliacion:
        """Reconciliar inventario de una reserva offline confirmada."""

        # 1. VALIDAR AISLAMIENTO
        if request.empresa_id != actor.empresa_id:
            raise PermissionError("Empresa no autorizada")

        # 2. OBTENER RESERVA CONFIRMADA
        reserva = self.repo.obtener_reserva_offline_confirmada(
            request.empresa_id, request.uuid_operacion_offline
        )

        if not reserva:
            logger.warning(
                f"[CU15] Reserva no encontrada o no confirmada. UUID={request.uuid_operacion_offline}"
            )
            return ResultadoReconciliacion(
                uuid_operacion_offline=request.uuid_operacion_offline,
                tipo_operacion="RESERVA_OFFLINE",
                empresa_id=request.empresa_id,
                sucursal_id=request.empresa_id,
                estado_general="PENDIENTE_REVISION",
                detalles=[],
                motivo_inconsistencia="Reserva no encontrada en servidor",
                fecha_reconciliacion=datetime.utcnow(),
                idempotencia_verificada=True,
            )

        # 3. OBTENER DETALLES DE RESERVA
        detalles_reserva = self.repo.obtener_detalles_reserva(reserva.id)

        if not detalles_reserva:
            logger.warning(
                f"[CU15] Reserva sin detalles. UUID={request.uuid_operacion_offline}, reserva_id={reserva.id}"
            )
            return ResultadoReconciliacion(
                uuid_operacion_offline=request.uuid_operacion_offline,
                tipo_operacion="RESERVA_OFFLINE",
                empresa_id=request.empresa_id,
                sucursal_id=reserva.sucursal_id,
                estado_general="PENDIENTE_REVISION",
                detalles=[],
                motivo_inconsistencia="Reserva sin detalles",
                fecha_reconciliacion=datetime.utcnow(),
                idempotencia_verificada=True,
            )

        # 4. ANALIZAR CADA VARIANTE (reservas comprometen stock_reservado, no cantidad total)
        detalles_reconciliacion = []
        estado_general = "CONSISTENTE"
        inconsistencias = []

        for detalle in detalles_reserva:
            stock_info = self.repo.obtener_stock_sucursal(
                reserva.sucursal_id, detalle.producto_variante_id
            )

            if not stock_info:
                logger.warning(
                    f"[CU15] Stock no encontrado para reserva. sucursal={reserva.sucursal_id}, variante={detalle.producto_variante_id}"
                )
                detalles_reconciliacion.append(
                    ReconciliacionVarianteDetail(
                        producto_variante_id=detalle.producto_variante_id,
                        cantidad_operacion=detalle.cantidad,
                        stock_actual=0,
                        stock_esperado=0,
                        diferencia=0,
                        estado="PENDIENTE_REVISION",
                    )
                )
                if estado_general == "CONSISTENTE":
                    estado_general = "PENDIENTE_REVISION"
                inconsistencias.append(f"Stock no encontrado para variante {detalle.producto_variante_id}")
                continue

            # Para reservas: verificar stock_reservado
            movimiento = self.repo.obtener_movimiento_por_reserva(reserva.id, detalle.producto_variante_id)

            if not movimiento:
                # Verificar si stock_reservado ya refleja la reserva
                if stock_info.stock_reservado >= detalle.cantidad:
                    # Reserva fue aplicada al stock_reservado
                    detalles_reconciliacion.append(
                        ReconciliacionVarianteDetail(
                            producto_variante_id=detalle.producto_variante_id,
                            cantidad_operacion=detalle.cantidad,
                            stock_actual=stock_info.cantidad,
                            stock_esperado=stock_info.cantidad,
                            diferencia=0,
                            estado="CONSISTENTE",
                        )
                    )
                else:
                    # stock_reservado no refleja la reserva
                    detalles_reconciliacion.append(
                        ReconciliacionVarianteDetail(
                            producto_variante_id=detalle.producto_variante_id,
                            cantidad_operacion=detalle.cantidad,
                            stock_actual=stock_info.stock_reservado,
                            stock_esperado=detalle.cantidad,
                            diferencia=detalle.cantidad - stock_info.stock_reservado,
                            estado="DIVERGENCIA_DETECTADA",
                        )
                    )
                    estado_general = "DIVERGENCIA_DETECTADA"
                    inconsistencias.append(
                        f"stock_reservado inconsistente para variante {detalle.producto_variante_id}: "
                        f"actual={stock_info.stock_reservado}, esperado={detalle.cantidad}"
                    )
            else:
                # Movimiento existe: consistencia ya verificada
                detalles_reconciliacion.append(
                    ReconciliacionVarianteDetail(
                        producto_variante_id=detalle.producto_variante_id,
                        cantidad_operacion=detalle.cantidad,
                        stock_actual=stock_info.cantidad,
                        stock_esperado=stock_info.cantidad,
                        diferencia=0,
                        estado="CONSISTENTE",
                    )
                )

        # 5. REGISTRAR RESULTADO
        motivo_general = None
        if inconsistencias:
            motivo_general = "; ".join(inconsistencias[:3])

        detalles_json = json.dumps(
            [
                {
                    "producto_variante_id": d.producto_variante_id,
                    "cantidad_operacion": d.cantidad_operacion,
                    "stock_actual": d.stock_actual,
                    "stock_esperado": d.stock_esperado,
                    "diferencia": d.diferencia,
                    "estado": d.estado,
                }
                for d in detalles_reconciliacion
            ]
        )

        self.repo.registrar_reconciliacion(
            empresa_id=request.empresa_id,
            sucursal_id=reserva.sucursal_id,
            uuid_operacion=request.uuid_operacion_offline,
            tipo_operacion="RESERVA_OFFLINE",
            estado_general=estado_general,
            detalles_json=detalles_json,
            motivo=motivo_general,
        )
        self.db.commit()

        logger.info(
            f"[CU15] Reconciliación reserva completada. UUID={request.uuid_operacion_offline}, "
            f"estado={estado_general}"
        )

        # 6. RETORNAR RESULTADO
        return ResultadoReconciliacion(
            uuid_operacion_offline=request.uuid_operacion_offline,
            tipo_operacion="RESERVA_OFFLINE",
            empresa_id=request.empresa_id,
            sucursal_id=reserva.sucursal_id,
            estado_general=estado_general,
            detalles=detalles_reconciliacion,
            motivo_inconsistencia=motivo_general,
            fecha_reconciliacion=datetime.utcnow(),
            idempotencia_verificada=True,
        )
