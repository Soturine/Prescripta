param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $Root "backend"
$FrontendPath = Join-Path $Root "frontend"

function Test-PortAvailable {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return -not $connection
}

function Require-Command {
    param([string]$CommandName, [string]$InstallHint)
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        Write-Host "Dependência ausente: $CommandName" -ForegroundColor Yellow
        Write-Host $InstallHint
        exit 1
    }
}

Require-Command "python" "Instale Python 3.12+ e rode: python -m pip install -r backend\requirements.txt"
Require-Command "npm" "Instale Node.js e rode: cd frontend; npm install"

if (-not (Test-Path (Join-Path $BackendPath "requirements.txt"))) {
    Write-Host "Backend não encontrado em $BackendPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $FrontendPath "package.json"))) {
    Write-Host "Frontend não encontrado em $FrontendPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-PortAvailable $BackendPort)) {
    Write-Host "Porta $BackendPort em uso. Informe outra com -BackendPort." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-PortAvailable $FrontendPort)) {
    Write-Host "Porta $FrontendPort em uso. O Vite pode escolher alternativa, mas tente -FrontendPort." -ForegroundColor Yellow
    exit 1
}

$BackendUrl = "http://127.0.0.1:$BackendPort"
$FrontendUrl = "http://127.0.0.1:$FrontendPort"

Write-Host "Iniciando Prescripta..." -ForegroundColor Cyan
Write-Host "Backend: $BackendUrl"
Write-Host "Swagger: $BackendUrl/docs"
Write-Host "Frontend: $FrontendUrl"

$backendCommand = "`$env:PRESCRIPTA_CORS_ORIGINS='http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort'; python -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort"
$frontendCommand = "`$env:VITE_API_URL='$BackendUrl/api'; npm run dev -- --host 127.0.0.1 --port $FrontendPort"

Start-Process powershell -ArgumentList @("-NoProfile", "-NoExit", "-Command", $backendCommand) -WorkingDirectory $BackendPath
Start-Process powershell -ArgumentList @("-NoProfile", "-NoExit", "-Command", $frontendCommand) -WorkingDirectory $FrontendPath

Start-Sleep -Seconds 3
Start-Process $FrontendUrl

Write-Host "Janelas abertas. Use Ctrl+C em cada janela para encerrar." -ForegroundColor Green
