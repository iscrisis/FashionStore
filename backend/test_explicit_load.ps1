# Test explicit Ciudad loading strategy

$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzkzMDUxMTUzLCJyb2wiOiJBRE1JTklTVFJBRE9SIn0.2IHkVUuxIYel5rEvFxdn3u-O79WAbcxHLRlVqWl5skI"

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ PRUEBA A: CREAR SUCURSAL               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$body = @{
    nombre = "Sucursal Explicit Load Test"
    ciudad_id = 15
    direccion = "Test Street"
    telefono = "(57) 300 1111111"
    is_active = $true
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/sucursales" `
      -Method POST `
      -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} `
      -Body $body -ErrorAction Stop

    $sucursal = $response.Content | ConvertFrom-Json

    if ($sucursal.id) {
        Write-Host "✅ CREADA: ID $($sucursal.id)" -ForegroundColor Green

        if ($sucursal.ciudad -and $sucursal.ciudad.nombre) {
            Write-Host "✅✅ CIUDAD CARGADA: $($sucursal.ciudad.nombre)" -ForegroundColor Green
            Write-Host ""
            Write-Host "PRUEBA A: PASS" -ForegroundColor Green
        } else {
            Write-Host "❌ CIUDAD NULL" -ForegroundColor Red
            Write-Host ""
            Write-Host "PRUEBA A: FAIL" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ NO CREADA" -ForegroundColor Red
        Write-Host ""
        Write-Host "PRUEBA A: FAIL" -ForegroundColor Red
    }

} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "PRUEBA A: FAIL" -ForegroundColor Red
}

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ PRUEBA B: LISTAR SUCURSALES           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/sucursales" `
      -Headers @{"Authorization"="Bearer $token"} -ErrorAction Stop

    $list = $response.Content | ConvertFrom-Json

    Write-Host "✅ LISTADAS: $($list.Count) sucursales" -ForegroundColor Green

    $with_ciudad = ($list | Where-Object { $_.ciudad -and $_.ciudad.nombre }).Count

    Write-Host "   Con ciudad: $with_ciudad / $($list.Count)" -ForegroundColor Yellow

    if ($with_ciudad -eq $list.Count) {
        Write-Host ""
        Write-Host "PRUEBA B: PASS" -ForegroundColor Green
    } else {
        Write-Host "   (Old records may not have ciudad)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "PRUEBA B: PARTIAL" -ForegroundColor Yellow
    }

} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "PRUEBA B: FAIL" -ForegroundColor Red
}

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ RESUMEN FINAL                          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
