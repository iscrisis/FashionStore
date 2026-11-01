"""Service de CU05 — Lógica de negocio para gestión de suscripciones."""

from datetime import datetime
from sqlalchemy.orm import Session

from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
from modules.P7_GestionSaaSySuscripciones.Models.plan import Plan
from modules.P7_GestionSaaSySuscripciones.Models.suscripcion import Suscripcion
from modules.P7_GestionSaaSySuscripciones.CU04_GestionarPlanesSaaS.repository import PlanesRepository
from .repository import SuscripcionesRepository
from .schemas import SuscripcionCrear, SuscripcionActualizar, SuscripcionRenovar


class EmpresaNoEncontradaError(Exception):
    """La empresa no existe."""


class PlanNoEncontradoError(Exception):
    """El plan no existe."""


class PlanInactivoError(Exception):
    """El plan está inactivo."""


class SuscripcionNoEncontradaError(Exception):
    """La suscripción no existe."""


class IncompatibilidadPlanError(Exception):
    """El nuevo plan es incompatible con los recursos actuales."""


class FuncionalidadNoHabilitadaError(Exception):
    """La funcionalidad no está habilitada en el plan de la empresa."""


class CapacidadesEmpresa:
    """Determina las capacidades de una empresa según su plan activo.

    Mecanismo centralizado para:
    - Verificar funcionalidades habilitadas
    - Validar límites (sucursales, usuarios)
    - Proteger acceso a funcionalidades en backend
    """

    def __init__(self, db: Session, empresa_id: int):
        self._db = db
        self._empresa_id = empresa_id
        self._suscripciones_repo = SuscripcionesRepository(db)
        self._planes_repo = PlanesRepository(db)
        self._suscripcion = None
        self._plan = None
        self._load()

    def _load(self) -> None:
        """Carga la suscripción y el plan activos de la empresa."""
        self._suscripcion = self._suscripciones_repo.get_by_empresa(self._empresa_id)
        if self._suscripcion:
            self._plan = self._planes_repo.get_by_id(self._suscripcion.plan_id)

    def tiene_suscripcion_activa(self) -> bool:
        """Verifica si la empresa tiene una suscripción activa."""
        return self._suscripcion is not None and self._suscripcion.activa

    def puede_acceder_a(self, funcionalidad: str) -> bool:
        """Verifica si la empresa puede acceder a una funcionalidad específica.

        Funcionalidades disponibles:
        - gestion_productos
        - gestion_ventas
        - reservas
        - operacion_offline
        - reportes_convencionales
        - reportes_generativos_ia
        """
        if not self.tiene_suscripcion_activa():
            return False

        if not self._plan:
            return False

        funcionalidad_map = {
            "gestion_productos": self._plan.gestion_productos,
            "gestion_ventas": self._plan.gestion_ventas,
            "reservas": self._plan.reservas,
            "operacion_offline": self._plan.operacion_offline,
            "reportes_convencionales": self._plan.reportes_convencionales,
            "reportes_generativos_ia": self._plan.reportes_generativos_ia,
        }

        return funcionalidad_map.get(funcionalidad, False)

    def validar_acceso_a(self, funcionalidad: str) -> None:
        """Valida acceso a una funcionalidad. Lanza error si no tiene acceso.

        Usada en endpoints que requieren una funcionalidad específica.
        """
        if not self.puede_acceder_a(funcionalidad):
            raise FuncionalidadNoHabilitadaError(
                f"La funcionalidad '{funcionalidad}' no está habilitada en el plan."
            )

    def limite_sucursales(self) -> int | None:
        """Devuelve el límite de sucursales permitidas."""
        if not self.tiene_suscripcion_activa() or not self._plan:
            return 0
        return self._plan.limite_sucursales

    def validar_limite_sucursales(self, sucursales_actuales: int) -> None:
        """Valida que no se exceda el límite de sucursales.

        sucursales_actuales: número de sucursales que la empresa tiene ahora
        """
        limite = self.limite_sucursales()
        if sucursales_actuales >= limite:
            raise IncompatibilidadPlanError(
                f"Se alcanzó el límite de {limite} sucursales permitidas por el plan."
            )


