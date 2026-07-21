$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Missing .venv. Run .\scripts\setup.ps1 first." }
$env:PYTHONPATH = "backend"
& $Python -m pytest -q backend/tests tests/contracts
Push-Location frontend
npm test -- --run
npm run build
npm audit --omit=dev --audit-level=high
Pop-Location
& $Python -m pip check
& $Python -m compileall -q backend/app
& $Python scripts/validate_ot013.py
$env:PYTHONPATH = 'backend'
& $Python scripts/validate_ot014.py
