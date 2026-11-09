"""Pruebas de integración CU11 accediendo directamente a PostgreSQL.

Este script verifica que la BD está correctamente esquematizada y que
las operaciones de sincronización pueden funcionar correctamente.

Ejecución:
    python tests/test_cu11_db_direct.py
"""

import os
import sys
from datetime import date, time

# Configuración PostgreSQL de pruebas
DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
DB_PORT = os.getenv("TEST_DB_PORT", "5433")
DB_NAME = os.getenv("TEST_DB_NAME", "fashionstore_test")
DB_USER = os.getenv("TEST_DB_USER", "test_user")
DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "test_password_secure")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("✗ psycopg2 no instalado. Instalar con: pip install psycopg2-binary")
    sys.exit(1)


class TestCU11DB:
    """Pruebas directas a PostgreSQL para CU11."""

    def __init__(self):
        self.conn = None
        self.cursor = None
        self.results = []

    def connect(self):
        """Conectar a PostgreSQL."""
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=5,
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print(f"✓ Conectado a PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
            return True
        except Exception as e:
            print(f"✗ Error conectando: {e}")
            return False

    def setup_schema(self):
        """Crear esquema para pruebas."""
        try:
            queries = [
                "CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE, empresa_id INTEGER, sucursal_id INTEGER, rol VARCHAR(50))",
                "CREATE TABLE IF NOT EXISTS empresas (id SERIAL PRIMARY KEY, nombre VARCHAR(255))",
                "CREATE TABLE IF NOT EXISTS sucursales (id SERIAL PRIMARY KEY, empresa_id INTEGER, nombre VARCHAR(255))",
                "CREATE TABLE IF NOT EXISTS productos (id SERIAL PRIMARY KEY, nombre VARCHAR(255), activo BOOLEAN DEFAULT true)",
                "CREATE TABLE IF NOT EXISTS tallas (id SERIAL PRIMARY KEY, nombre VARCHAR(50))",
                "CREATE TABLE IF NOT EXISTS colores (id SERIAL PRIMARY KEY, nombre VARCHAR(50))",
                "CREATE TABLE IF NOT EXISTS producto_variantes (id SERIAL PRIMARY KEY, producto_id INTEGER, talla_id INTEGER, color_id INTEGER, activo BOOLEAN DEFAULT true)",
                "CREATE TABLE IF NOT EXISTS stock_sucursal (id SERIAL PRIMARY KEY, sucursal_id INTEGER, producto_variante_id INTEGER, cantidad INTEGER DEFAULT 100, stock_reservado INTEGER DEFAULT 0, UNIQUE(sucursal_id, producto_variante_id))",
                "CREATE TABLE IF NOT EXISTS ventas (id SERIAL PRIMARY KEY, empresa_id INTEGER, sucursal_id INTEGER, codigo_venta VARCHAR(50), total DECIMAL(10,2), uuid_operacion_offline VARCHAR(255) UNIQUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS venta_detalles (id SERIAL PRIMARY KEY, venta_id INTEGER, producto_variante_id INTEGER, cantidad INTEGER, precio_unitario DECIMAL(10,2), subtotal DECIMAL(10,2))",
                "CREATE TABLE IF NOT EXISTS pagos (id SERIAL PRIMARY KEY, venta_id INTEGER UNIQUE, metodo_pago VARCHAR(50), monto_recibido DECIMAL(10,2), estado VARCHAR(50) DEFAULT 'CONFIRMADO', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS reservas (id SERIAL PRIMARY KEY, empresa_id INTEGER, sucursal_id INTEGER, cliente_id INTEGER, fecha_reserva DATE, hora_inicio TIME, estado_general VARCHAR(50), uuid_operacion_offline VARCHAR(255) UNIQUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS reserva_detalles (id SERIAL PRIMARY KEY, reserva_id INTEGER, producto_variante_id INTEGER, cantidad INTEGER, estado VARCHAR(50) DEFAULT 'PENDIENTE')",
            ]

            for query in queries:
                self.cursor.execute(query)
            self.conn.commit()
            print("✓ Esquema creado")
            return True
        except Exception as e:
            print(f"✗ Error en schema: {e}")
            self.conn.rollback()
            return False

    def seed_data(self):
        """Insertar datos de prueba."""
        try:
            # Limpiar tablas primero
            tables = [
                "venta_detalles",
                "pagos",
                "ventas",
                "reserva_detalles",
                "reservas",
                "stock_sucursal",
                "producto_variantes",
                "tallas",
                "colores",
                "productos",
                "sucursales",
                "empresas",
                "usuarios",
            ]
            for table in tables:
                self.cursor.execute(f"TRUNCATE TABLE {table} CASCADE")

            # Insertar datos
            self.cursor.execute(
                "INSERT INTO empresas (id, nombre) VALUES (100, 'Empresa Test')"
            )
            self.cursor.execute(
                "INSERT INTO sucursales (id, empresa_id, nombre) VALUES (10, 100, 'Sucursal Test')"
            )
            self.cursor.execute(
                "INSERT INTO usuarios (id, email, empresa_id, sucursal_id, rol) VALUES (1, 'cliente@test.com', 100, 10, 'CLIENTE')"
            )
            self.cursor.execute(
                "INSERT INTO productos (id, nombre, activo) VALUES (50, 'Remera Test', true)"
            )
            self.cursor.execute(
                "INSERT INTO tallas (id, nombre) VALUES (5, 'M')"
            )
            self.cursor.execute(
                "INSERT INTO colores (id, nombre) VALUES (3, 'Azul')"
            )
            self.cursor.execute(
                "INSERT INTO producto_variantes (id, producto_id, talla_id, color_id, activo) VALUES (50, 50, 5, 3, true)"
            )
            self.cursor.execute(
                "INSERT INTO stock_sucursal (sucursal_id, producto_variante_id, cantidad, stock_reservado) VALUES (10, 50, 100, 0)"
            )

            self.conn.commit()
            print("✓ Datos insertados")
            return True
        except Exception as e:
            print(f"✗ Error insertando datos: {e}")
            self.conn.rollback()
            return False

    def test_1_insertar_venta_con_uuid(self):
        """TEST 1: Insertar venta con UUID de sincronización."""
        print("\n[TEST 1] Insertar venta con UUID de sincronización...")

        try:
            # Simular lo que haría CU24
            self.cursor.execute(
                """INSERT INTO ventas
                   (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline)
                   VALUES (100, 10, 'V-001', 200.00, 'uuid-venta-test-001')
                   RETURNING id"""
            )
            venta_id = self.cursor.fetchone()["id"]

            # Insertar detalles
            self.cursor.execute(
                """INSERT INTO venta_detalles
                   (venta_id, producto_variante_id, cantidad, precio_unitario, subtotal)
                   VALUES (%s, 50, 2, 100.00, 200.00)""",
                (venta_id,),
            )

            # Simular lo que haría CU25 - insertar pago
            self.cursor.execute(
                """INSERT INTO pagos
                   (venta_id, metodo_pago, monto_recibido, estado)
                   VALUES (%s, 'EFECTIVO', 250.00, 'CONFIRMADO')""",
                (venta_id,),
            )

            # Deducir stock
            self.cursor.execute(
                """UPDATE stock_sucursal
                   SET cantidad = cantidad - 2
                   WHERE sucursal_id = 10 AND producto_variante_id = 50"""
            )

            self.conn.commit()

            # Verificar
            self.cursor.execute(
                "SELECT * FROM ventas WHERE id = %s", (venta_id,)
            )
            venta = self.cursor.fetchone()

            self.cursor.execute(
                "SELECT * FROM pagos WHERE venta_id = %s", (venta_id,)
            )
            pago = self.cursor.fetchone()

            if venta and pago and venta["uuid_operacion_offline"] == "uuid-venta-test-001":
                print(f"  ✓ Venta ID {venta_id} insertada con UUID")
                print(f"    UUID: {venta['uuid_operacion_offline']}")
                print(f"    Pago confirmado: {pago['estado']}")
                self.results.append(("test_1", True, f"Venta {venta_id}"))
                return True
            else:
                print(f"  ✗ Datos inconsistentes")
                self.results.append(("test_1", False, "Datos incompletos"))
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.conn.rollback()
            self.results.append(("test_1", False, str(e)))
            return False

    def test_2_idempotencia_uuid_unico(self):
        """TEST 2: Constraint UNIQUE en uuid_operacion_offline previene duplicados."""
        print("\n[TEST 2] UNIQUE constraint previene UUID duplicado...")

        try:
            # Intentar insertar venta con UUID duplicado
            try:
                self.cursor.execute(
                    """INSERT INTO ventas
                       (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline)
                       VALUES (100, 10, 'V-002', 300.00, 'uuid-venta-test-001')"""
                )
                self.conn.commit()
                print("  ✗ No hay UNIQUE constraint (permitió duplicado)")
                self.results.append(("test_2", False, "UNIQUE missing"))
                return False
            except psycopg2.IntegrityError:
                self.conn.rollback()
                # Esto es lo esperado
                print("  ✓ UNIQUE constraint rechazó UUID duplicado")

            # Verificar que solo existe una venta con ese UUID
            self.cursor.execute(
                "SELECT COUNT(*) as count FROM ventas WHERE uuid_operacion_offline = 'uuid-venta-test-001'"
            )
            count = self.cursor.fetchone()["count"]

            if count == 1:
                print(f"  ✓ Idempotencia garantizada: 1 venta para UUID")
                self.results.append(("test_2", True, "Idempotencia OK"))
                return True
            else:
                print(f"  ✗ Count incorrecto: {count}")
                self.results.append(("test_2", False, f"Count={count}"))
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.conn.rollback()
            self.results.append(("test_2", False, str(e)))
            return False

    def test_3_stock_deducido(self):
        """TEST 3: Stock se descuenta exactamente una vez."""
        print("\n[TEST 3] Stock deducido exactamente una vez...")

        try:
            # Stock inicial
            stock_antes = self.cursor.execute(
                "SELECT cantidad FROM stock_sucursal WHERE sucursal_id = 10 AND producto_variante_id = 50"
            ).fetchone()["cantidad"]
            print(f"  Stock antes: {stock_antes}")

            # Simular segunda venta
            self.cursor.execute(
                """INSERT INTO ventas
                   (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline)
                   VALUES (100, 10, 'V-003', 500.00, 'uuid-venta-test-deduccion')
                   RETURNING id"""
            )
            venta_id2 = self.cursor.fetchone()["id"]

            # Deducir stock por 5 unidades
            self.cursor.execute(
                """UPDATE stock_sucursal
                   SET cantidad = cantidad - 5
                   WHERE sucursal_id = 10 AND producto_variante_id = 50"""
            )

            self.conn.commit()

            # Stock después
            stock_despues = self.cursor.execute(
                "SELECT cantidad FROM stock_sucursal WHERE sucursal_id = 10 AND producto_variante_id = 50"
            ).fetchone()["cantidad"]
            print(f"  Stock después: {stock_despues}")

            diferencia = stock_antes - stock_despues
            print(f"  Diferencia: {diferencia}")

            if diferencia == 5:
                print(f"  ✓ Stock deducido correctamente")
                self.results.append(("test_3", True, f"Stock -{diferencia}"))
                return True
            else:
                print(f"  ✗ Stock incorrecto: esperado 5, obtenido {diferencia}")
                self.results.append(("test_3", False, f"Stock-{diferencia}"))
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.conn.rollback()
            self.results.append(("test_3", False, str(e)))
            return False

    def test_4_insertar_reserva(self):
        """TEST 4: Insertar reserva con UUID de sincronización."""
        print("\n[TEST 4] Insertar reserva con UUID de sincronización...")

        try:
            # Simular lo que haría CU17
            self.cursor.execute(
                """INSERT INTO reservas
                   (empresa_id, sucursal_id, cliente_id, fecha_reserva, hora_inicio, estado_general, uuid_operacion_offline)
                   VALUES (100, 10, 1, '2026-11-15', '10:00', 'PENDIENTE', 'uuid-reserva-test-001')
                   RETURNING id"""
            )
            reserva_id = self.cursor.fetchone()["id"]

            # Insertar detalle
            self.cursor.execute(
                """INSERT INTO reserva_detalles
                   (reserva_id, producto_variante_id, cantidad, estado)
                   VALUES (%s, 50, 1, 'PENDIENTE')""",
                (reserva_id,),
            )

            # Incrementar stock_reservado
            self.cursor.execute(
                """UPDATE stock_sucursal
                   SET stock_reservado = stock_reservado + 1
                   WHERE sucursal_id = 10 AND producto_variante_id = 50"""
            )

            self.conn.commit()

            # Verificar
            reserva = self.cursor.execute(
                "SELECT * FROM reservas WHERE id = %s", (reserva_id,)
            ).fetchone()

            if (
                reserva
                and reserva["uuid_operacion_offline"] == "uuid-reserva-test-001"
            ):
                print(f"  ✓ Reserva ID {reserva_id} insertada con UUID")
                print(
                    f"    Fecha: {reserva['fecha_reserva']}, Hora: {reserva['hora_inicio']}"
                )
                self.results.append(("test_4", True, f"Reserva {reserva_id}"))
                return True
            else:
                print(f"  ✗ Datos inconsistentes")
                self.results.append(("test_4", False, "Datos incompletos"))
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.conn.rollback()
            self.results.append(("test_4", False, str(e)))
            return False

    def test_5_rollback_transaccion(self):
        """TEST 5: Rollback en caso de error."""
        print("\n[TEST 5] Rollback de transacción en caso de error...")

        try:
            # Contar ventas antes
            ventas_antes = self.cursor.execute(
                "SELECT COUNT(*) as count FROM ventas"
            ).fetchone()["count"]

            try:
                # Iniciar transacción
                self.cursor.execute("BEGIN")

                # Insertar venta
                self.cursor.execute(
                    """INSERT INTO ventas
                       (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline)
                       VALUES (100, 10, 'V-ERROR', 100.00, 'uuid-venta-rollback-test')"""
                )

                # Simular error (violar constraint UNIQUE deliberadamente)
                self.cursor.execute(
                    """INSERT INTO ventas
                       (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline)
                       VALUES (100, 10, 'V-ERROR2', 100.00, 'uuid-venta-rollback-test')"""
                )

                self.cursor.execute("COMMIT")
            except psycopg2.IntegrityError:
                # Rollback
                self.cursor.execute("ROLLBACK")

            # Contar ventas después
            ventas_despues = self.cursor.execute(
                "SELECT COUNT(*) as count FROM ventas"
            ).fetchone()["count"]

            if ventas_despues == ventas_antes:
                print(f"  ✓ Rollback funcionó: ventas {ventas_antes} -> {ventas_despues}")
                self.results.append(("test_5", True, "Rollback OK"))
                return True
            else:
                print(
                    f"  ✗ Rollback no funcionó: ventas {ventas_antes} -> {ventas_despues}"
                )
                self.results.append(
                    ("test_5", False, f"Ventas {ventas_despues} (no rollback)")
                )
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results.append(("test_5", False, str(e)))
            return False

    def print_results(self):
        """Imprimir resultados."""
        print("\n" + "=" * 70)
        print("RESUMEN DE PRUEBAS DIRECTAS A POSTGRESQL CU11")
        print("=" * 70)

        passed = sum(1 for _, result, _ in self.results if result)
        total = len(self.results)

        for test, result, detail in self.results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status} - {test}: {detail}")

        print(f"\nTotal: {passed}/{total} pruebas aprobadas\n")

        if passed == total:
            print("✓ TODAS LAS PRUEBAS PASARON")
            print("\nPostgreSQL está configurado correctamente para CU11:")
            print("  • Tablas creadas con esquema correcto")
            print("  • UUID UNIQUE constraints previenen duplicados (idempotencia)")
            print("  • Stock se puede deducir/reservar correctamente")
            print("  • Transacciones y rollback funcionan")
        else:
            print("✗ ALGUNAS PRUEBAS FALLARON")

        print("=" * 70)
        return passed == total

    def cleanup(self):
        """Cerrar conexión."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    """Ejecutar pruebas."""
    print("Pruebas directas de PostgreSQL para CU11")
    print(f"Conectando a: {DB_HOST}:{DB_PORT}/{DB_NAME}\n")

    test = TestCU11DB()

    if not test.connect():
        return False

    if not test.setup_schema():
        test.cleanup()
        return False

    if not test.seed_data():
        test.cleanup()
        return False

    # Ejecutar pruebas
    test.test_1_insertar_venta_con_uuid()
    test.test_2_idempotencia_uuid_unico()
    test.test_3_stock_deducido()
    test.test_4_insertar_reserva()
    test.test_5_rollback_transaccion()

    success = test.print_results()
    test.cleanup()

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
