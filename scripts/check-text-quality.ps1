param([string]$Path)
$ErrorActionPreference = "Stop"
$arguments = @((Join-Path $PSScriptRoot "check_text_quality.py"))
if ($Path) { $arguments += $Path }
& python @arguments
exit $LASTEXITCODE
