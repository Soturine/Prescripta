Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$criticalPatterns = @([char]0x00C3, [char]0x00C2, [char]0xFFFD)
$accentWarnings = @(
  "prescricao",
  "seguranca",
  "historico",
  "reconciliacao",
  "clinico",
  "pratico",
  "decisao",
  "integracao",
  "avaliacao",
  "usuario",
  "orientacao",
  "configuracao",
  "relatorio",
  "evidencia"
)
$exclude = "\\(node_modules|dist|\.git|\.venv|docs\\assets)\\"
$extensions = @("*.md", "*.py", "*.ts", "*.tsx", "*.ps1", "*.example", "*.txt")
$files = foreach ($extension in $extensions) {
  Get-ChildItem -Path $root -Recurse -File -Include $extension |
    Where-Object { $_.FullName -notmatch $exclude }
}

$errors = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

foreach ($file in $files) {
  $relative = Resolve-Path -Path $file.FullName -Relative
  $text = [System.IO.File]::ReadAllText($file.FullName)

  foreach ($pattern in $criticalPatterns) {
    if ($text.Contains($pattern)) {
      $errors.Add("Mojibake ou encoding inválido em ${relative}: padrão '${pattern}'")
    }
  }

  if ($file.Extension -eq ".md") {
    $lines = $text -split "`r?`n"
    for ($index = 0; $index -lt $lines.Count; $index++) {
      $line = $lines[$index]
      if ($line.Length -gt 500 -and $line -notmatch "^http|^\|") {
        $errors.Add("Linha Markdown muito longa em ${relative}:$($index + 1)")
      }
    }
  }

  if ($file.Extension -in @(".md", ".tsx") -and $text -match "FHIR fict[ií]cio|mock_hospital|Paciente Demo") {
    $warnings.Add("Revisar linguagem de produto/demo em ${relative}.")
  }

  $visibleLines = New-Object System.Collections.Generic.List[string]
  foreach ($line in ($text -split "`r?`n")) {
    if ($file.Extension -eq ".md") {
      $visibleLines.Add($line)
      continue
    }
    if ($file.Extension -in @(".tsx", ".ts")) {
      if ($line -match ">[^<{]+<|title=|placeholder=|label=|description=|message=|text:") {
        $visibleLines.Add($line)
      }
      continue
    }
    if ($file.Extension -in @(".ps1", ".txt", ".example")) {
      if ($line -notmatch "^\s*(\$|#|function|param|\}|if|foreach|return)") {
        $visibleLines.Add($line)
      }
    }
  }

  if ($relative -notmatch "scripts\\check-text-quality\.ps1$") {
    foreach ($line in $visibleLines) {
      foreach ($word in $accentWarnings) {
        if ($line -match "\b$word\b") {
          $warnings.Add("Revisar possível termo sem acento em ${relative}: ${word}")
          break
        }
      }
    }
  }
}

$envExample = Join-Path $root ".env.example"
if (Test-Path $envExample) {
  $envText = [System.IO.File]::ReadAllText($envExample)
  if (($envText -split "`r?`n").Count -lt 8) {
    $errors.Add(".env.example parece comprimido em poucas linhas.")
  }
  if ($envText -notmatch "PRESCRIPTA_CONFIG_ENCRYPTION_KEY=") {
    $errors.Add(".env.example não documenta PRESCRIPTA_CONFIG_ENCRYPTION_KEY.")
  }
} else {
  $errors.Add(".env.example não encontrado.")
}

foreach ($warning in $warnings | Select-Object -Unique) {
  Write-Host "Aviso: $warning" -ForegroundColor Yellow
}

if ($errors.Count -gt 0) {
  foreach ($item in $errors) {
    Write-Host "Erro: $item" -ForegroundColor Red
  }
  exit 1
}

Write-Host "Qualidade textual OK." -ForegroundColor Green
