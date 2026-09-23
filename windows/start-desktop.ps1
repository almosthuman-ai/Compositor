[CmdletBinding()]
param([string]$Executable)
$ErrorActionPreference = 'Stop'
if (-not $Executable) {
    $pointer = Join-Path $env:LOCALAPPDATA 'Compositor/installed-executable.txt'
    if (-not (Test-Path -LiteralPath $pointer)) { throw 'Install Compositor first.' }
    $Executable = (Get-Content -LiteralPath $pointer -Raw).Trim()
}
$Executable = [IO.Path]::GetFullPath($Executable)
if (-not (Test-Path -LiteralPath $Executable)) { throw 'The installed executable is missing.' }
$taskName = 'Compositor Desktop'
$action = New-ScheduledTaskAction -Execute $Executable -WorkingDirectory (Split-Path -Parent $Executable)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
Write-Output 'Compositor launched through its independent desktop task.'
