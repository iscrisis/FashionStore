# Script para iniciar FastAPI en puerto 8001 conectado EXCLUSIVAMENTE a fashionstore_e2e_cu11_cu12

# Exportar variables de entorno para fashionstore_e2e_cu11_cu12
$env:DATABASE_URL = "postgresql+psycopg://test_user:test_password_secure@localhost:5433/fashionstore_e2e_cu11_cu12"
$env:JWT_SECRET_KEY = "test-secret-key-e2e-only-12345678901234567890"
$env:JWT_ALGORITHM = "HS256"
$env:JWT_EXPIRE_MINUTES = "1440"
$env:BACKEND_PORT = "8001"
$env:APP_ENV = "e2e_test"

Write-Host "DATABASE_URL establecido: postgresql+psycopg://test_user:***@localhost:5433/fashionstore_e2e_cu11_cu12" -ForegroundColor Green
Write-Host "Iniciando FastAPI en puerto 8001..." -ForegroundColor Cyan

# Iniciar FastAPI
cd "C:\Users\hp\Desktop\P1\FashionStore\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
