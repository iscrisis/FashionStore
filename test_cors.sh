#!/bin/bash

echo "=== CORS PREFLIGHT TEST (OPTIONS request) ==="
echo "Testing OPTIONS /api/v1/empresas from localhost:4200..."
curl -v -X OPTIONS http://localhost:8000/api/v1/empresas \
  -H "Origin: http://localhost:4200" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type"

echo ""
echo ""
echo "=== HEALTH CHECK TEST ==="
curl -v http://localhost:8000/api/v1/health

echo ""
echo ""
echo "=== AUTHENTICATION TEST (login) ==="
curl -v -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "superadmin@fashionstore.com", "password": "changeme"}' \
  -H "Origin: http://localhost:4200"

