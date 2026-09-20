"""Acceso a datos de CU32 -- Gestionar promociones (Administrador).

Tabla propia: Promocion (+ la asociación pura `promocion_productos`, ver
Models/promocion.py). Reutiliza Producto (CU08) SOLO en lectura -- CU32
nunca crea, edita ni desactiva un Producto, solo lee cuáles están activos
para poder asociarlos a una promoción.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P6_InnovacionYAnalisis.Models.promocion import Promocion, promocion_productos


class PromocionRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self) -> list[Promocion]:
        stmt = (
            select(Promocion)
            .options(selectinload(Promocion.productos))
            .order_by(Promocion.fecha_creacion.desc(), Promocion.id.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def obtener_por_id(self, promocion_id: int) -> Promocion | None:
        stmt = (
            select(Promocion)
            .where(Promocion.id == promocion_id)
            .options(selectinload(Promocion.productos))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def obtener_por_id_bloqueado(self, promocion_id: int) -> Promocion | None:
        """SELECT ... FOR UPDATE -- editar()/desactivar() bloquean la fila
        antes de mutarla, mismo criterio ya usado en el resto del proyecto
        (ej. CU19/CU20/CU25/CU26), para que dos ediciones/desactivaciones
        concurrentes de la MISMA promoción nunca se pisen entre sí."""
        stmt = (
            select(Promocion)
            .where(Promocion.id == promocion_id)
            .options(selectinload(Promocion.productos))
            .with_for_update(of=Promocion)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def crear(self, promocion: Promocion) -> Promocion:
        self.db.add(promocion)
        self.db.commit()
        self.db.refresh(promocion)
        return promocion

    def guardar(self) -> None:
        self.db.commit()

    def existe_solapamiento(
        self,
        producto_ids: list[int],
        fecha_inicio: date,
        fecha_fin: date,
        excluir_promocion_id: int | None = None,
    ) -> bool:
        """True si ALGUNO de `producto_ids` ya tiene una promoción `activa`
        (bandera, no estado derivado -- una promoción que el Administrador
        ya desactivó nunca bloquea una nueva, aunque sus fechas se crucen)
        cuyo rango se superpone con [fecha_inicio, fecha_fin] -- overlap
        clásico de rangos inclusivos: A.inicio <= B.fin AND B.inicio <=
        A.fin. `excluir_promocion_id` es la propia promoción al editar (no
        debe chocar consigo misma)."""
        if not producto_ids:
            return False
        stmt = (
            select(func.count(func.distinct(promocion_productos.c.producto_id)))
            .select_from(
                promocion_productos.join(Promocion, Promocion.id == promocion_productos.c.promocion_id)
            )
            .where(
                promocion_productos.c.producto_id.in_(producto_ids),
                Promocion.activa.is_(True),
                Promocion.fecha_inicio <= fecha_fin,
                Promocion.fecha_fin >= fecha_inicio,
            )
        )
        if excluir_promocion_id is not None:
            stmt = stmt.where(Promocion.id != excluir_promocion_id)
        total = self.db.execute(stmt).scalar_one()
        return (total or 0) > 0


class ProductoLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_activos_by_ids(self, producto_ids: set[int]) -> dict[int, Producto]:
        if not producto_ids:
            return {}
        stmt = select(Producto).where(Producto.id.in_(producto_ids), Producto.is_active.is_(True))
        return {p.id: p for p in self.db.execute(stmt).scalars()}
