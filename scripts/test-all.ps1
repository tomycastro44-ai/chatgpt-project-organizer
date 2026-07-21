$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = "python"
if (Test-Path "./.venv/Scripts/python.exe") { $Python = "./.venv/Scripts/python.exe" }
$env:PYTHONPATH = "backend"
& $Python -m pytest -q backend/tests tests/contracts
Push-Location frontend
npm test -- --run
npm run build
Pop-Location
& $Python scripts/validate_ot012.py
