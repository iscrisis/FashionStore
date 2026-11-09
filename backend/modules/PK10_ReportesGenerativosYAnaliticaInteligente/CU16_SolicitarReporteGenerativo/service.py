"""Servicio de CU16 -- Orquestación de solicitud de reporte generativo.

CU16 gestiona el flujo de solicitud que entra (texto/voz → transcrito ya en frontend).
Reutiliza completamente la lógica de CU30 para interpretación y generación.

Responsabilidades de CU16:
1. Verificar autenticación y permisos.
2. Validar que el plan SaaS tenga habilitado reportes_generativos_ia.
3. Delegar a ConsultaInteligenteService (CU30) para la interpretación real.
4. Garantizar que los criterios se validen antes de consultar PostgreSQL.

NO duplica lógica de CU30.
"""

import logging
from sqlalchemy.orm import Session

from modules.P6_InnovacionYAnalisis.CU30_ConsultarReportesIndicadores.consulta_inteligente_service import (
    ConsultaInteligenteService,
)
from modules.P6_InnovacionYAnalisis.CU30_ConsultarReportesIndicadores.schemas import (
    ConsultaInteligenteRequest,
    ConsultaInteligenteResponse,
)
from modules.P7_GestionSaaSySuscripciones.CU05_GestionarSuscripcionEmpresa.service import (
    CapacidadesEmpresa,
    FuncionalidadNoHabilitadaError,
)
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

logger = logging.getLogger(__name__)


class SolicitarReporteGenerativoService:
    """Orquestación de solicitud de reporte generativo (CU16).

    Reutiliza ConsultaInteligenteService de CU30 sin duplicar su lógica.
    """

    def __init__(self, db: Session):
        self.db = db
        self.consulta_inteligente = ConsultaInteligenteService(db)

    def procesar_solicitud(
        self,
        payload: ConsultaInteligenteRequest,
        actor: Usuario,
    ) -> ConsultaInteligenteResponse:
        """Procesa una solicitud de reporte generativo.

        Flujo:
        1. Verificar autenticación.
        2. Validar plan SaaS.
        3. Delegar a CU30 para interpretación.

        Args:
            payload: Solicitud (texto/voz ya transcrita).
            actor: Usuario autenticado.

        Returns:
            Respuesta con interpretación y datos.

        Raises:
            FuncionalidadNoHabilitadaError: Si el plan no incluye reportes_generativos_ia.
        """
        if not actor or not actor.empresa_id:
            logger.error("[CU16] Usuario no autenticado")
            raise ValueError("Usuario no autenticado")

        # Validar que el plan tenga habilitado reportes_generativos_ia
        try:
            capacidades = CapacidadesEmpresa(self.db, actor.empresa_id)
            capacidades.validar_acceso_a("reportes_generativos_ia")
        except FuncionalidadNoHabilitadaError as e:
            logger.warning(
                f"[CU16] Empresa {actor.empresa_id} sin acceso a reportes_generativos_ia"
            )
            raise e

        logger.info(
            f"[CU16] Procesando solicitud para empresa={actor.empresa_id}, "
            f"usuario={actor.id}: {payload.consulta[:50]}..."
        )

        # Delegar a CU30 para la interpretación y generación
        # CU16 NO modifica la lógica de CU30, solo la orquesta
        resultado = self.consulta_inteligente.consultar(payload)

        logger.info(
            f"[CU16] Solicitud procesada exitosamente. "
            f"Intención: {resultado.intencion}, Éxito: {resultado.exito}"
        )

        return resultado
