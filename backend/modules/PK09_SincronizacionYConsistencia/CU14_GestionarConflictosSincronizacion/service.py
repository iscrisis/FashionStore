"""Servicio para CU14 — Gestionar conflictos de sincronización.

Responsabilidad exclusiva:
- Detectar conflictos informados por CU11
- Registrar conflictos para auditoría y resolución
- Mantener trazabilidad del UUID original
- Prevenir reintentos indefinidos de conflictos
- Permitir consulta y resolución manual
"""

import logging
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.PK09_SincronizacionYConsistencia.CU11_SincronizarOperacionesPendientes.schemas import (
    ResultadoSincronizacionVenta,
    ResultadoSincronizacionReserva,
)

from .repository import ConflictoRepository
from .schemas import (
    ConflictoDetectadoSchema,
    ConflictoRegistroSchema,
    ConflictoConsultaSchema,
    ListaConflictosSchema,
    ResolverConflictoRequest,
    ResolverConflictoResponse,
)

logger = logging.getLogger(__name__)


class GestionarConflictosService:
    """Orquestación de detección y gestión de conflictos de sincronización."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ConflictoRepository(db)

    # ============================================================================
    # DETECCIÓN AUTOMÁTICA DE CONFLICTOS
    # ============================================================================

    def registrar_conflicto_desde_resultado_cu11(
        self,
        actor: Usuario,
        resultado: ResultadoSincronizacionVenta | ResultadoSincronizacionReserva,
    ) -> ConflictoRegistroSchema | None:
        """Detectar y registrar un conflicto desde el resultado de CU11.

        Solo registra si el resultado es CONFLICTO.
        Si es RECHAZADA o CONFIRMADA, retorna None (no hay conflicto a registrar).
        """

        if resultado.estado != "CONFLICTO":
            return None

        # Determinar tipo de operación
        tipo_operacion = (
            "VENTA_OFFLINE"
            if hasattr(resultado, "venta_id")
            else "RESERVA_OFFLINE"
        )

        # Clasificar tipo de conflicto según el motivo
        tipo_conflicto = self._clasificar_conflicto(resultado.motivo)

        logger.info(
            f"[CU14] Conflicto detectado. UUID={resultado.uuid_local}, "
            f"tipo={tipo_conflicto}, motivo={resultado.motivo}"
        )

        # Registrar conflicto
        conflicto = self.repo.registrar_conflicto(
            empresa_id=actor.empresa_id,
            uuid_operacion=resultado.uuid_local,
            tipo_operacion=tipo_operacion,
            tipo_conflicto=tipo_conflicto,
            motivo=resultado.motivo or "Conflicto sin motivo especificado",
            usuario_id=actor.id,
        )

        self.db.commit()

        return ConflictoRegistroSchema(
            id=conflicto.id,
            uuid_operacion_offline=conflicto.uuid_operacion_offline,
            tipo_conflicto=conflicto.tipo_conflicto,
            estado_conflicto=conflicto.estado_conflicto,
            fecha_detectado=conflicto.fecha_detectado,
            debe_reintentarse_automaticamente=conflicto.debe_reintentarse_automaticamente,
        )

    @staticmethod
    def _clasificar_conflicto(motivo: str | None) -> str:
        """Clasificar el tipo de conflicto según el motivo."""

        if not motivo:
            return "OTROS"

        motivo_lower = motivo.lower()

        if "stock" in motivo_lower or "insuficiente" in motivo_lower:
            return "STOCK_INSUFICIENTE"

        if "variante" in motivo_lower or "disponible" in motivo_lower:
            return "VARIANTE_NO_DISPONIBLE"

        if "inconsistencia" in motivo_lower or "mismatch" in motivo_lower:
            return "INCONSISTENCIA_DATOS"

        return "OTROS"

    # ============================================================================
    # CONSULTA DE CONFLICTOS
    # ============================================================================

    def obtener_conflictos_sin_resolver(
        self, actor: Usuario, limit: int = 100
    ) -> ListaConflictosSchema:
        """Obtener conflictos sin resolver de la empresa del usuario."""

        # Validar que el usuario es de la empresa
        conflictos = self.repo.obtener_conflictos_sin_resolver(actor.empresa_id, limit)

        conflictos_schema = [
            ConflictoConsultaSchema(
                id=c.id,
                uuid_operacion_offline=c.uuid_operacion_offline,
                tipo_operacion=c.tipo_operacion,
                tipo_conflicto=c.tipo_conflicto,
                motivo=c.motivo,
                detalles_conflicto=c.detalles_conflicto,
                estado_conflicto=c.estado_conflicto,
                fecha_detectado=c.fecha_detectado,
                usuario_id=c.usuario_id,
                debe_reintentarse_automaticamente=c.debe_reintentarse_automaticamente,
            )
            for c in conflictos
        ]

        return ListaConflictosSchema(
            total=len(conflictos_schema),
            conflictos=conflictos_schema,
        )

    def obtener_conflicto_por_uuid(
        self, actor: Usuario, uuid_operacion: str
    ) -> ConflictoConsultaSchema | None:
        """Obtener un conflicto específico por UUID."""

        conflicto = self.repo.obtener_conflicto_por_uuid(actor.empresa_id, uuid_operacion)

        if not conflicto:
            return None

        return ConflictoConsultaSchema(
            id=conflicto.id,
            uuid_operacion_offline=conflicto.uuid_operacion_offline,
            tipo_operacion=conflicto.tipo_operacion,
            tipo_conflicto=conflicto.tipo_conflicto,
            motivo=conflicto.motivo,
            detalles_conflicto=conflicto.detalles_conflicto,
            estado_conflicto=conflicto.estado_conflicto,
            fecha_detectado=conflicto.fecha_detectado,
            usuario_id=conflicto.usuario_id,
            debe_reintentarse_automaticamente=conflicto.debe_reintentarse_automaticamente,
        )

    # ============================================================================
    # RESOLUCIÓN DE CONFLICTOS
    # ============================================================================

    def resolver_conflicto(
        self,
        actor: Usuario,
        conflicto_id: int,
        request: ResolverConflictoRequest,
    ) -> ResolverConflictoResponse:
        """Resolver un conflicto (descartar, marcar para reintentar, etc.)."""

        # Obtener conflicto
        conflicto = self.db.query(self.repo.db.query).filter_by(
            id=conflicto_id, empresa_id=actor.empresa_id
        ).first()

        if not conflicto:
            raise ValueError("Conflicto no encontrado")

        # Determinar estado según acción
        estado_resolucion = "RESUELTO" if request.accion == "DESCARTAR" else "PENDIENTE_MANUAL"

        # Resolver conflicto
        conflicto_actualizado = self.repo.resolver_conflicto(
            conflicto_id, estado_resolucion, actor.id
        )

        if request.accion == "REINTENTAR_MANUAL":
            self.repo.marcar_para_reintentar(conflicto_id)

        self.db.commit()

        logger.info(
            f"[CU14] Conflicto resuelto. ID={conflicto_id}, acción={request.accion}, usuario={actor.id}"
        )

        return ResolverConflictoResponse(
            id=conflicto_actualizado.id,
            uuid_operacion_offline=conflicto_actualizado.uuid_operacion_offline,
            estado_conflicto=conflicto_actualizado.estado_conflicto,
            fecha_resolucion=conflicto_actualizado.fecha_resolucion or datetime.utcnow(),
            accion=request.accion,
        )

    # ============================================================================
    # VERIFICACIÓN PARA EVITAR REINTENTOS AUTOMÁTICOS
    # ============================================================================

    def conflicto_evita_reintentos_automaticos(
        self, empresa_id: int, uuid_operacion: str
    ) -> bool:
        """Verificar si un conflicto existe y evita reintentos automáticos.

        Retorna True si hay un conflicto NO RESUELTO para este UUID.
        CU13 debe consultar esto antes de reintentar automáticamente.
        """

        conflicto = self.repo.obtener_conflicto_por_uuid(empresa_id, uuid_operacion)

        if not conflicto:
            return False

        # Si el conflicto está sin resolver, evitar reintentos
        return conflicto.estado_conflicto in ["DETECTADO", "PENDIENTE_MANUAL"]


# Importar datetime para la respuesta
from datetime import datetime
