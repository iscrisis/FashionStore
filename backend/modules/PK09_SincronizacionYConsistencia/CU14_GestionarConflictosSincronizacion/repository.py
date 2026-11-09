"""Repository para CU14 — Gestionar conflictos de sincronización."""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from modules.Models.conflicto_sincronizacion import ConflictoSincronizacion


class ConflictoRepository:
    """Acceso a datos de conflictos."""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================================
    # REGISTRO DE CONFLICTOS
    # ============================================================================

    def registrar_conflicto(
        self,
        empresa_id: int,
        uuid_operacion: str,
        tipo_operacion: str,
        tipo_conflicto: str,
        motivo: str,
        detalles_conflicto: dict | None = None,
        usuario_id: int | None = None,
    ) -> ConflictoSincronizacion:
        """Registrar un conflicto detectado durante la sincronización."""

        conflicto_existente = self.db.query(ConflictoSincronizacion).filter(
            and_(
                ConflictoSincronizacion.empresa_id == empresa_id,
                ConflictoSincronizacion.uuid_operacion_offline == uuid_operacion,
                ConflictoSincronizacion.estado_conflicto.in_(["DETECTADO", "PENDIENTE_MANUAL"]),
            )
        ).first()

        if conflicto_existente:
            # Actualizar conflicto existente
            conflicto_existente.tipo_conflicto = tipo_conflicto
            conflicto_existente.motivo = motivo
            conflicto_existente.detalles_conflicto = json.dumps(detalles_conflicto) if detalles_conflicto else None
            conflicto_existente.fecha_detectado = datetime.utcnow()
            return conflicto_existente

        # Crear nuevo conflicto
        conflicto = ConflictoSincronizacion(
            empresa_id=empresa_id,
            uuid_operacion_offline=uuid_operacion,
            tipo_operacion=tipo_operacion,
            tipo_conflicto=tipo_conflicto,
            motivo=motivo,
            detalles_conflicto=json.dumps(detalles_conflicto) if detalles_conflicto else None,
            estado_conflicto="DETECTADO",
            usuario_id=usuario_id,
            debe_reintentarse_automaticamente=False,
        )

        self.db.add(conflicto)
        return conflicto

    # ============================================================================
    # CONSULTA DE CONFLICTOS
    # ============================================================================

    def obtener_conflicto_por_uuid(
        self, empresa_id: int, uuid_operacion: str
    ) -> ConflictoSincronizacion | None:
        """Obtener conflicto por UUID de operación."""

        return self.db.query(ConflictoSincronizacion).filter(
            and_(
                ConflictoSincronizacion.empresa_id == empresa_id,
                ConflictoSincronizacion.uuid_operacion_offline == uuid_operacion,
            )
        ).first()

    def obtener_conflictos_sin_resolver(
        self, empresa_id: int, limit: int = 100
    ) -> list[ConflictoSincronizacion]:
        """Obtener conflictos sin resolver (DETECTADO o PENDIENTE_MANUAL)."""

        return self.db.query(ConflictoSincronizacion).filter(
            and_(
                ConflictoSincronizacion.empresa_id == empresa_id,
                ConflictoSincronizacion.estado_conflicto.in_(["DETECTADO", "PENDIENTE_MANUAL"]),
            )
        ).order_by(ConflictoSincronizacion.fecha_detectado.desc()).limit(limit).all()

    def obtener_conflictos_por_tipo(
        self, empresa_id: int, tipo_conflicto: str, limit: int = 100
    ) -> list[ConflictoSincronizacion]:
        """Obtener conflictos de un tipo específico."""

        return self.db.query(ConflictoSincronizacion).filter(
            and_(
                ConflictoSincronizacion.empresa_id == empresa_id,
                ConflictoSincronizacion.tipo_conflicto == tipo_conflicto,
            )
        ).order_by(ConflictoSincronizacion.fecha_detectado.desc()).limit(limit).all()

    def contar_conflictos_sin_resolver(self, empresa_id: int) -> int:
        """Contar conflictos sin resolver."""

        return self.db.query(ConflictoSincronizacion).filter(
            and_(
                ConflictoSincronizacion.empresa_id == empresa_id,
                ConflictoSincronizacion.estado_conflicto.in_(["DETECTADO", "PENDIENTE_MANUAL"]),
            )
        ).count()

    # ============================================================================
    # RESOLUCIÓN DE CONFLICTOS
    # ============================================================================

    def resolver_conflicto(
        self, conflicto_id: int, estado_resolucion: str, usuario_resolucion_id: int | None = None
    ) -> ConflictoSincronizacion:
        """Resolver un conflicto (RESUELTO, DESCARTADO, etc.)."""

        conflicto = self.db.query(ConflictoSincronizacion).filter_by(id=conflicto_id).first()

        if conflicto:
            conflicto.estado_conflicto = estado_resolucion
            conflicto.fecha_resolucion = datetime.utcnow()
            conflicto.usuario_resolucion_id = usuario_resolucion_id

        return conflicto

    def marcar_para_reintentar(self, conflicto_id: int) -> ConflictoSincronizacion:
        """Marcar conflicto para reintentar automáticamente."""

        conflicto = self.db.query(ConflictoSincronizacion).filter_by(id=conflicto_id).first()

        if conflicto:
            conflicto.debe_reintentarse_automaticamente = True
            conflicto.estado_conflicto = "PENDIENTE_MANUAL"

        return conflicto
