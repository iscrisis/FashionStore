"""Servicio de CU17 -- Orquestación de generación de reporte dinámico.

CU17 recibe solicitud con filtros (fecha, sucursal, categoría, producto).
Reutiliza ReportesService de CU30 para obtener datos sin duplicar.

Responsabilidades de CU17:
1. Validar autenticación y autorización.
2. Verificar plan SaaS (reportes_generativos_ia).
3. Validar que categoría/producto existan y pertenezcan a la empresa.
4. Delegar a ReportesService para generación de datos.
5. Construir respuesta estructurada con metadatos.
6. Garantizar aislamiento multitenant.

NO duplica lógica de generación de datos (eso es CU30).
"""

import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from modules.P6_InnovacionYAnalisis.CU30_ConsultarReportesIndicadores.service import (
    ReportesService,
    RangoFechaInvalidoError,
    SucursalInvalidaError,
)
from modules.P7_GestionSaaSySuscripciones.CU05_GestionarSuscripcionEmpresa.service import (
    CapacidadesEmpresa,
    FuncionalidadNoHabilitadaError,
)
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.producto import Producto

from .schemas import (
    GenerarReporteDinamicoRequest,
    GenerarReporteDinamicoResponse,
)

logger = logging.getLogger(__name__)


class CategoriaNoEncontradaError(Exception):
    """Categoría solicitada no existe o no pertenece a la empresa."""


class ProductoNoEncontradoError(Exception):
    """Producto solicitado no existe o no pertenece a la empresa."""


