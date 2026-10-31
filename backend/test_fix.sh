#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"
ADMIN1_EMAIL="admin@fashionstore.com"
ADMIN1_PASS="password"
ADMIN2_EMAIL="cristelvicente981@gmail.com"
ADMIN2_PASS="12345678"

echo "==============================================="
echo "TEST 1: CREAR SUCURSAL (Empresa A)"
echo "==============================================="

LOGIN_RESP=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"correo\":\"$ADMIN1_EMAIL\",\"password\":\"$ADMIN1_PASS\"}")

TOKEN1=$(echo "$LOGIN_RESP" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token Admin 1: ${TOKEN1:0:30}..."

echo ""
echo "Crear Ciudad..."
CIUDAD_RESP=$(curl -s -X POST "$BASE_URL/ciudades" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN1" \
  -d '{"nombre":"Bogotá","departamento":"Cundinamarca","is_active":true}')

CIUDAD_ID=$(echo "$CIUDAD_RESP" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo "Ciudad ID: $CIUDAD_ID"

echo ""
echo "Crear Sucursal..."
SUCURSAL_RESP=$(curl -s -X POST "$BASE_URL/sucursales" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN1" \
  -d "{\"nombre\":\"Centro Bogotá\",\"ciudad_id\":$CIUDAD_ID,\"direccion\":\"Calle 50\",\"telefono\":\"+57\",\"is_active\":true}")

echo "Response:"
echo "$SUCURSAL_RESP" | head -c 500
echo ""
echo ""

if echo "$SUCURSAL_RESP" | grep -q '"id":'; then
    SUCURSAL_ID=$(echo "$SUCURSAL_RESP" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    echo "✅ SUCURSAL CREADA - ID: $SUCURSAL_ID"

    if echo "$SUCURSAL_RESP" | grep -q '"ciudad":{'; then
        echo "✅ CIUDAD SERIALIZADA CORRECTAMENTE"
        echo "TEST 1: PASS"
    else
        echo "❌ CIUDAD NO SERIALIZADA"
        echo "TEST 1: FAIL"
    fi
elif echo "$SUCURSAL_RESP" | grep -q "ResponseValidationError"; then
    echo "❌ ResponseValidationError - Fix NO funcionó"
    echo "TEST 1: FAIL"
else
    echo "❌ ERROR: $(echo $SUCURSAL_RESP | head -c 200)"
    echo "TEST 1: FAIL"
fi

echo ""
echo "==============================================="
echo "TEST 2: LISTAR SUCURSALES"
echo "==============================================="

LIST_RESP=$(curl -s -X GET "$BASE_URL/sucursales" \
  -H "Authorization: Bearer $TOKEN1")

echo "Count: $(echo $LIST_RESP | grep -o '"id"' | wc -l)"
if echo "$LIST_RESP" | grep -q '"ciudad":{'; then
    echo "✅ CIUDAD EN LISTADO"
    echo "TEST 2: PASS"
else
    echo "❌ CIUDAD NO EN LISTADO"
    echo "TEST 2: FAIL"
fi

echo ""
echo "==============================================="
echo "TEST 3: OBTENER DETALLE"
echo "==============================================="

DETAIL_RESP=$(curl -s -X GET "$BASE_URL/sucursales/$SUCURSAL_ID" \
  -H "Authorization: Bearer $TOKEN1")

echo "Response (first 500 chars):"
echo "$DETAIL_RESP" | head -c 500
echo ""

if echo "$DETAIL_RESP" | grep -q '"ciudad":{'; then
    echo "✅ CIUDAD EN DETALLE"
    echo "TEST 3: PASS"
else
    echo "❌ CIUDAD NO EN DETALLE"
    echo "TEST 3: FAIL"
fi

echo ""
echo "==============================================="
echo "TEST 4: MULTITENANCY - EMPRESA B NO VE"
echo "==============================================="

LOGIN2=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"correo\":\"$ADMIN2_EMAIL\",\"password\":\"$ADMIN2_PASS\"}")

TOKEN2=$(echo "$LOGIN2" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token Admin 2: ${TOKEN2:0:30}..."

LIST2=$(curl -s -X GET "$BASE_URL/sucursales" \
  -H "Authorization: Bearer $TOKEN2")

COUNT=$(echo "$LIST2" | grep -o '"id"' | wc -l)
if [ $COUNT -eq 0 ]; then
    echo "✅ Admin 2 no ve sucursales de Admin 1"
    echo "TEST 4: PASS"
else
    echo "⚠️ Admin 2 ve sucursales (puede ser válido si son suyas)"
    echo "TEST 4: CHECK"
fi

echo ""
echo "==============================================="
echo "TESTS COMPLETADOS"
echo "==============================================="
