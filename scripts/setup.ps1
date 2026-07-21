$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m venv .venv
& ./.venv/Scripts/python.exe -m pip install --upgrade pip
& ./.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm --prefix frontend ci

Write-Host "Setup complete. Run ./scripts/start-dev.ps1"
