param(
  [string]$Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$allowlistPath = Join-Path $PSScriptRoot "text-quality-allowlist.json"
if (-not (Test-Path $allowlistPath)) {
  throw "Allowlist obrigatória não encontrada: $allowlistPath"
}
$allowlist = Get-Content -Raw -Encoding utf8 $allowlistPath | ConvertFrom-Json
$targets = if ($Path) {
  @(Resolve-Path $Path)
} else {
  @(
    Join-Path $root "README.md"
    Join-Path $root "CHANGELOG.md"
    Join-Path $root "ROADMAP.md"
    Join-Path $root "docs"
    Join-Path $root "backend\app"
    Join-Path $root "frontend\src"
    Join-Path $root "scripts"
    Join-Path $root "examples"
  )
}
$extensions = @(".md", ".py", ".ts", ".tsx")
$forbidden = @(
  "nao", "prescricao", "clinico", "historico", "relatorio", "avaliacao", "decisao",
  "medico", "farmaceutico", "configuracao", "validacao", "jurisdicao", "orientacao",
  "execucao", "importacao", "revisao", "farmacologico", "principio", "audiencia",
  "psicotropico", "serotonergico", "litio"
)
$mojibake = @([char]0x00C3, [char]0x00C2, [char]0xFFFD)
$files = New-Object System.Collections.Generic.List[System.IO.FileInfo]
foreach ($target in $targets) {
  if (-not (Test-Path $target)) { continue }
  $item = Get-Item $target
  if ($item.PSIsContainer) {
    Get-ChildItem $item.FullName -Recurse -File | Where-Object {
      $_.Extension -in $extensions -and $_.FullName -notmatch "\\(node_modules|dist)\\"
    } | ForEach-Object { $files.Add($_) }
  } elseif ($item.Extension -in $extensions) {
    $files.Add($item)
  }
}

$errors = New-Object System.Collections.Generic.List[string]
foreach ($file in $files) {
  $text = [System.IO.File]::ReadAllText($file.FullName)
  $relative = Resolve-Path -Path $file.FullName -Relative
  foreach ($marker in $mojibake) {
    if ($text.Contains($marker)) {
      $errors.Add("Mojibake em ${relative}: caractere U+$([int]$marker).ToString('X4')")
    }
  }
  $inCodeFence = $false
  $lineNumber = 0
  foreach ($line in ($text -split "`r?`n")) {
    $lineNumber++
    if ($file.Extension -eq ".md" -and $line.TrimStart().StartsWith('```')) {
      $inCodeFence = -not $inCodeFence
      continue
    }
    if ($inCodeFence -or $line -match "text-quality:\s*allow") { continue }
    $visible = $file.Extension -eq ".md"
    if ($file.Extension -in @(".ts", ".tsx")) {
      $visible = $line -match ">[^<{]+<|title=|placeholder=|label=|description=|message=|text:"
    }
    if ($file.Extension -eq ".py") {
      $visible = $line -match "detail=|title=|description=|recommendation=|message=|educational_notice="
    }
    if (-not $visible) { continue }
    $scanLine = [regex]::Replace($line, '`[^`]*`', '')
    $scanLine = [regex]::Replace($scanLine, 'https?://\S+', '')
    if ($scanLine -match '[\p{L}]+\?[\p{L}?]+') {
      $errors.Add("Possível caractere corrompido em ${relative}:${lineNumber}")
    }
    foreach ($word in $forbidden) {
      if ($scanLine -match "(?i)(?<![A-Za-z0-9_])$([regex]::Escape($word))(?![A-Za-z0-9_])") {
        $errors.Add("Termo sem acento em ${relative}:${lineNumber}: '$word'")
      }
    }
    if ($file.Extension -eq ".md") {
      foreach ($match in [regex]::Matches($line, '!??\[[^\]]*\]\(([^)]+)\)')) {
        $link = $match.Groups[1].Value.Trim().Split(' ')[0].Trim('<', '>')
        if ($link -match '^(https?://|mailto:|#)' -or [string]::IsNullOrWhiteSpace($link)) {
          continue
        }
        $linkPath = ($link -split '#')[0]
        if ([string]::IsNullOrWhiteSpace($linkPath)) { continue }
        $resolvedLink = Join-Path $file.DirectoryName ([uri]::UnescapeDataString($linkPath))
        if (-not (Test-Path $resolvedLink)) {
          $errors.Add("Link ou asset inexistente em ${relative}:${lineNumber}: '$linkPath'")
        }
      }
    }
  }
}

if ($errors.Count -gt 0) {
  $errors | Select-Object -Unique | ForEach-Object { Write-Host "Erro: $_" -ForegroundColor Red }
  exit 1
}
Write-Host "Qualidade textual OK." -ForegroundColor Green
