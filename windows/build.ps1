[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run windows/setup.ps1 first.' }
Push-Location $repo
try {
    & $python -m PyInstaller --noconfirm windows/Compositor.spec
    if ($LASTEXITCODE -ne 0) { throw 'Windows build failed.' }
    & $python windows/collect_licenses.py dist/Compositor
    if ($LASTEXITCODE -ne 0) { throw 'Dependency notice collection failed.' }
    Copy-Item -LiteralPath 'LICENSE' -Destination 'dist/Compositor/LICENSE.txt'
    Copy-Item -LiteralPath 'windows/THIRD_PARTY_NOTICES.md' -Destination 'dist/Compositor/THIRD_PARTY_NOTICES.md'
    Write-Output (Join-Path $repo 'dist/Compositor/Compositor.exe')
} finally { Pop-Location }
