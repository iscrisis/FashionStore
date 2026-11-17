#!/usr/bin/env python3
"""
Script idempotente de poblamiento del dashboard.

Reutiliza EXACTAMENTE:
- SessionLocal de app.db.session
- Configuración DATABASE_URL
- Modelos ORM originales
- Estrategia de transacciones e idempotencia
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta, time, date
from decimal import Decimal
from random import randint, choice, sample
import logging

# Asegurar que app es importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Usar SessionLocal EXACTAMENTE como en la app
from app.db.session import SessionLocal
from sqlalchemy import select, func

# Importar TODOS los modelos (mismo patrón que create_all_script.py)
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P4_ReservasYAtencion.Models.reserva import Reserva, ReservaDetalle, EstadoReserva
from modules.P5_ComprasVentasYPagos.Models.venta import Venta, VentaDetalle, EstadoVenta
from modules.P5_ComprasVentasYPagos.Models.pago import Pago, EstadoPago, ProveedorPago
from modules.P5_ComprasVentasYPagos.Models.devolucion import DevolucionCambio, TipoOperacionDevolucion, MotivoDevolucion, EstadoReembolso


class DashboardDataPopulator:
    """Poblador idempotente del dashboard - integración exacta con arquitectura existente."""

    EMPRESA_ID = 1
    FECHA_INICIO = date(2026, 1, 1)
    FECHA_FIN = date(2026, 8, 31)

    def __init__(self):
        self.db = SessionLocal()
        self.stats = {
            "ventas_pagadas_convertidas": 0,
            "pagos_creados": 0,
            "pagos_sin_crear": 0,
            "reservas_creadas": 0,
            "reservas_duplicadas": 0,
            "detalles_reserva_creados": 0,
            "devoluciones_creadas": 0,
            "cambios_creados": 0,
            "errores": [],
        }

    def run(self):
        """Ejecuta el poblamiento completo de forma idempotente."""
        try:
            logger.info("=" * 70)
            logger.info("POBLAMIENTO DASHBOARD - ARQUITECTURA EXISTENTE")
            logger.info("=" * 70)

            self._convertir_ventas_a_pagadas()
            self._crear_reservas_con_estados()
            self._crear_devoluciones_cambios()
            self._verificar_integridad()

            logger.info("=" * 70)
            logger.info("RESUMEN FINAL")
            logger.info("=" * 70)
            self._imprimir_estadisticas()

            return True

        except Exception as e:
            logger.error(f"❌ Error fatal: {e}", exc_info=True)
            self.stats["errores"].append(str(e))
            return False
        finally:
            self.db.close()

    def _convertir_ventas_a_pagadas(self):
        """Convierte ventas PENDIENTE_PAGO en PAGADAS con pagos asociados."""
        logger.info("\n📋 Paso 1: Convertir ventas PENDIENTE_PAGO en PAGADAS...")

        try:
            # Obtener ventas sin pago confirmado
            stmt = (
                select(Venta)
                .where(
                    Venta.empresa_id == self.EMPRESA_ID,
                    Venta.estado == EstadoVenta.PENDIENTE_PAGO,
                )
                .order_by(Venta.id)
            )
            ventas_pendientes = list(self.db.execute(stmt).scalars().all())

            if not ventas_pendientes:
                logger.info("  ✓ No hay ventas pendientes para convertir")
                return

            logger.info(f"  Procesando {len(ventas_pendientes)} ventas pendientes...")

            for i, venta in enumerate(ventas_pendientes, 1):
                try:
                    # Verificar si ya tiene pago PAGADO (idempotencia)
                    stmt_pago = (
                        select(Pago)
                        .where(
                            Pago.venta_id == venta.id,
                            Pago.estado == EstadoPago.PAGADO,
                        )
                    )
                    pago_existente = self.db.execute(stmt_pago).scalar_one_or_none()

                    if pago_existente:
                        # Venta ya pagada, solo asegurar estado correcto
                        if venta.estado != EstadoVenta.PAGADA:
                            venta.estado = EstadoVenta.PAGADA
                            self.stats["ventas_pagadas_convertidas"] += 1
                        else:
                            self.stats["pagos_sin_crear"] += 1
                        continue

                    # Crear pago PAGADO (idempotencia: usar uuid_operacion_offline si existe)
                    uuid_operacion = f"pago-venta-{venta.id}-{self.EMPRESA_ID}"

                    stmt_check_uuid = (
                        select(Pago).where(
                            Pago.stripe_payment_intent_id == uuid_operacion
                        )
                    )
                    if self.db.execute(stmt_check_uuid).scalar_one_or_none():
                        # Pago ya existe
                        venta.estado = EstadoVenta.PAGADA
                        self.stats["pagos_sin_crear"] += 1
                        continue

                    # Crear nuevo pago
                    proveedor = choice([
                        ProveedorPago.STRIPE,
                        ProveedorPago.EFECTIVO,
                        ProveedorPago.TARJETA,
                        ProveedorPago.QR,
                    ])

                    fecha_pago = self._fecha_aleatoria(
                        venta.fecha_creacion.date(),
                        self.FECHA_FIN,
                    )

                    pago = Pago(
                        venta_id=venta.id,
                        proveedor=proveedor,
                        monto=venta.total,
                        estado=EstadoPago.PAGADO,
                        fecha_creacion=datetime.combine(
                            fecha_pago, time(randint(9, 20), randint(0, 59)), tzinfo=timezone.utc
                        ),
                        fecha_confirmacion=datetime.combine(
                            fecha_pago, time(randint(9, 21), randint(0, 59)), tzinfo=timezone.utc
                        ),
                        stripe_payment_intent_id=uuid_operacion,
                    )

                    # Campos opcionales por proveedor
                    if proveedor == ProveedorPago.EFECTIVO:
                        pago.monto_recibido = venta.total + Decimal(randint(0, 50))
                        pago.cambio = pago.monto_recibido - venta.total
                    elif proveedor == ProveedorPago.TARJETA:
                        pago.tipo_tarjeta = choice(["DEBITO", "CREDITO"])
                        pago.referencia = f"AUTH{randint(100000, 999999)}"

                    self.db.add(pago)
                    venta.estado = EstadoVenta.PAGADA

                    self.stats["pagos_creados"] += 1
                    self.stats["ventas_pagadas_convertidas"] += 1

                    if i % 10 == 0:
                        logger.info(f"    ↳ Procesadas {i}/{len(ventas_pendientes)} ventas...")

                except Exception as e:
                    logger.warning(f"  ⚠️ Error venta {venta.id}: {e}")
                    self.stats["errores"].append(f"Venta {venta.id}: {str(e)}")

            self.db.commit()
            logger.info(
                f"  ✓ Completado: "
                f"{self.stats['ventas_pagadas_convertidas']} ventas PAGADAS, "
                f"{self.stats['pagos_creados']} pagos nuevos"
            )

        except Exception as e:
            logger.error(f"  ❌ Error en conversión de ventas: {e}")
            self.db.rollback()
            raise

    def _crear_reservas_con_estados(self):
        """Crea reservas con diferentes estados para enriquecer reportes."""
        logger.info("\n📋 Paso 2: Crear reservas con diferentes estados...")

        try:
            # Obtener datos base
            stmt_clientes = (
                select(Usuario)
                .where(Usuario.empresa_id == self.EMPRESA_ID)
                .limit(50)
            )
            clientes = list(self.db.execute(stmt_clientes).scalars().all())

            stmt_sucursales = (
                select(Sucursal)
                .where(Sucursal.empresa_id == self.EMPRESA_ID)
            )
            sucursales = list(self.db.execute(stmt_sucursales).scalars().all())

            stmt_variantes = (
                select(ProductoVariante)
                .where(ProductoVariante.is_active.is_(True))
                .limit(100)
            )
            variantes = list(self.db.execute(stmt_variantes).scalars().all())

            if not clientes or not sucursales or not variantes:
                logger.warning("  ⚠️ Datos insuficientes para crear reservas")
                return

            logger.info(
                f"  Creando ~40 reservas con "
                f"clientes={len(clientes)}, "
                f"sucursales={len(sucursales)}, "
                f"variantes={len(variantes)}..."
            )

            estados = list(EstadoReserva)
            num_reservas = 40

            for i in range(1, num_reservas + 1):
                try:
                    # Verificar si ya existe (idempotencia)
                    codigo_reserva = f"RS-{self.EMPRESA_ID:02d}{i:05d}"
                    stmt_check = (
                        select(Reserva)
                        .where(Reserva.codigo_reserva == codigo_reserva)
                    )
                    if self.db.execute(stmt_check).scalar_one_or_none():
                        self.stats["reservas_duplicadas"] += 1
                        continue

                    # Crear reserva
                    fecha_res = self._fecha_aleatoria(self.FECHA_INICIO, self.FECHA_FIN)
                    hora_res = time(randint(9, 19), randint(0, 59))
                    estado = choice(estados)

                    reserva = Reserva(
                        empresa_id=self.EMPRESA_ID,
                        codigo_reserva=codigo_reserva,
                        cliente_id=choice(clientes).id,
                        sucursal_id=choice(sucursales).id,
                        fecha_reserva=fecha_res,
                        hora_inicio=hora_res,
                        estado_general=estado,
                        fecha_creacion=datetime.combine(
                            fecha_res, hora_res, tzinfo=timezone.utc
                        ),
                    )

                    self.db.add(reserva)
                    self.db.flush()

                    # Agregar detalles
                    num_detalles = randint(1, 3)
                    variantes_sel = sample(variantes, min(num_detalles, len(variantes)))

                    for variante in variantes_sel:
                        detalle = ReservaDetalle(
                            reserva_id=reserva.id,
                            producto_variante_id=variante.id,
                            cantidad=randint(1, 3),
                            estado=estado,
                        )
                        self.db.add(detalle)
                        self.stats["detalles_reserva_creados"] += 1

                    self.stats["reservas_creadas"] += 1

                    if i % 10 == 0:
                        logger.info(f"    ↳ Creadas {i}/{num_reservas} reservas...")

                except Exception as e:
                    logger.debug(f"  Reserva {i}: {e}")
                    self.stats["errores"].append(f"Reserva {i}: {str(e)}")

            self.db.commit()
            logger.info(
                f"  ✓ Completado: "
                f"{self.stats['reservas_creadas']} reservas, "
                f"{self.stats['detalles_reserva_creados']} detalles"
            )

        except Exception as e:
            logger.error(f"  ❌ Error en creación de reservas: {e}")
            self.db.rollback()
            raise

    def _crear_devoluciones_cambios(self):
        """Crea devoluciones y cambios basados en ventas pagadas."""
        logger.info("\n📋 Paso 3: Crear devoluciones y cambios...")

        try:
            # Obtener ventas pagadas
            stmt_ventas = (
                select(Venta)
                .where(
                    Venta.empresa_id == self.EMPRESA_ID,
                    Venta.estado == EstadoVenta.PAGADA,
                )
                .limit(60)
            )
            ventas = list(self.db.execute(stmt_ventas).scalars().all())

            # Obtener cajeros
            stmt_cajeros = (
                select(Usuario)
                .where(Usuario.empresa_id == self.EMPRESA_ID)
                .limit(10)
            )
            cajeros = list(self.db.execute(stmt_cajeros).scalars().all())

            if not ventas or not cajeros:
                logger.warning("  ⚠️ Datos insuficientes para crear devoluciones")
                return

            logger.info(f"  Creando devoluciones/cambios de {len(ventas)} ventas...")

            num_devoluciones_creadas = 0

            # Procesar ~15 ventas al azar para devoluciones/cambios
            for venta in sample(ventas, min(15, len(ventas))):
                try:
                    # Obtener detalles de la venta
                    stmt_detalles = (
                        select(VentaDetalle)
                        .where(VentaDetalle.venta_id == venta.id)
                    )
                    detalles = list(self.db.execute(stmt_detalles).scalars().all())

                    if not detalles:
                        continue

                    detalle = choice(detalles)
                    tipo = choice([
                        TipoOperacionDevolucion.DEVOLUCION,
                        TipoOperacionDevolucion.CAMBIO,
                    ])
                    cantidad = min(detalle.cantidad, randint(1, detalle.cantidad))

                    # Verificar idempotencia (usar uuid)
                    uuid_operacion = f"devolucion-{detalle.id}-{self.EMPRESA_ID}"

                    stmt_check_uuid = (
                        select(DevolucionCambio)
                        .where(
                            DevolucionCambio.venta_detalle_id == detalle.id,
                            DevolucionCambio.cantidad == cantidad,
                            DevolucionCambio.tipo == tipo,
                        )
                    )
                    if self.db.execute(stmt_check_uuid).scalar_one_or_none():
                        # Ya existe
                        continue

                    fecha_dev = self._fecha_aleatoria(
                        venta.fecha_creacion.date() + timedelta(days=1),
                        self.FECHA_FIN,
                    )

                    devolucion = DevolucionCambio(
                        venta_id=venta.id,
                        venta_detalle_id=detalle.id,
                        tipo=tipo,
                        cantidad=cantidad,
                        variante_original_id=detalle.producto_variante_id,
                        cajero_id=choice(cajeros).id,
                        sucursal_id=venta.sucursal_id,
                        fecha_creacion=datetime.combine(
                            fecha_dev, time(randint(9, 20), randint(0, 59)), tzinfo=timezone.utc
                        ),
                    )

                    # Campos específicos por tipo
                    if tipo == TipoOperacionDevolucion.DEVOLUCION:
                        devolucion.motivo = choice([
                            MotivoDevolucion.TALLA,
                            MotivoDevolucion.DEFECTO,
                            MotivoDevolucion.PRODUCTO_INCORRECTO,
                        ])
                        devolucion.monto_reembolso = detalle.precio_unitario * cantidad
                        devolucion.metodo_reembolso = choice([
                            ProveedorPago.EFECTIVO,
                            ProveedorPago.TARJETA,
                        ])
                        devolucion.estado_reembolso = EstadoReembolso.REGISTRADO
                        self.stats["devoluciones_creadas"] += 1
                    else:
                        self.stats["cambios_creados"] += 1

                    self.db.add(devolucion)
                    num_devoluciones_creadas += 1

                except Exception as e:
                    logger.debug(f"  Devolución venta {venta.id}: {e}")
                    self.stats["errores"].append(f"Devolución {venta.id}: {str(e)}")

            self.db.commit()
            logger.info(
                f"  ✓ Completado: "
                f"{self.stats['devoluciones_creadas']} devoluciones, "
                f"{self.stats['cambios_creados']} cambios"
            )

        except Exception as e:
            logger.error(f"  ❌ Error en creación de devoluciones: {e}")
            self.db.rollback()
            raise

    def _verificar_integridad(self):
        """Verifica integridad de datos en la base de datos."""
        logger.info("\n📋 Verificando integridad de datos...")

        try:
            # Contar registros finales
            ventas_pagadas = self.db.execute(
                select(func.count(Venta.id)).where(
                    Venta.empresa_id == self.EMPRESA_ID,
                    Venta.estado == EstadoVenta.PAGADA,
                )
            ).scalar()

            pagos_pagados = self.db.execute(
                select(func.count(Pago.id)).where(
                    Pago.estado == EstadoPago.PAGADO,
                )
            ).scalar()

            reservas = self.db.execute(
                select(func.count(Reserva.id)).where(
                    Reserva.empresa_id == self.EMPRESA_ID,
                )
            ).scalar()

            devoluciones = self.db.execute(
                select(func.count(DevolucionCambio.id)).where(
                    DevolucionCambio.tipo == TipoOperacionDevolucion.DEVOLUCION,
                )
            ).scalar()

            cambios = self.db.execute(
                select(func.count(DevolucionCambio.id)).where(
                    DevolucionCambio.tipo == TipoOperacionDevolucion.CAMBIO,
                )
            ).scalar()

            logger.info(f"  ✓ Ventas PAGADAS: {ventas_pagadas}")
            logger.info(f"  ✓ Pagos PAGADOS: {pagos_pagados}")
            logger.info(f"  ✓ Reservas: {reservas}")
            logger.info(f"  ✓ Devoluciones: {devoluciones}")
            logger.info(f"  ✓ Cambios: {cambios}")

        except Exception as e:
            logger.warning(f"  ⚠️ Error en verificación: {e}")

    def _fecha_aleatoria(self, inicio: date, fin: date) -> date:
        """Genera fecha aleatoria entre inicio y fin (inclusive)."""
        delta = (fin - inicio).days
        random_days = randint(0, delta)
        return inicio + timedelta(days=random_days)

    def _imprimir_estadisticas(self):
        """Imprime estadísticas del poblamiento."""
        logger.info(f"  Ventas convertidas a PAGADAS: {self.stats['ventas_pagadas_convertidas']}")
        logger.info(f"  Pagos creados: {self.stats['pagos_creados']}")
        logger.info(f"  Pagos sin crear (ya existían): {self.stats['pagos_sin_crear']}")
        logger.info(f"  Reservas creadas: {self.stats['reservas_creadas']}")
        logger.info(f"  Reservas duplicadas (no creadas): {self.stats['reservas_duplicadas']}")
        logger.info(f"  Detalles de reserva: {self.stats['detalles_reserva_creados']}")
        logger.info(f"  Devoluciones creadas: {self.stats['devoluciones_creadas']}")
        logger.info(f"  Cambios creados: {self.stats['cambios_creados']}")

        total_operaciones = (
            self.stats['ventas_pagadas_convertidas'] +
            self.stats['pagos_creados'] +
            self.stats['reservas_creadas'] +
            self.stats['devoluciones_creadas'] +
            self.stats['cambios_creados']
        )

        if self.stats['errores']:
            logger.warning(f"\n  ⚠️ Errores encontrados: {len(self.stats['errores'])}")
            for error in self.stats['errores'][:5]:
                logger.warning(f"    - {error}")

        logger.info(f"\n✅ TOTAL DE OPERACIONES: {total_operaciones}")
        logger.info("=" * 70)

        return total_operaciones


def main():
    """Punto de entrada del script."""
    try:
        populator = DashboardDataPopulator()
        success = populator.run()

        if success:
            logger.info("\n✅ POBLAMIENTO COMPLETADO EXITOSAMENTE")
            return 0
        else:
            logger.error("\n❌ POBLAMIENTO CON ERRORES")
            return 1

    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
