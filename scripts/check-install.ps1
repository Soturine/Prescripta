Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

function Test-Command {
  param([string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

$checks = @(
  @{ Label = "Python"; Ok = (Test-Command "python"); Hint = "Instale Python 3.12+." },
  @{ Label = "Node/npm"; Ok = (Test-Command "npm"); Hint = "Instale Node.js LTS." },
  @{ Label = "Backend"; Ok = (Test-Path (Join-Path $backend "requirements.txt")); Hint = "Diretório backend ausente." },
  @{ Label = "Frontend"; Ok = (Test-Path (Join-Path $frontend "package.json")); Hint = "Diretório frontend ausente." },
  @{ Label = "Venv"; Ok = (Test-Path $venvPython); Hint = "Rode scripts/setup-dev.ps1." },
  @{ Label = "Node modules"; Ok = (Test-Path (Join-Path $frontend "node_modules")); Hint = "Rode scripts/setup-dev.ps1." }
)

$failed = $false
foreach ($check in $checks) {
  if ($check.Ok) {
    Write-Host "OK  $($check.Label)" -ForegroundColor Green
  } else {
    Write-Host "ERRO $($check.Label): $($check.Hint)" -ForegroundColor Red
    $failed = $true
  }
}

if ($failed) {
  exit 1
}

Write-Host "Instalação local pronta." -ForegroundColor Green
