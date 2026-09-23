[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Push-Location $repo
try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        py -3.11 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 for Windows, then run setup again.' }
    }
    & ./.venv/Scripts/python.exe -m pip install -r windows/requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    Write-Output 'Ready. Run .venv/Scripts/pythonw.exe windows/run.py or windows/build.ps1.'
} finally { Pop-Location }
