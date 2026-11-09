"""Repositorio de CU11 — Sincronizar operaciones pendientes.

Responsable de:
- Verificar idempotencia (UUID ya procesado)
- Registrar operaciones de forma transaccional
- Actualizar estados de sincronización
"""

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from modules.P5_ComprasVentasYPagos.Models.venta import Venta
from modules.P4_ReservasYAtencion.Models.reserva import Reserva


class RegistroSincronizacionRepository:
    """Repositorio para auditoría e idempotencia de sincronizaciones.

    NOTA: La idempotencia se implementa mediante:
    1. Restricción UNIQUE sobre (empresa_id, uuid_operacion_local)
    2. Lectura antes de insertar
    3. Transacción atómica

    Los registros de sincronización no existen aún como modelo.
    Se recomienda crearlos en una migración Alembic futura.

    Por ahora, la idempotencia se valida consultando si la Venta/Reserva
    con ese UUID_ORIGEN ya existe.
    """

    def __init__(self, db: Session):
        self.db = db

    def obtener_venta_por_uuid_origen(self, empresa_id: int, uuid_origen: str) -> Venta | None:
        """Obtener venta que ya fue sincronizada con este UUID.

        Valida idempotencia: si la venta ya existe con este UUID, retornarla.
        """
        stmt = select(Venta).where(
            and_(
                Venta.empresa_id == empresa_id,
                Venta.uuid_operacion_offline == uuid_origen,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def obtener_reserva_por_uuid_origen(self, empresa_id: int, uuid_origen: str) -> Reserva | None:
        """Obtener reserva que ya fue sincronizada con este UUID.

        Valida idempotencia: si la reserva ya existe con este UUID, retornarla.
        """
        stmt = select(Reserva).where(
            and_(
                Reserva.empresa_id == empresa_id,
                Reserva.uuid_operacion_offline == uuid_origen,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def registrar_sincronizacion_venta(
        self,
        empresa_id: int,
        uuid_origen: str,
        venta: Venta,
    ) -> None:
        """Guardar relación entre UUID local y Venta oficial.

        Esto se hace dentro de la transacción de CU24 que crea la venta.
        El campo uuid_operacion_offline de Venta se asigna durante creación.
        """
        # La Venta ya tiene uuid_operacion_offline asignado
        # No hay acción adicional aquí en esta fase
        pass
