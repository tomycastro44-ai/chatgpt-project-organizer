$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Backend = Start-Process -FilePath "./.venv/Scripts/python.exe" -ArgumentList "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--reload", "--port", "8000" -PassThru
$Frontend = Start-Process -FilePath "npm" -ArgumentList "--prefix", "frontend", "run", "dev" -PassThru

Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Press Ctrl+C to stop."
try {
    Wait-Process -Id $Backend.Id, $Frontend.Id
} finally {
    Stop-Process -Id $Backend.Id, $Frontend.Id -ErrorAction SilentlyContinue
}
