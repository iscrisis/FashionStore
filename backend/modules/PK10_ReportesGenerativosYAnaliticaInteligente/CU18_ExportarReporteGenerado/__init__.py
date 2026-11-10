"""CU18 - Exportar Reporte Generado.

Responsabilidades:
1. Recibir solicitud de exportación con filtros y formato (PDF/XLSX).
2. Reutilizar CU17 para generar datos del reporte.
3. Formatear datos en PDF o Excel según solicitud.
4. Devolver archivo descargable.
5. Validar autenticación, SaaS y aislamiento multitenant.
"""

from .router import router

__all__ = ["router"]