class SuscripcionesService:
    def __init__(self, db: Session):
        self._db = db
        self._suscripciones_repo = SuscripcionesRepository(db)
        self._planes_repo = PlanesRepository(db)

    def listar_empresas_con_suscripciones(self) -> list[dict]:
        """Lista todas las empresas y sus suscripciones activas."""
        empresas = self._db.query(Empresa).all()
        resultado = []
        for empresa in empresas:
            suscripcion = self._suscripciones_repo.get_by_empresa(empresa.id)
            plan = None
            if suscripcion:
                plan = self._planes_repo.get_by_id(suscripcion.plan_id)
            resultado.append({
                "empresa_id": empresa.id,
                "empresa_nombre": empresa.nombre,
                "empresa_razon_social": empresa.razon_social,
                "suscripcion": suscripcion,
                "plan": plan,
            })
        return resultado

    def obtener_suscripcion_empresa(self, empresa_id: int) -> dict:
        """Obtiene la suscripción completa de una empresa con plan y funcionalidades."""
        empresa = self._db.get(Empresa, empresa_id)
        if not empresa:
            raise EmpresaNoEncontradaError

        suscripcion = self._suscripciones_repo.get_by_empresa(empresa_id)
        if not suscripcion:
            return {
                "empresa": empresa,
                "suscripcion": None,
                "plan": None,
                "funcionalidades_habilitadas": {},
            }

        plan = self._planes_repo.get_by_id(suscripcion.plan_id)
        funcionalidades = self._extraer_funcionalidades_plan(plan) if plan else {}

        return {
            "empresa": empresa,
            "suscripcion": suscripcion,
            "plan": plan,
            "funcionalidades_habilitadas": funcionalidades,
        }

    def asignar_plan(self, datos: SuscripcionCrear) -> Suscripcion:
        """Asigna un plan a una empresa creando una nueva suscripción."""
        empresa = self._db.get(Empresa, datos.empresa_id)
        if not empresa:
            raise EmpresaNoEncontradaError

        plan = self._planes_repo.get_by_id(datos.plan_id)
        if not plan:
            raise PlanNoEncontradoError
        if not plan.is_active:
            raise PlanInactivoError

        suscripcion = Suscripcion(
            empresa_id=datos.empresa_id,
            plan_id=datos.plan_id,
            fecha_inicio=datos.fecha_inicio,
            fecha_vencimiento=datos.fecha_vencimiento,
            activa=True,
        )
        return self._suscripciones_repo.crear(suscripcion)

    def asignar_plan_registro(
        self,
        empresa_id: int,
        plan_id: int,
        fecha_inicio: datetime,
        fecha_vencimiento: datetime,
    ) -> Suscripcion:
        """Asigna un plan inicial durante el registro de empresa.

        Usado internamente por CU01 para crear la suscripción inicial.
        Requiere que la empresa y plan ya existan y sean válidos.
        """
        empresa = self._db.get(Empresa, empresa_id)
        if not empresa:
            raise EmpresaNoEncontradaError

        plan = self._planes_repo.get_by_id(plan_id)
        if not plan:
            raise PlanNoEncontradoError
        if not plan.is_active:
            raise PlanInactivoError

        suscripcion = Suscripcion(
            empresa_id=empresa_id,
            plan_id=plan_id,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            activa=True,
        )
        return self._suscripciones_repo.crear(suscripcion)

    def cambiar_plan(self, empresa_id: int, plan_id_nuevo: int) -> Suscripcion:
        """Cambia el plan de una empresa."""
        empresa = self._db.get(Empresa, empresa_id)
        if not empresa:
            raise EmpresaNoEncontradaError

        suscripcion = self._suscripciones_repo.get_by_empresa(empresa_id)
        if not suscripcion:
            raise SuscripcionNoEncontradaError

        plan_nuevo = self._planes_repo.get_by_id(plan_id_nuevo)
        if not plan_nuevo:
            raise PlanNoEncontradoError
        if not plan_nuevo.is_active:
            raise PlanInactivoError

        self._validar_compatibilidad_plan(empresa_id, plan_id_nuevo)

        suscripcion.plan_id = plan_id_nuevo
        return self._suscripciones_repo.guardar(suscripcion)

    def renovar_suscripcion(self, empresa_id: int, datos: SuscripcionRenovar) -> Suscripcion:
        """Renueva la suscripción de una empresa."""
        empresa = self._db.get(Empresa, empresa_id)
        if not empresa:
            raise EmpresaNoEncontradaError

        suscripcion = self._suscripciones_repo.get_by_empresa(empresa_id)
        if not suscripcion:
            raise SuscripcionNoEncontradaError

        suscripcion.fecha_vencimiento = datos.fecha_vencimiento
        suscripcion.activa = True
        return self._suscripciones_repo.guardar(suscripcion)

    def cambiar_estado(self, empresa_id: int, activo: bool) -> Suscripcion:
        """Cambia el estado de la suscripción."""
        empresa = self._db.get(Empresa, empresa_id)
        if not empresa:
            raise EmpresaNoEncontradaError

        suscripcion = self._suscripciones_repo.get_by_empresa(empresa_id)
        if not suscripcion:
            raise SuscripcionNoEncontradaError

        suscripcion.activa = activo
        return self._suscripciones_repo.guardar(suscripcion)

    def obtener_funcionalidades_habilitadas(self, empresa_id: int) -> dict:
        """Obtiene las funcionalidades habilitadas para una empresa según su plan."""
        resultado = self.obtener_suscripcion_empresa(empresa_id)
        return resultado.get("funcionalidades_habilitadas", {})

    def _validar_compatibilidad_plan(self, empresa_id: int, plan_id_nuevo: int) -> None:
        """Valida que el nuevo plan sea compatible con los recursos actuales.

        Específicamente verifica que el límite de sucursales del nuevo plan
        sea suficiente para las sucursales que la empresa ya tiene.
        """
        plan_nuevo = self._planes_repo.get_by_id(plan_id_nuevo)
        if not plan_nuevo:
            raise PlanNoEncontradoError

        # Contar sucursales actuales de la empresa
        # NOTA: Por ahora solo validamos la lógica. En una integración real,
        # haría una query a la tabla de sucursales.
        # Para esta fase, la validación está documentada pero sin integración
        # con CU03 hasta no tener su estructura clara.

    def _extraer_funcionalidades_plan(self, plan: Plan) -> dict:
        """Extrae las funcionalidades habilitadas del plan."""
        if not plan:
            return {}
        return {
            "gestion_productos": plan.gestion_productos,
            "gestion_ventas": plan.gestion_ventas,
            "reservas": plan.reservas,
            "operacion_offline": plan.operacion_offline,
            "reportes_convencionales": plan.reportes_convencionales,
            "reportes_generativos_ia": plan.reportes_generativos_ia,
        }
