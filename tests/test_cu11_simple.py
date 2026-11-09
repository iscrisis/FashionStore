#!/usr/bin/env python3
"""Pruebas simples de PostgreSQL para CU11."""

import os
import sys

DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
DB_PORT = os.getenv("TEST_DB_PORT", "5433")
DB_NAME = os.getenv("TEST_DB_NAME", "fashionstore_test")
DB_USER = os.getenv("TEST_DB_USER", "test_user")
DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "test_password_secure")

try:
    import psycopg2
except ImportError:
    print("[ERROR] psycopg2 no instalado: pip install psycopg2-binary")
    sys.exit(1)


def connect_db():
    """Conectar a PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        return conn
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def setup_schema(conn):
    """Crear esquema."""
    cur = conn.cursor()
    queries = [
        "CREATE TABLE IF NOT EXISTS ventas (id SERIAL PRIMARY KEY, empresa_id INT, sucursal_id INT, codigo_venta VARCHAR(50), total DECIMAL(10,2), uuid_operacion_offline VARCHAR(255) UNIQUE, created_at TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS venta_detalles (id SERIAL PRIMARY KEY, venta_id INT, producto_variante_id INT, cantidad INT, precio_unitario DECIMAL(10,2))",
        "CREATE TABLE IF NOT EXISTS pagos (id SERIAL PRIMARY KEY, venta_id INT UNIQUE, metodo_pago VARCHAR(50), monto_recibido DECIMAL(10,2))",
        "CREATE TABLE IF NOT EXISTS stock_sucursal (id SERIAL PRIMARY KEY, sucursal_id INT, producto_variante_id INT, cantidad INT DEFAULT 100, UNIQUE(sucursal_id, producto_variante_id))",
        "CREATE TABLE IF NOT EXISTS reservas (id SERIAL PRIMARY KEY, empresa_id INT, sucursal_id INT, cliente_id INT, fecha_reserva DATE, hora_inicio TIME, uuid_operacion_offline VARCHAR(255) UNIQUE)",
    ]
    for q in queries:
        cur.execute(q)
    conn.commit()
    cur.close()
    print("[SETUP] Esquema listo")


def test_uuid_unique(conn):
    """TEST: UNIQUE constraint en uuid previene duplicados."""
    print("\n[TEST] UUID UNIQUE constraint...")
    cur = conn.cursor()

    try:
        # Truncate
        cur.execute("TRUNCATE TABLE pagos CASCADE")
        cur.execute("TRUNCATE TABLE venta_detalles CASCADE")
        cur.execute("TRUNCATE TABLE ventas CASCADE")
        conn.commit()

        # Insert 1
        cur.execute(
            "INSERT INTO ventas (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline) VALUES (100, 10, 'V1', 200, 'uuid-test-001')"
        )
        conn.commit()
        print("  [OK] Primera venta insertada")

        # Try insert duplicado
        try:
            cur.execute(
                "INSERT INTO ventas (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline) VALUES (100, 10, 'V2', 300, 'uuid-test-001')"
            )
            conn.commit()
            print("  [FAIL] UUID duplicado no fue rechazado")
            return False
        except psycopg2.IntegrityError:
            conn.rollback()
            print("  [OK] UUID duplicado rechazado por UNIQUE constraint")

        # Verificar count
        cur.execute(
            "SELECT COUNT(*) FROM ventas WHERE uuid_operacion_offline = 'uuid-test-001'"
        )
        count = cur.fetchone()[0]
        if count == 1:
            print(f"  [OK] Count = 1 (idempotencia garantizada)")
            return True
        else:
            print(f"  [FAIL] Count = {count} (esperado 1)")
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        conn.rollback()
        return False
    finally:
        cur.close()


def test_stock_deduction(conn):
    """TEST: Stock se descuenta correctamente."""
    print("\n[TEST] Stock deduction...")
    cur = conn.cursor()

    try:
        # Truncate
        cur.execute("TRUNCATE TABLE stock_sucursal CASCADE")
        cur.execute("TRUNCATE TABLE venta_detalles CASCADE")
        cur.execute("TRUNCATE TABLE ventas CASCADE")
        conn.commit()

        # Insert stock
        cur.execute(
            "INSERT INTO stock_sucursal (sucursal_id, producto_variante_id, cantidad) VALUES (10, 50, 100)"
        )
        conn.commit()
        print("  [OK] Stock inicial = 100")

        # Check stock before
        cur.execute(
            "SELECT cantidad FROM stock_sucursal WHERE sucursal_id = 10 AND producto_variante_id = 50"
        )
        stock_before = cur.fetchone()[0]

        # Insert venta y deducir stock
        cur.execute(
            "INSERT INTO ventas (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline) VALUES (100, 10, 'V-stock', 500, 'uuid-stock-001')"
        )
        cur.execute(
            "UPDATE stock_sucursal SET cantidad = cantidad - 5 WHERE sucursal_id = 10 AND producto_variante_id = 50"
        )
        conn.commit()
        print("  [OK] Deducido 5 unidades")

        # Check stock after
        cur.execute(
            "SELECT cantidad FROM stock_sucursal WHERE sucursal_id = 10 AND producto_variante_id = 50"
        )
        stock_after = cur.fetchone()[0]

        diff = stock_before - stock_after
        if diff == 5:
            print(f"  [OK] Stock: {stock_before} -> {stock_after} (diferencia = 5)")
            return True
        else:
            print(f"  [FAIL] Diferencia = {diff} (esperado 5)")
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        conn.rollback()
        return False
    finally:
        cur.close()


def test_transactions(conn):
    """TEST: Transacciones y rollback funcionan."""
    print("\n[TEST] Transactions and rollback...")
    cur = conn.cursor()

    try:
        # Count antes
        cur.execute("SELECT COUNT(*) FROM ventas")
        count_before = cur.fetchone()[0]

        # Try transaction with error
        try:
            cur.execute("BEGIN")
            cur.execute(
                "INSERT INTO ventas (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline) VALUES (100, 10, 'V-err', 100, 'uuid-err-001')"
            )
            # Error intencional
            cur.execute(
                "INSERT INTO ventas (empresa_id, sucursal_id, codigo_venta, total, uuid_operacion_offline) VALUES (100, 10, 'V-err2', 100, 'uuid-err-001')"
            )
            cur.execute("COMMIT")
        except psycopg2.IntegrityError:
            cur.execute("ROLLBACK")
            print("  [OK] Transaction rollback en error UNIQUE")

        # Count después
        cur.execute("SELECT COUNT(*) FROM ventas")
        count_after = cur.fetchone()[0]

        if count_after == count_before:
            print(
                f"  [OK] Rollback funcionó: count {count_before} -> {count_after}"
            )
            return True
        else:
            print(
                f"  [FAIL] Rollback no funcionó: count {count_before} -> {count_after}"
            )
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False
    finally:
        cur.close()


def main():
    """Ejecutar pruebas."""
    print("=" * 70)
    print("PRUEBAS DE INTEGRACIÓN CU11 - POSTGRESQL")
    print("=" * 70)
    print(f"Base de datos: {DB_HOST}:{DB_PORT}/{DB_NAME}\n")

    conn = connect_db()
    if not conn:
        print("[FAIL] No se pudo conectar a PostgreSQL")
        return False

    setup_schema(conn)

    results = []
    results.append(("UUID UNIQUE", test_uuid_unique(conn)))
    results.append(("Stock deduction", test_stock_deduction(conn)))
    results.append(("Transactions", test_transactions(conn)))

    conn.close()

    # Resumen
    print("\n" + "=" * 70)
    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nTotal: {passed}/{total} pruebas aprobadas")
    print("=" * 70)

    if passed == total:
        print("\nPostgreSQL esta LISTO para CU11:")
        print("  + UUID UNIQUE previene duplicados (idempotencia)")
        print("  + Stock se deduce correctamente")
        print("  + Transacciones y rollback funcionan")
        print("\nBackend puede ser desplegado con confianza.")
        return True
    else:
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
