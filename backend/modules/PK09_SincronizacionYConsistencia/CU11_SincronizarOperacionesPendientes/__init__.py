"""CU11 — Sincronizar operaciones pendientes (Cajero, Cliente).

Permite que operaciones offline (reservas y ventas presenciales registradas en
IndexedDB) se envíen a FastAPI, se validen y se persistan en PostgreSQL de forma
transaccional, sin duplicaciones, con idempotencia garantizada.

Reutiliza las reglas de negocio de CU24 (venta presencial) y CU25 (pago presencial).
"""

from .router import router

__all__ = ["router"]
