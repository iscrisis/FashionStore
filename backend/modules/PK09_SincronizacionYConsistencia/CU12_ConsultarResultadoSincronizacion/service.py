"""Servicio de CU12 — Consultar resultado de sincronización.

Consulta qué ocurrió con una operación enviada por CU11.
Obtiene información persistida en PostgreSQL sin ejecutar nuevas sincronizaciones.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .repository import ConsultarResultadoRepository
from .schemas import ResultadoSincronizacionOut, ResumenResultadosSincronizacion


class ConsultarResultadoService:
    """Consulta resultados de operaciones sincronizadas."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ConsultarResultadoRepository(db)

    def consultar_resultado_venta(
        self,
        actor: Usuario,
        uuid_local: str,
    ) -> ResultadoSincronizacionOut | None:
        """Consultar resultado de una venta offline.

        Retorna la información si fue sincronizada.
        Retorna None si no existe o no está autorizado.
        """
        # Validar aislamiento
        if actor.rol not in ["ADMINISTRADOR", "CAJERO"]:
            return None

        # Consultar venta sincronizada
        venta = self.repo.obtener_venta_por_uuid_origen(actor.empresa_id, uuid_local)
        if not venta:
            return None

        # Validar sucursal si aplica
        if actor.sucursal_id and venta.sucursal_id != actor.sucursal_id:
            return None

        # Construir resultado
        return ResultadoSincronizacionOut(
            uuid_local=uuid_local,
            tipo_operacion="VENTA_OFFLINE",
            estado="CONFIRMADA",  # Si existe en DB, fue confirmada
            motivo=None,
            venta_id=venta.id,
            codigo_venta=venta.codigo_venta,
            reserva_id=None,
            codigo_reserva=None,
            fecha_local=venta.fecha_creacion,
            fecha_sincronizacion=venta.fecha_creacion,
            total=venta.total,
            empresa_id=venta.empresa_id,
            sucursal_id=venta.sucursal_id,
        )

    def consultar_resultado_reserva(
        self,
        actor: Usuario,
        uuid_local: str,
    ) -> ResultadoSincronizacionOut | None:
        """Consultar resultado de una reserva offline.

        Retorna la información si fue sincronizada.
        Retorna None si no existe o no está autorizado.
        """
        # Validar aislamiento
        if actor.rol not in ["CLIENTE", "ADMINISTRADOR", "CAJERO"]:
            return None

        # Consultar reserva sincronizada
        reserva = self.repo.obtener_reserva_por_uuid_origen(actor.empresa_id, uuid_local)
        if not reserva:
            return None

        # Validar sucursal si aplica
        if actor.sucursal_id and reserva.sucursal_id != actor.sucursal_id:
            return None

        # Validar cliente (solo su propia reserva)
        if actor.rol == "CLIENTE" and reserva.cliente_id != actor.id:
            return None

        # Construir resultado
        return ResultadoSincronizacionOut(
            uuid_local=uuid_local,
            tipo_operacion="RESERVA_OFFLINE",
            estado="CONFIRMADA",  # Si existe en DB, fue confirmada
            motivo=None,
            venta_id=None,
            codigo_venta=None,
            reserva_id=reserva.id,
            codigo_reserva=getattr(reserva, 'codigo_reserva', f"RES-{uuid_local[:8]}"),
            fecha_local=reserva.fecha_creacion,
            fecha_sincronizacion=reserva.fecha_creacion,
            total=None,
            empresa_id=reserva.empresa_id,
            sucursal_id=reserva.sucursal_id,
        )

    def listar_resultados_venta(
        self,
        actor: Usuario,
    ) -> list[ResultadoSincronizacionOut]:
        """Listar todas las ventas sincronizadas del usuario."""
        if actor.rol not in ["ADMINISTRADOR", "CAJERO"]:
            return []

        ventas = self.repo.listar_ventas_sincronizadas(
            actor.empresa_id,
            actor.sucursal_id,
        )

        return [
            ResultadoSincronizacionOut(
                uuid_local=v.uuid_operacion_offline,
                tipo_operacion="VENTA_OFFLINE",
                estado="CONFIRMADA",
                motivo=None,
                venta_id=v.id,
                codigo_venta=v.codigo_venta,
                reserva_id=None,
                codigo_reserva=None,
                fecha_local=v.created_at,
                fecha_sincronizacion=v.created_at,
                total=v.total,
                empresa_id=v.empresa_id,
                sucursal_id=v.sucursal_id,
            )
            for v in ventas
            if v.uuid_operacion_offline  # Validar que existe UUID
        ]

    def listar_resultados_reserva(
        self,
        actor: Usuario,
    ) -> list[ResultadoSincronizacionOut]:
        """Listar todas las reservas sincronizadas del usuario."""
        if actor.rol not in ["CLIENTE", "ADMINISTRADOR", "CAJERO"]:
            return []

        reservas = self.repo.listar_reservas_sincronizadas(
            actor.empresa_id,
            actor.sucursal_id,
        )

        # Filtrar por cliente si es CLIENTE
        if actor.rol == "CLIENTE":
            reservas = [r for r in reservas if r.cliente_id == actor.id]

        return [
            ResultadoSincronizacionOut(
                uuid_local=r.uuid_operacion_offline,
                tipo_operacion="RESERVA_OFFLINE",
                estado="CONFIRMADA",
                motivo=None,
                venta_id=None,
                codigo_venta=None,
                reserva_id=r.id,
                codigo_reserva=getattr(r, 'codigo_reserva', f"RES-{r.uuid_operacion_offline[:8]}"),
                fecha_local=r.created_at,
                fecha_sincronizacion=r.created_at,
                total=None,
                empresa_id=r.empresa_id,
                sucursal_id=r.sucursal_id,
            )
            for r in reservas
            if r.uuid_operacion_offline  # Validar que existe UUID
        ]

    def obtener_resumen(self, actor: Usuario) -> ResumenResultadosSincronizacion:
        """Obtener resumen de conteos de resultados."""
        ventas = self.listar_resultados_venta(actor)
        reservas = self.listar_resultados_reserva(actor)

        todas = ventas + reservas
        confirmadas = sum(1 for r in todas if r.estado == "CONFIRMADA")
        rechazadas = sum(1 for r in todas if r.estado == "RECHAZADA")
        conflictos = sum(1 for r in todas if r.estado == "CONFLICTO")

        return ResumenResultadosSincronizacion(
            confirmadas=confirmadas,
            pendientes=0,  # En futuro: contar pendientes desde IndexedDB
            rechazadas=rechazadas,
            conflictos=conflictos,
            total=len(todas),
        )
