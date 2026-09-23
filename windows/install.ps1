[CmdletBinding()]
param([string]$Source)
$ErrorActionPreference = 'Stop'
if (-not $Source) { $Source = Join-Path (Split-Path -Parent $PSScriptRoot) 'dist/Compositor' }
$Source = [IO.Path]::GetFullPath($Source)
if (-not (Test-Path -LiteralPath (Join-Path $Source 'Compositor.exe'))) { throw 'Build Compositor first, or specify its extracted distribution folder.' }
$installRoot = Join-Path $env:LOCALAPPDATA 'Compositor'
$destination = Join-Path $installRoot ('apps/' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $destination -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $Source 'Compositor.exe') -Destination $destination
Copy-Item -LiteralPath (Join-Path $Source 'Compositor-Tools.exe') -Destination $destination
Copy-Item -LiteralPath (Join-Path $Source '_internal') -Destination $destination -Recurse
foreach ($notice in @('LICENSE.txt','THIRD_PARTY_NOTICES.md','third-party-licenses')) {
    Copy-Item -LiteralPath (Join-Path $Source $notice) -Destination $destination -Recurse
}
$executable = Join-Path $destination 'Compositor.exe'
$shell = New-Object -ComObject WScript.Shell
foreach ($folder in @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:APPDATA 'Microsoft/Windows/Start Menu/Programs'))) {
    $shortcut = $shell.CreateShortcut((Join-Path $folder 'Compositor.lnk'))
    $shortcut.TargetPath = $executable
    $shortcut.WorkingDirectory = $destination
    $shortcut.Description = 'Layered art and generative editing'
    $shortcut.Save()
}
$executable | Set-Content -LiteralPath (Join-Path $installRoot 'installed-executable.txt') -Encoding UTF8
Write-Output "Installed: $executable"
