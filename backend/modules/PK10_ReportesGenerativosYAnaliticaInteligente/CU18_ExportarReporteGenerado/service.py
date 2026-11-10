"""Servicio de CU18 -- Exportación de reportes dinámicos a PDF y Excel.

CU18 reutiliza CU17 para generar datos del reporte, luego los formatea
en PDF o Excel según solicitud.

Responsabilidades de CU18:
1. Validar autenticación y autorización.
2. Verificar plan SaaS (reportes_generativos_ia).
3. Delegar a CU17 GenerarReporteDinamicoService para generar datos.
4. Formatear datos en PDF o Excel.
5. Retornar archivo descargable con nombre apropiado.
6. Garantizar aislamiento multitenant.

NO duplica lógica de generación de datos (eso es CU17 y CU30).
"""

import logging
from datetime import date
from io import BytesIO
from typing import Optional, Literal
from decimal import Decimal

from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P7_GestionSaaSySuscripciones.CU05_GestionarSuscripcionEmpresa.service import (
    CapacidadesEmpresa,
    FuncionalidadNoHabilitadaError,
)
from modules.PK10_ReportesGenerativosYAnaliticaInteligente.CU17_GenerarVisualizarReporteDinamico.service import (
    GenerarReporteDinamicoService,
)
from modules.PK10_ReportesGenerativosYAnaliticaInteligente.CU17_GenerarVisualizarReporteDinamico.schemas import (
    GenerarReporteDinamicoRequest,
)

from .schemas import ExportarReporteRequest

logger = logging.getLogger(__name__)


