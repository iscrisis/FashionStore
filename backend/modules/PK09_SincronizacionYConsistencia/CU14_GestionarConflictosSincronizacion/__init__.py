"""CU14 — Gestionar conflictos de sincronización.

Módulo responsable de:
- Detectar conflictos reales informados por CU11
- Registrar conflictos para auditoría
- Mantener trazabilidad del UUID original
- Evitar reintentos indefinidos mediante CU13
- Permitir consulta y resolución manual de conflictos
- Impedir duplicación de operaciones
"""

from .service import GestionarConflictosService
from .repository import ConflictoRepository
from .router import router

__all__ = ["GestionarConflictosService", "ConflictoRepository", "router"]
