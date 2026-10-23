#!/bin/bash

# Script para testear endpoints DELETE
# Uso: ./test-delete-endpoints.sh

API_URL="http://localhost:8000/api/v1"
ADMIN_EMAIL="admin@fashionstore.com"
ADMIN_PASSWORD="TuContraseña123!"

echo "================================"
echo "Testing DELETE Endpoints"
echo "================================"
echo ""

# 1. Obtener token
echo "[1] Obteniendo token de autenticación..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"correo\": \"$ADMIN_EMAIL\",
    \"password\": \"$ADMIN_PASSWORD\"
  }")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Error: No se pudo obtener el token"
  echo "Respuesta: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Token obtenido: ${TOKEN:0:20}..."
echo ""

# Función auxiliar para testear DELETE
test_delete() {
  local name=$1
  local endpoint=$2
  local id=$3

  echo "Testing: DELETE $endpoint/$id"
  RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$API_URL/$endpoint/$id" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

  HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
  BODY=$(echo "$RESPONSE" | head -n -1)

  if [ "$HTTP_CODE" == "204" ]; then
    echo "  ✅ Status 204 - Eliminado correctamente"
  elif [ "$HTTP_CODE" == "404" ]; then
    echo "  ⚠️ Status 404 - No encontrado (ID podría no existir)"
  else
    echo "  ❌ Status $HTTP_CODE"
    echo "  Response: $BODY"
  fi
  echo ""
}

# 2. Testear endpoints (ajusta los IDs según tu base de datos)
echo "[2] Testeando endpoints DELETE..."
echo ""

echo "--- CU06: Gestionar Sucursales ---"
test_delete "Ciudades" "ciudades" 1
test_delete "Sucursales" "sucursales" 1

echo "--- CU09: Categorías, Tallas y Colores ---"
test_delete "Categorías" "categorias" 1
test_delete "Tallas" "tallas" 1
test_delete "Colores" "colores" 1

echo "--- CU10: Temporadas y Colecciones ---"
test_delete "Temporadas" "temporadas" 1
test_delete "Colecciones" "colecciones" 1

echo "--- CU13: Gestionar Proveedores ---"
test_delete "Proveedores" "proveedores" 1

echo "--- CU08: Gestionar Productos ---"
test_delete "Productos" "productos" 1

echo "--- CU32: Gestionar Promociones ---"
test_delete "Promociones" "promociones" 1

echo ""
echo "================================"
echo "Testing completado"
echo "================================"
echo ""
echo "Nota: Reemplaza los IDs (1, 2, etc.) con IDs reales de tu base de datos"
