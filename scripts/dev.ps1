param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  throw "Ambiente virtual ausente. Rode scripts/setup-dev.ps1 primeiro."
}

$backendUrl = "http://127.0.0.1:$BackendPort"
$frontendUrl = "http://127.0.0.1:$FrontendPort"

$backendCommand = "`$env:PRESCRIPTA_CORS_ORIGINS='http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort'; & '$venvPython' -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort --reload"
$frontendCommand = "`$env:VITE_API_URL='$backendUrl/api'; npm run dev -- --host 127.0.0.1 --port $FrontendPort"

Write-Host "Backend:  $backendUrl"
Write-Host "Swagger:  $backendUrl/docs"
Write-Host "Frontend: $frontendUrl"

Start-Process powershell -ArgumentList @("-NoProfile", "-NoExit", "-Command", $backendCommand) -WorkingDirectory $backend
Start-Process powershell -ArgumentList @("-NoProfile", "-NoExit", "-Command", $frontendCommand) -WorkingDirectory $frontend

Write-Host "Servidores iniciados em janelas separadas." -ForegroundColor Green