class GenerarReporteDinamicoService:
    """Orquestación de generación de reporte dinámico (CU17).

    Reutiliza ReportesService de CU30 para obtener datos.
    Valida autorización, filtros y aislamiento multitenant.
    """

    def __init__(self, db: Session):
        self.db = db
        self.reportes = ReportesService(db)

    def generar_reporte(
        self,
        payload: GenerarReporteDinamicoRequest,
        actor: Usuario,
    ) -> GenerarReporteDinamicoResponse:
        """Genera un reporte dinámico con los filtros especificados.

        Flujo:
        1. Validar autenticación.
        2. Verificar plan SaaS.
        3. Validar categoría/producto (si aplica).
        4. Delegar a ReportesService para datos.
        5. Construir respuesta.

        Args:
            payload: Solicitud con filtros.
            actor: Usuario autenticado.

        Returns:
            Respuesta con datos del reporte.

        Raises:
            ValueError: Usuario no autenticado.
            FuncionalidadNoHabilitadaError: Plan sin reportes_generativos_ia.
            CategoriaNoEncontradaError: Categoría no válida.
            ProductoNoEncontradoError: Producto no válido.
            RangoFechaInvalidoError: Rango de fechas inválido.
            SucursalInvalidaError: Sucursal no válida.
        """
        if not actor or not actor.empresa_id:
            logger.error("[CU17] Usuario no autenticado")
            raise ValueError("Usuario no autenticado")

        empresa_id = actor.empresa_id
        logger.info(
            f"[CU17] Generando reporte para empresa={empresa_id}, usuario={actor.id}"
        )

        # 1. Validar plan SaaS
        try:
            capacidades = CapacidadesEmpresa(self.db, empresa_id)
            capacidades.validar_acceso_a("reportes_generativos_ia")
        except FuncionalidadNoHabilitadaError as e:
            logger.warning(
                f"[CU17] Empresa {empresa_id} sin acceso a reportes_generativos_ia"
            )
            raise e

        # 2. Validar categoría (si aplica)
        if payload.categoria_id is not None:
            categoria = self.db.query(Categoria).filter(
                Categoria.id == payload.categoria_id,
                Categoria.empresa_id == empresa_id,
            ).first()
            if not categoria:
                logger.warning(
                    f"[CU17] Categoría {payload.categoria_id} no encontrada para empresa {empresa_id}"
                )
                raise CategoriaNoEncontradaError(
                    f"Categoría {payload.categoria_id} no existe o no pertenece a tu empresa"
                )

        # 3. Validar producto (si aplica)
        if payload.producto_id is not None:
            producto = self.db.query(Producto).filter(
                Producto.id == payload.producto_id,
                Producto.empresa_id == empresa_id,
            ).first()
            if not producto:
                logger.warning(
                    f"[CU17] Producto {payload.producto_id} no encontrado para empresa {empresa_id}"
                )
                raise ProductoNoEncontradoError(
                    f"Producto {payload.producto_id} no existe o no pertenece a tu empresa"
                )

        # 4. Generar reporte según tipo solicitado
        tipo = payload.tipo_reporte.lower()
        try:
            if tipo == "ventas":
                datos = self._generar_reporte_ventas(
                    payload.fecha_desde,
                    payload.fecha_hasta,
                    payload.sucursal_id,
                    payload.categoria_id,
                    payload.producto_id,
                    empresa_id,
                )
            elif tipo == "inventario":
                datos = self._generar_reporte_inventario(
                    payload.sucursal_id,
                    payload.categoria_id,
                    payload.producto_id,
                    empresa_id,
                )
            elif tipo == "productos":
                datos = self._generar_reporte_productos(
                    payload.fecha_desde,
                    payload.fecha_hasta,
                    payload.sucursal_id,
                    payload.categoria_id,
                    empresa_id,
                )
            else:  # "completo" o desconocido
                datos = self._generar_reporte_completo(
                    payload.fecha_desde,
                    payload.fecha_hasta,
                    payload.sucursal_id,
                    payload.categoria_id,
                    payload.producto_id,
                    empresa_id,
                )
        except (RangoFechaInvalidoError, SucursalInvalidaError) as e:
            logger.error(f"[CU17] Error en validación de parámetros: {str(e)}")
            raise

        logger.info(
            f"[CU17] Reporte generado exitosamente. "
            f"Tipo: {tipo}, Empresa: {empresa_id}"
        )

        # 5. Construir respuesta
        filtros_aplicados = {
            "fecha_desde": payload.fecha_desde.isoformat() if payload.fecha_desde else None,
            "fecha_hasta": payload.fecha_hasta.isoformat() if payload.fecha_hasta else None,
            "sucursal_id": payload.sucursal_id,
            "categoria_id": payload.categoria_id,
            "producto_id": payload.producto_id,
        }

        return GenerarReporteDinamicoResponse(
            tipo_reporte=tipo,
            exito=True,
            filtros_aplicados=filtros_aplicados,
            resumen=datos.get("resumen"),
            datos=datos,
        )

    def _generar_reporte_ventas(
        self,
        desde: Optional[date],
        hasta: Optional[date],
        sucursal_id: Optional[int],
        categoria_id: Optional[int],
        producto_id: Optional[int],
        empresa_id: int,
    ) -> dict:
        """Genera reporte de ventas con filtros opcionales."""
        resultado = self.reportes.ventas(
            desde, hasta, sucursal_id, empresa_id,
            categoria_id=categoria_id,
            producto_id=producto_id
        )
        datos = resultado.dict()

        # Agregar datos por semana si hay rango de fechas
        if desde or hasta:
            datos["por_semana"] = self.reportes.ventas_por_semana(desde, hasta, sucursal_id, empresa_id).get("semanas", [])

        return datos

    def _generar_reporte_inventario(
        self,
        sucursal_id: Optional[int],
        categoria_id: Optional[int],
        producto_id: Optional[int],
        empresa_id: int,
    ) -> dict:
        """Genera reporte de inventario con filtros opcionales."""
        resultado = self.reportes.inventario(sucursal_id, empresa_id)
        return resultado.dict()

    def _generar_reporte_productos(
        self,
        desde: Optional[date],
        hasta: Optional[date],
        sucursal_id: Optional[int],
        categoria_id: Optional[int],
        empresa_id: int,
    ) -> dict:
        """Genera reporte de productos más vendidos, opcionalmente por categoría."""
        datos = {}

        # Productos más vendidos (top 10)
        productos = self.reportes.productos_mas_vendidos(desde, hasta, sucursal_id, empresa_id)
        datos["top_productos"] = productos.dict()

        # Ventas por categoría
        datos["por_categoria"] = self.reportes.ventas_por_categoria(desde, hasta, sucursal_id, empresa_id)

        return datos

    def _generar_reporte_completo(
        self,
        desde: Optional[date],
        hasta: Optional[date],
        sucursal_id: Optional[int],
        categoria_id: Optional[int],
        producto_id: Optional[int],
        empresa_id: int,
    ) -> dict:
        """Genera reporte completo con todos los datos disponibles."""
        resumen = self.reportes.resumen(desde, hasta, sucursal_id, empresa_id)
        ventas = self.reportes.ventas(desde, hasta, sucursal_id, empresa_id)
        inventario = self.reportes.inventario(sucursal_id, empresa_id)
        productos = self.reportes.productos_mas_vendidos(desde, hasta, sucursal_id, empresa_id)

        datos = {
            "resumen": resumen.dict(),
            "ventas": ventas.dict(),
            "inventario": inventario.dict(),
            "productos": productos.dict(),
        }

        # Agregar análisis avanzados
        if desde or hasta:
            datos["por_semana"] = self.reportes.ventas_por_semana(desde, hasta, sucursal_id, empresa_id)

        datos["por_categoria"] = self.reportes.ventas_por_categoria(desde, hasta, sucursal_id, empresa_id)

        return datos
