Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$dbPath = Join-Path $root "backend\prescripta.db"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  throw "Ambiente virtual ausente. Rode scripts/setup-dev.ps1 primeiro."
}

if (Test-Path $dbPath) {
  $resolvedRoot = (Resolve-Path $root).Path
  $resolvedDb = (Resolve-Path $dbPath).Path
  if (-not $resolvedDb.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Caminho de banco fora do workspace: $resolvedDb"
  }
  Remove-Item -LiteralPath $resolvedDb -Force
  Write-Host "Banco demo removido: $resolvedDb" -ForegroundColor Yellow
}

Push-Location (Join-Path $root "backend")
try {
  & $venvPython -c "from app.database.session import init_db, SessionLocal; from app.database.seed import seed_demo_data; init_db(); db=SessionLocal(); seed_demo_data(db); db.close()"
} finally {
  Pop-Location
}

Write-Host "Banco demo recriado com seed." -ForegroundColor Green
