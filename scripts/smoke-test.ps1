param(
  [string]$ApiUrl = "http://127.0.0.1:8000/api"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$health = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get
if ($health.status -ne "ok") { throw "API não saudável." }
$login = Invoke-RestMethod -Uri "$ApiUrl/auth/login" -Method Post -ContentType "application/json" -Body (@{
  email = "admin@prescripta.local"
  password = "Admin@12345"
} | ConvertTo-Json)
$headers = @{ Authorization = "Bearer $($login.access_token)" }
$dashboard = Invoke-RestMethod -Uri "$ApiUrl/dashboard" -Headers $headers
if ($null -eq $dashboard.catalog_quality) { throw "Dashboard sem métricas de qualidade." }
Write-Host "Smoke test OK: API, autenticação e dashboard." -ForegroundColor Green
