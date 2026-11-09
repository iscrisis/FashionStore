#!/bin/bash
# Iniciar FastAPI en puerto 8001 conectado EXCLUSIVAMENTE a fashionstore_e2e_cu11_cu12

export DATABASE_URL="postgresql+psycopg://test_user:test_password_secure@localhost:5433/fashionstore_e2e_cu11_cu12"
export JWT_SECRET_KEY="test-secret-key-e2e-only-12345678901234567890"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRE_MINUTES="1440"

cd "$(dirname "$0")"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
