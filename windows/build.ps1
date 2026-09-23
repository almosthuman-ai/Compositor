[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run windows/setup.ps1 first.' }
Push-Location $repo
try {
    function Get-CompositorSourceSignature {
        $sourceFiles = @(Get-ChildItem -LiteralPath 'windows/compositor' -Recurse -File | Where-Object { $_.Extension -in @('.py','.md','.json') })
        $sourceFiles += Get-Item -LiteralPath 'windows/run.py','windows/Compositor.spec','windows/requirements.txt'
        return (($sourceFiles | Sort-Object FullName | ForEach-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }) -join '|')
    }
    $compositorSourceSignature = Get-CompositorSourceSignature
    # PyInstaller logs progress to stderr. Windows PowerShell can turn those
    # lines into NativeCommandError records when a caller redirects the build.
    # The native exit code, not its diagnostic stream, determines success.
    $buildErrorPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $python -m PyInstaller --clean --noconfirm windows/Compositor.spec
        $buildExitCode = $LASTEXITCODE
    } finally { $ErrorActionPreference = $buildErrorPreference }
    if ($buildExitCode -ne 0) { throw 'Windows build failed.' }
    if ((Get-CompositorSourceSignature) -ne $compositorSourceSignature) { throw 'Source changed during this build. Build again before installing or distributing it.' }
    & $python windows/collect_licenses.py dist/Compositor
    if ($LASTEXITCODE -ne 0) { throw 'Dependency notice collection failed.' }
    Copy-Item -LiteralPath 'LICENSE' -Destination 'dist/Compositor/LICENSE.txt'
    Copy-Item -LiteralPath 'windows/THIRD_PARTY_NOTICES.md' -Destination 'dist/Compositor/THIRD_PARTY_NOTICES.md'
    Write-Output (Join-Path $repo 'dist/Compositor/Compositor.exe')
} finally { Pop-Location }
