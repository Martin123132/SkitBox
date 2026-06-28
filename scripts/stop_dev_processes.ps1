param(
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

$targets = Get-CimInstance Win32_Process |
  Where-Object {
    $_.CommandLine -and
    $_.CommandLine -like "*sitcom_engine_app.app*" -and
    ($_.Name -like "python*" -or $_.Name -eq "py.exe") -and
    $_.ProcessId -ne $PID
  }

if (-not $targets) {
  Write-Host "No SkitBox app server processes found."
  exit 0
}

foreach ($target in $targets) {
  $line = $target.CommandLine
  if ($line.Length -gt 180) {
    $line = $line.Substring(0, 180) + "..."
  }
  if ($WhatIf) {
    Write-Host "Would stop PID $($target.ProcessId): $line"
    continue
  }
  Stop-Process -Id $target.ProcessId -Force
  Write-Host "Stopped SkitBox PID $($target.ProcessId)"
}
