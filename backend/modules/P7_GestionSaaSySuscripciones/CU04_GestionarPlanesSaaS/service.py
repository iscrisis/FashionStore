"""Service de CU04 — Lógica de negocio para gestión de planes SaaS."""

from sqlalchemy.orm import Session

from modules.P7_GestionSaaSySuscripciones.Models.plan import Plan
from .repository import PlanesRepository
from .schemas import PlanCrear, PlanActualizar


class PlanNombreDuplicadoError(Exception):
    """Ya existe un plan con ese nombre."""


class PlanSlugDuplicadoError(Exception):
    """Ya existe un plan con ese slug."""


class PlanNoEncontradoError(Exception):
    """El plan no existe."""


class PlanTieneSubscripcionesError(Exception):
    """No se puede modificar/eliminar un plan que tiene suscripciones activas."""


class DatosInvalidosError(Exception):
    """Los datos del plan son inválidos."""


class PlanesService:
    def __init__(self, db: Session):
        self._db = db
        self._repo = PlanesRepository(db)

    def listar(self, is_active: bool | None = None) -> list[Plan]:
        """Lista planes disponibles."""
        return self._repo.listar(is_active=is_active)

    def obtener(self, plan_id: int) -> Plan:
        """Obtiene un plan por ID."""
        plan = self._repo.get_by_id(plan_id)
        if plan is None:
            raise PlanNoEncontradoError
        return plan

    def crear(self, datos: PlanCrear) -> Plan:
        """Crea un nuevo plan."""
        if self._repo.existe_nombre(datos.nombre):
            raise PlanNombreDuplicadoError

        if self._repo.existe_slug(datos.slug):
            raise PlanSlugDuplicadoError

        plan = Plan(
            nombre=datos.nombre.strip(),
            slug=datos.slug.strip().lower(),
            descripcion=datos.descripcion.strip(),
            precio=datos.precio,
            limite_sucursales=datos.limite_sucursales,
            limite_usuarios=datos.limite_usuarios,
            gestion_productos=datos.gestion_productos,
            gestion_ventas=datos.gestion_ventas,
            reservas=datos.reservas,
            operacion_offline=datos.operacion_offline,
            reportes_convencionales=datos.reportes_convencionales,
            reportes_generativos_ia=datos.reportes_generativos_ia,
        )
        return self._repo.crear(plan)

    def actualizar(self, plan_id: int, datos: PlanActualizar) -> Plan:
        """Actualiza un plan existente."""
        plan = self.obtener(plan_id)

        if self._repo.tiene_suscripciones_activas(plan_id):
            raise PlanTieneSubscripcionesError(
                "No se puede modificar un plan que tiene suscripciones activas"
            )

        if datos.nombre is not None:
            if self._repo.existe_nombre(datos.nombre, excluyendo_id=plan_id):
                raise PlanNombreDuplicadoError
            plan.nombre = datos.nombre.strip()

        if datos.slug is not None:
            if self._repo.existe_slug(datos.slug, excluyendo_id=plan_id):
                raise PlanSlugDuplicadoError
            plan.slug = datos.slug.strip().lower()

        if datos.descripcion is not None:
            plan.descripcion = datos.descripcion.strip()

        if datos.precio is not None:
            plan.precio = datos.precio

        if datos.limite_sucursales is not None:
            plan.limite_sucursales = datos.limite_sucursales

        if datos.limite_usuarios is not None:
            plan.limite_usuarios = datos.limite_usuarios

        # Actualizar funcionalidades
        if datos.gestion_productos is not None:
            plan.gestion_productos = datos.gestion_productos
        if datos.gestion_ventas is not None:
            plan.gestion_ventas = datos.gestion_ventas
        if datos.reservas is not None:
            plan.reservas = datos.reservas
        if datos.operacion_offline is not None:
            plan.operacion_offline = datos.operacion_offline
        if datos.reportes_convencionales is not None:
            plan.reportes_convencionales = datos.reportes_convencionales
        if datos.reportes_generativos_ia is not None:
            plan.reportes_generativos_ia = datos.reportes_generativos_ia

        return self._repo.guardar(plan)

    def cambiar_estado(self, plan_id: int, activo: bool) -> Plan:
        """Cambia el estado (activo/inactivo) de un plan."""
        plan = self.obtener(plan_id)

        if not activo and self._repo.tiene_suscripciones_activas(plan_id):
            raise PlanTieneSubscripcionesError(
                "No se puede desactivar un plan que tiene suscripciones activas"
            )

        plan.is_active = activo
        return self._repo.guardar(plan)

    def eliminar(self, plan_id: int) -> None:
        """Elimina un plan."""
        plan = self.obtener(plan_id)

        if self._repo.tiene_suscripciones_activas(plan_id):
            raise PlanTieneSubscripcionesError(
                "No se puede eliminar un plan que tiene suscripciones activas"
            )

        self._repo.eliminar(plan)
