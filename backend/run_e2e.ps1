# FastAPI E2E en puerto 8001 - fashionstore_e2e_cu11_cu12

$env:DATABASE_URL = 'postgresql+psycopg://test_user:test_password_secure@localhost:5433/fashionstore_e2e_cu11_cu12'

Write-Host '======================================' -ForegroundColor Green
Write-Host 'FastAPI E2E - Puerto 8001' -ForegroundColor Green
Write-Host 'Base: fashionstore_e2e_cu11_cu12' -ForegroundColor Green
Write-Host '======================================' -ForegroundColor Green
Write-Host ''
Write-Host 'Iniciando...' -ForegroundColor Cyan
Write-Host ''

Set-Location -Path 'C:\Users\hp\Desktop\P1\FashionStore\backend'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
