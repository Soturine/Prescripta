Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$frontend = Join-Path $root "frontend"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python 3.12+ não encontrado."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  throw "npm não encontrado. Instale Node.js LTS."
}

if (-not (Test-Path $venvPython)) {
  python -m venv (Join-Path $root ".venv")
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $root "backend\requirements.txt")

Push-Location $frontend
try {
  npm install
} finally {
  Pop-Location
}

Write-Host "Ambiente de desenvolvimento preparado." -ForegroundColor Green
