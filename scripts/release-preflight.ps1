$ErrorActionPreference = "Stop"
& python (Join-Path $PSScriptRoot "release_preflight.py")
exit $LASTEXITCODE
