"""Pruebas de integración para CU11 — Sincronizar operaciones pendientes.

Requiere:
- PostgreSQL corriendo en localhost:5433 (contenedor Docker)
- Backend FastAPI corriendo en localhost:8000
- Base de datos: fashionstore_test

Ejecución:
    python -m pytest tests/test_cu11_integration.py -v -s
"""

import json
import os
import time
from datetime import date, datetime, time as time_type
from decimal import Decimal

import psycopg2
import requests
from psycopg2.extras import RealDictCursor, execute_values

# Configuración
DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
DB_PORT = os.getenv("TEST_DB_PORT", "5433")
DB_NAME = os.getenv("TEST_DB_NAME", "fashionstore_test")
DB_USER = os.getenv("TEST_DB_USER", "test_user")
DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "test_password_secure")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# Token de autenticación (mock para pruebas)
AUTH_TOKEN = "test_token_12345"
AUTH_HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}


class TestDB:
    """Conectar y ejecutar queries en PostgreSQL de pruebas."""

    def __init__(self):
        self.conn = None
        self.cursor = None

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
            print(f"✗ Error conectando a PostgreSQL: {e}")
            return False

    def setup_schema(self):
        """Crear esquema básico para pruebas."""
        try:
            # Crear tablas mínimas necesarias
            queries = [
                # Usuarios
                """CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE,
                    empresa_id INTEGER NOT NULL,
                    sucursal_id INTEGER,
                    rol VARCHAR(50)
                )""",
                # Empresas
                """CREATE TABLE IF NOT EXISTS empresas (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255)
                )""",
                # Sucursales
                """CREATE TABLE IF NOT EXISTS sucursales (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER,
                    nombre VARCHAR(255)
                )""",
                # Productos
                """CREATE TABLE IF NOT EXISTS productos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255),
                    activo BOOLEAN DEFAULT true
                )""",
                # ProductoVariantes
                """CREATE TABLE IF NOT EXISTS producto_variantes (
                    id SERIAL PRIMARY KEY,
                    producto_id INTEGER,
                    talla_id INTEGER,
                    color_id INTEGER,
                    activo BOOLEAN DEFAULT true
                )""",
                # Tallas
                """CREATE TABLE IF NOT EXISTS tallas (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(50)
                )""",
                # Colores
                """CREATE TABLE IF NOT EXISTS colores (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(50)
                )""",
                # Stock
                """CREATE TABLE IF NOT EXISTS stock_sucursal (
                    id SERIAL PRIMARY KEY,
                    sucursal_id INTEGER,
                    producto_variante_id INTEGER,
                    cantidad INTEGER DEFAULT 100,
                    stock_reservado INTEGER DEFAULT 0,
                    UNIQUE(sucursal_id, producto_variante_id)
                )""",
                # Ventas
                """CREATE TABLE IF NOT EXISTS ventas (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER,
                    sucursal_id INTEGER,
                    codigo_venta VARCHAR(50),
                    total DECIMAL(10,2),
                    uuid_operacion_offline VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                # VentaDetalles
                """CREATE TABLE IF NOT EXISTS venta_detalles (
                    id SERIAL PRIMARY KEY,
                    venta_id INTEGER,
                    producto_variante_id INTEGER,
                    cantidad INTEGER,
                    precio_unitario DECIMAL(10,2),
                    subtotal DECIMAL(10,2)
                )""",
                # Pagos
                """CREATE TABLE IF NOT EXISTS pagos (
                    id SERIAL PRIMARY KEY,
                    venta_id INTEGER UNIQUE,
                    metodo_pago VARCHAR(50),
                    monto_recibido DECIMAL(10,2),
                    estado VARCHAR(50) DEFAULT 'CONFIRMADO',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                # Reservas
                """CREATE TABLE IF NOT EXISTS reservas (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER,
                    sucursal_id INTEGER,
                    cliente_id INTEGER,
                    fecha_reserva DATE,
                    hora_inicio TIME,
                    estado_general VARCHAR(50),
                    uuid_operacion_offline VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                # ReservaDetalles
                """CREATE TABLE IF NOT EXISTS reserva_detalles (
                    id SERIAL PRIMARY KEY,
                    reserva_id INTEGER,
                    producto_variante_id INTEGER,
                    cantidad INTEGER,
                    estado VARCHAR(50) DEFAULT 'PENDIENTE'
                )""",
            ]
            for query in queries:
                self.cursor.execute(query)
            self.conn.commit()
            print("✓ Esquema creado/verificado")
            return True
        except Exception as e:
            print(f"✗ Error creando esquema: {e}")
            self.conn.rollback()
            return False

    def seed_data(self):
        """Insertar datos de prueba."""
        try:
            # Empresa
            self.cursor.execute(
                "INSERT INTO empresas (id, nombre) VALUES (100, 'Empresa Test') ON CONFLICT DO NOTHING"
            )

            # Sucursal
            self.cursor.execute(
                "INSERT INTO sucursales (id, empresa_id, nombre) VALUES (10, 100, 'Sucursal Test') ON CONFLICT DO NOTHING"
            )

            # Usuario Cliente
            self.cursor.execute(
                "INSERT INTO usuarios (id, email, empresa_id, sucursal_id, rol) VALUES (1, 'cliente@test.com', 100, 10, 'CLIENTE') ON CONFLICT DO NOTHING"
            )

            # Usuario Cajero
            self.cursor.execute(
                "INSERT INTO usuarios (id, email, empresa_id, sucursal_id, rol) VALUES (2, 'cajero@test.com', 100, 10, 'CAJERO') ON CONFLICT DO NOTHING"
            )

            # Producto
            self.cursor.execute(
                "INSERT INTO productos (id, nombre, activo) VALUES (50, 'Remera Test', true) ON CONFLICT DO NOTHING"
            )

            # Talla
            self.cursor.execute(
                "INSERT INTO tallas (id, nombre) VALUES (5, 'M') ON CONFLICT DO NOTHING"
            )

            # Color
            self.cursor.execute(
                "INSERT INTO colores (id, nombre) VALUES (3, 'Azul') ON CONFLICT DO NOTHING"
            )

            # ProductoVariante
            self.cursor.execute(
                "INSERT INTO producto_variantes (id, producto_id, talla_id, color_id, activo) VALUES (50, 50, 5, 3, true) ON CONFLICT DO NOTHING"
            )

            # Stock
            self.cursor.execute(
                "INSERT INTO stock_sucursal (id, sucursal_id, producto_variante_id, cantidad, stock_reservado) VALUES (50, 10, 50, 100, 0) ON CONFLICT DO NOTHING"
            )

            self.conn.commit()
            print("✓ Datos de prueba insertados")
            return True
        except Exception as e:
            print(f"✗ Error insertando datos: {e}")
            self.conn.rollback()
            return False

    def query(self, sql, params=None):
        """Ejecutar query SELECT."""
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"✗ Error en query: {e}")
            return []

    def close(self):
        """Cerrar conexión."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


class TestCU11:
    """Pruebas de integración para CU11."""

    def __init__(self):
        self.db = TestDB()
        self.results = []

    def setup(self):
        """Preparar ambiente de pruebas."""
        if not self.db.connect():
            return False
        if not self.db.setup_schema():
            return False
        if not self.db.seed_data():
            return False
        return True

    def test_1_sincronizar_venta_valida(self):
        """Prueba 1: Sincronizar una venta válida."""
        print("\n[TEST 1] Sincronizar venta válida...")

        payload = {
            "uuid": "uuid-venta-test-001",
            "tipo_operacion": "VENTA_OFFLINE",
            "empresa_id": 100,
            "sucursal_id": 10,
            "fecha_operacion_local": "2026-11-08T12:00:00Z",
            "detalles": [
                {
                    "producto_variante_id": 50,
                    "cantidad": 2,
                    "precio_unitario": 100.0,
                    "subtotal": 200.0,
                }
            ],
            "metodo_pago": "EFECTIVO",
            "monto_recibido": 250.0,
            "total": 200.0,
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/sincronizar/ventas",
                json=payload,
                headers=AUTH_HEADERS,
                timeout=10,
            )

            if response.status_code == 201:
                resultado = response.json()
                if resultado.get("estado") == "CONFIRMADA":
                    venta_id = resultado.get("venta_id")

                    # Verificar en DB
                    venta = self.db.query(
                        "SELECT * FROM ventas WHERE id = %s", (venta_id,)
                    )
                    if venta:
                        print(f"  ✓ Venta sincronizada: ID={venta_id}")
                        print(f"    UUID origen: {venta[0]['uuid_operacion_offline']}")
                        self.results.append(("test_1", True, f"Venta {venta_id}"))
                        return True
            print(f"  ✗ Response: {response.status_code} - {response.text}")
            self.results.append(("test_1", False, response.text[:100]))
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results.append(("test_1", False, str(e)))
        return False

    def test_2_sincronizar_reserva_valida(self):
        """Prueba 2: Sincronizar una reserva válida."""
        print("\n[TEST 2] Sincronizar reserva válida...")

        payload = {
            "uuid": "uuid-reserva-test-001",
            "tipo_operacion": "RESERVA_OFFLINE",
            "empresa_id": 100,
            "sucursal_id": 10,
            "cliente_id": 1,
            "fecha_reserva": "2026-11-15",
            "hora_inicio": "10:00",
            "detalles": [
                {
                    "producto_variante_id": 50,
                    "cantidad": 1,
                }
            ],
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/sincronizar/reservas",
                json=payload,
                headers=AUTH_HEADERS,
                timeout=10,
            )

            if response.status_code == 201:
                resultado = response.json()
                if resultado.get("estado") == "CONFIRMADA":
                    reserva_id = resultado.get("reserva_id")

                    # Verificar en DB
                    reserva = self.db.query(
                        "SELECT * FROM reservas WHERE id = %s", (reserva_id,)
                    )
                    if reserva:
                        print(f"  ✓ Reserva sincronizada: ID={reserva_id}")
                        print(f"    UUID origen: {reserva[0]['uuid_operacion_offline']}")
                        self.results.append(("test_2", True, f"Reserva {reserva_id}"))
                        return True
            print(f"  ✗ Response: {response.status_code} - {response.text}")
            self.results.append(("test_2", False, response.text[:100]))
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results.append(("test_2", False, str(e)))
        return False

    def test_3_idempotencia_uuid_duplicado(self):
        """Prueba 3: Idempotencia — UUID duplicado no crea duplicado."""
        print("\n[TEST 3] Idempotencia — Reenviar UUID duplicado...")

        payload = {
            "uuid": "uuid-venta-test-001",  # Mismo UUID de TEST 1
            "tipo_operacion": "VENTA_OFFLINE",
            "empresa_id": 100,
            "sucursal_id": 10,
            "fecha_operacion_local": "2026-11-08T12:00:00Z",
            "detalles": [
                {
                    "producto_variante_id": 50,
                    "cantidad": 2,
                    "precio_unitario": 100.0,
                    "subtotal": 200.0,
                }
            ],
            "metodo_pago": "EFECTIVO",
            "monto_recibido": 250.0,
            "total": 200.0,
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/sincronizar/ventas",
                json=payload,
                headers=AUTH_HEADERS,
                timeout=10,
            )

            if response.status_code == 201:
                resultado = response.json()
                if resultado.get("estado") == "CONFIRMADA":
                    # Verificar que el motivo es "idempotente"
                    if "idempotente" in resultado.get("motivo", "").lower():
                        # Contar ventas con este UUID
                        ventas = self.db.query(
                            "SELECT COUNT(*) as count FROM ventas WHERE uuid_operacion_offline = %s",
                            ("uuid-venta-test-001",),
                        )
                        if ventas and ventas[0]["count"] == 1:
                            print(
                                f"  ✓ Idempotencia verificada: 1 venta para UUID duplicado"
                            )
                            self.results.append(("test_3", True, "Idempotencia OK"))
                            return True
            print(f"  ✗ Response: {response.status_code} - {response.text}")
            self.results.append(("test_3", False, response.text[:100]))
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results.append(("test_3", False, str(e)))
        return False

    def test_4_stock_deducido_una_sola_vez(self):
        """Prueba 4: Stock deducido exactamente una vez."""
        print("\n[TEST 4] Stock deducido exactamente una vez...")

        # Stock antes
        stock_antes = self.db.query(
            "SELECT cantidad FROM stock_sucursal WHERE producto_variante_id = 50 AND sucursal_id = 10"
        )

        payload = {
            "uuid": "uuid-venta-test-deduccion",
            "tipo_operacion": "VENTA_OFFLINE",
            "empresa_id": 100,
            "sucursal_id": 10,
            "fecha_operacion_local": "2026-11-08T12:30:00Z",
            "detalles": [
                {
                    "producto_variante_id": 50,
                    "cantidad": 5,
                    "precio_unitario": 100.0,
                    "subtotal": 500.0,
                }
            ],
            "metodo_pago": "EFECTIVO",
            "monto_recibido": 500.0,
            "total": 500.0,
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/sincronizar/ventas",
                json=payload,
                headers=AUTH_HEADERS,
                timeout=10,
            )

            if response.status_code == 201:
                # Stock después
                stock_despues = self.db.query(
                    "SELECT cantidad FROM stock_sucursal WHERE producto_variante_id = 50 AND sucursal_id = 10"
                )

                if stock_antes and stock_despues:
                    diferencia = (
                        stock_antes[0]["cantidad"] - stock_despues[0]["cantidad"]
                    )
                    print(
                        f"  Stock antes: {stock_antes[0]['cantidad']}, después: {stock_despues[0]['cantidad']}"
                    )
                    print(f"  Diferencia: {diferencia}")

                    if diferencia == 5:
                        print(f"  ✓ Stock deducido correctamente (5 unidades)")
                        self.results.append(
                            ("test_4", True, f"Stock -5 correctamente")
                        )
                        return True
                    else:
                        print(f"  ✗ Stock no coincide: esperado 5, obtenido {diferencia}")
                        self.results.append(
                            ("test_4", False, f"Stock mal: {diferencia}")
                        )
            print(f"  ✗ Response: {response.status_code} - {response.text}")
            self.results.append(("test_4", False, response.text[:100]))
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results.append(("test_4", False, str(e)))
        return False

    def print_results(self):
        """Imprimir resumen de resultados."""
        print("\n" + "=" * 60)
        print("RESUMEN DE PRUEBAS DE INTEGRACIÓN CU11")
        print("=" * 60)

        passed = sum(1 for _, result, _ in self.results if result)
        total = len(self.results)

        for test, result, detail in self.results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status} - {test}: {detail}")

        print(f"\nTotal: {passed}/{total} pruebas aprobadas")
        print("=" * 60)

        return passed == total

    def cleanup(self):
        """Limpiar."""
        self.db.close()


def main():
    """Ejecutar suite de pruebas."""
    print("Iniciando pruebas de integración CU11...")
    print(f"PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"API: {API_BASE_URL}")

    test = TestCU11()

    if not test.setup():
        print("✗ No se pudo preparar el ambiente de pruebas")
        return False

    # Ejecutar pruebas
    test.test_1_sincronizar_venta_valida()
    time.sleep(1)
    test.test_2_sincronizar_reserva_valida()
    time.sleep(1)
    test.test_3_idempotencia_uuid_duplicado()
    time.sleep(1)
    test.test_4_stock_deducido_una_sola_vez()

    # Resultados
    success = test.print_results()
    test.cleanup()

    return success


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)