class ExportarReporteService:
    """Exportación de reportes dinámicos a PDF y Excel."""

    def __init__(self, db: Session):
        self.db = db
        self.cu17_service = GenerarReporteDinamicoService(db)

    def exportar(
        self,
        payload: ExportarReporteRequest,
        actor: Usuario,
    ) -> tuple[bytes, str]:
        """Exporta un reporte dinámico a PDF o Excel.

        Args:
            payload: Solicitud con filtros y formato.
            actor: Usuario autenticado.

        Returns:
            Tupla (contenido_archivo_bytes, nombre_archivo).

        Raises:
            ValueError: Usuario no autenticado.
            FuncionalidadNoHabilitadaError: Plan sin reportes_generativos_ia.
        """
        if not actor or not actor.empresa_id:
            logger.error("[CU18] Usuario no autenticado")
            raise ValueError("Usuario no autenticado")

        empresa_id = actor.empresa_id
        logger.info(
            f"[CU18] Exportando reporte. Empresa={empresa_id}, Usuario={actor.id}, "
            f"Formato={payload.formato}"
        )

        # Validar plan SaaS
        try:
            capacidades = CapacidadesEmpresa(self.db, empresa_id)
            capacidades.validar_acceso_a("reportes_generativos_ia")
        except FuncionalidadNoHabilitadaError as e:
            logger.warning(
                f"[CU18] Empresa {empresa_id} sin acceso a reportes_generativos_ia"
            )
            raise e

        # Generar datos vía CU17
        cu17_request = GenerarReporteDinamicoRequest(
            fecha_desde=payload.fecha_desde,
            fecha_hasta=payload.fecha_hasta,
            sucursal_id=payload.sucursal_id,
            categoria_id=payload.categoria_id,
            producto_id=payload.producto_id,
            tipo_reporte=payload.tipo_reporte,
        )
        reporte_response = self.cu17_service.generar_reporte(cu17_request, actor)

        # Formatear según solicitud
        if payload.formato.lower() == "pdf":
            contenido = self._generar_pdf(reporte_response, actor)
            nombre = self._generar_nombre_archivo(
                payload.tipo_reporte, payload.fecha_desde, payload.fecha_hasta, "pdf"
            )
        elif payload.formato.lower() == "xlsx":
            contenido = self._generar_excel(reporte_response, actor)
            nombre = self._generar_nombre_archivo(
                payload.tipo_reporte, payload.fecha_desde, payload.fecha_hasta, "xlsx"
            )
        else:
            raise ValueError(f"Formato no soportado: {payload.formato}")

        logger.info(
            f"[CU18] Reporte exportado exitosamente. Empresa={empresa_id}, "
            f"Tamaño={len(contenido)} bytes"
        )

        return contenido, nombre

    def _generar_pdf(self, reporte, actor: Usuario) -> bytes:
        """Genera PDF con el reporte."""
        pdf = FPDF(format="A4")
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()

        # Colores
        color_primario = (169, 0, 18)  # Rojo FashionStore
        color_texto = (25, 25, 25)
        color_secundario = (102, 102, 102)

        # Encabezado
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*color_primario)
        pdf.cell(0, 10, "REPORTE DE VENTAS", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*color_secundario)
        empresa_nombre = actor.empresa.nombre if hasattr(actor, 'empresa') and actor.empresa else "FashionStore"
        pdf.cell(0, 5, f"Empresa: {empresa_nombre}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, f"Fecha de generación: {date.today().isoformat()}", new_x="LMARGIN", new_y="NEXT")

        # Filtros
        filtros = reporte.filtros_aplicados
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*color_texto)
        pdf.ln(4)
        pdf.cell(0, 5, "FILTROS APLICADOS:", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*color_secundario)
        if filtros.get("fecha_desde"):
            pdf.cell(0, 4, f"- Desde: {filtros['fecha_desde']}", new_x="LMARGIN", new_y="NEXT")
        if filtros.get("fecha_hasta"):
            pdf.cell(0, 4, f"- Hasta: {filtros['fecha_hasta']}", new_x="LMARGIN", new_y="NEXT")
        if filtros.get("sucursal_id"):
            pdf.cell(0, 4, f"- Sucursal ID: {filtros['sucursal_id']}", new_x="LMARGIN", new_y="NEXT")
        if filtros.get("categoria_id"):
            pdf.cell(0, 4, f"- Categoria ID: {filtros['categoria_id']}", new_x="LMARGIN", new_y="NEXT")
        if filtros.get("producto_id"):
            pdf.cell(0, 4, f"- Producto ID: {filtros['producto_id']}", new_x="LMARGIN", new_y="NEXT")

        # Resumen
        if reporte.resumen:
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*color_texto)
            pdf.cell(0, 5, "RESUMEN:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*color_secundario)
            resumen = reporte.resumen
            if isinstance(resumen, dict):
                for clave, valor in resumen.items():
                    if isinstance(valor, (int, float, Decimal)):
                        pdf.cell(0, 4, f"- {clave}: {valor}", new_x="LMARGIN", new_y="NEXT")

        # Datos detallados (por semana)
        if reporte.datos and "por_semana" in reporte.datos:
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*color_texto)
            pdf.cell(0, 5, "VENTAS POR SEMANA:", new_x="LMARGIN", new_y="NEXT")

            semanas = reporte.datos.get("por_semana", {}).get("semanas", [])
            if semanas:
                pdf.set_font("Helvetica", "", 8)
                for semana in semanas:
                    semana_str = semana.get("semana", "")
                    ventas = semana.get("ventas", 0)
                    ingresos = semana.get("ingresos", 0)
                    pdf.cell(0, 4, f"  {semana_str}: {ventas} ventas, Bs {ingresos:.2f}",
                            new_x="LMARGIN", new_y="NEXT")

        # Datos por categoría
        if reporte.datos and "por_categoria" in reporte.datos:
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*color_texto)
            pdf.cell(0, 5, "INGRESOS POR CATEGORIA:", new_x="LMARGIN", new_y="NEXT")

            categorias = reporte.datos.get("por_categoria", {}).get("categorias", [])
            if categorias:
                pdf.set_font("Helvetica", "", 8)
                for cat in categorias:
                    nombre = cat.get("nombre", "")
                    unidades = cat.get("unidades", 0)
                    ingresos = cat.get("ingresos", 0)
                    pdf.cell(0, 4, f"  {nombre}: {unidades} unidades, Bs {ingresos:.2f}",
                            new_x="LMARGIN", new_y="NEXT")

        buffer = BytesIO()
        pdf.output(buffer)
        return buffer.getvalue()

    def _generar_excel(self, reporte, actor: Usuario) -> bytes:
        """Genera Excel XLSX con el reporte."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte"

        # Estilos
        header_fill = PatternFill(start_color="A90012", end_color="A90012", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Encabezado
        ws["A1"] = "REPORTE DE VENTAS"
        ws["A1"].font = Font(bold=True, size=14, color="A90012")
        ws.merge_cells("A1:F1")

        empresa_nombre = actor.empresa.nombre if hasattr(actor, 'empresa') and actor.empresa else "FashionStore"
        ws["A2"] = f"Empresa: {empresa_nombre}"
        ws["A3"] = f"Fecha de generación: {date.today().isoformat()}"

        row = 5

        # Filtros aplicados
        ws[f"A{row}"] = "FILTROS APLICADOS:"
        ws[f"A{row}"].font = Font(bold=True)
        row += 1

        filtros = reporte.filtros_aplicados
        if filtros.get("fecha_desde"):
            ws[f"A{row}"] = f"Desde: {filtros['fecha_desde']}"
            row += 1
        if filtros.get("fecha_hasta"):
            ws[f"A{row}"] = f"Hasta: {filtros['fecha_hasta']}"
            row += 1

        row += 1

        # Tabla: Ventas por semana
        if reporte.datos and "por_semana" in reporte.datos:
            ws[f"A{row}"] = "VENTAS POR SEMANA"
            ws[f"A{row}"].font = Font(bold=True)
            row += 1

            semanas = reporte.datos.get("por_semana", {}).get("semanas", [])
            if semanas:
                headers = ["Semana", "Ventas", "Ingresos"]
                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=row, column=col)
                    cell.value = header
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.border = border
                    cell.alignment = Alignment(horizontal="center")

                row += 1

                for semana in semanas:
                    ws.cell(row=row, column=1).value = semana.get("semana", "")
                    ws.cell(row=row, column=2).value = semana.get("ventas", 0)
                    ws.cell(row=row, column=3).value = semana.get("ingresos", 0)
                    for col in range(1, 4):
                        ws.cell(row=row, column=col).border = border
                    row += 1

                ws.column_dimensions["A"].width = 15
                ws.column_dimensions["B"].width = 12
                ws.column_dimensions["C"].width = 15

            row += 2

        # Tabla: Ingresos por categoría
        if reporte.datos and "por_categoria" in reporte.datos:
            ws[f"A{row}"] = "INGRESOS POR CATEGORÍA"
            ws[f"A{row}"].font = Font(bold=True)
            row += 1

            categorias = reporte.datos.get("por_categoria", {}).get("categorias", [])
            if categorias:
                headers = ["Categoría", "Unidades", "Ingresos"]
                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=row, column=col)
                    cell.value = header
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.border = border
                    cell.alignment = Alignment(horizontal="center")

                row += 1

                for cat in categorias:
                    ws.cell(row=row, column=1).value = cat.get("nombre", "")
                    ws.cell(row=row, column=2).value = cat.get("unidades", 0)
                    ws.cell(row=row, column=3).value = cat.get("ingresos", 0)
                    for col in range(1, 4):
                        ws.cell(row=row, column=col).border = border
                    row += 1

                ws.column_dimensions["A"].width = 20
                ws.column_dimensions["B"].width = 12
                ws.column_dimensions["C"].width = 15

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _generar_nombre_archivo(
        self,
        tipo_reporte: str,
        fecha_desde: Optional[date],
        fecha_hasta: Optional[date],
        formato: str,
    ) -> str:
        """Genera nombre descriptivo para el archivo."""
        fecha_hoy = date.today().isoformat()
        desde_str = fecha_desde.isoformat() if fecha_desde else "inicio"
        hasta_str = fecha_hasta.isoformat() if fecha_hasta else "fin"

        nombre = f"reporte_{tipo_reporte}_{desde_str}_{hasta_str}_{fecha_hoy}.{formato}"
        return nombre
