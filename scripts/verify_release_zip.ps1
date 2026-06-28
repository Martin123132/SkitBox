param(
  [string]$Version = "",
  [string]$ZipPath = "",
  [string]$WorkRoot = "",
  [switch]$SkipDoctor
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Get-SkitBoxVersion {
  $initPath = Join-Path $repoRoot "sitcom_engine_app\__init__.py"
  $initText = Get-Content -Raw -LiteralPath $initPath
  $match = [regex]::Match($initText, '__version__\s*=\s*"([^"]+)"')
  if (-not $match.Success) {
    throw "Could not read SkitBox version from $initPath"
  }
  return "v$($match.Groups[1].Value)"
}

if (-not $Version) {
  $Version = Get-SkitBoxVersion
}

$safeVersion = $Version -replace "[^a-zA-Z0-9._-]", "-"
if ($WorkRoot) {
  New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
  $tempBase = (Resolve-Path -LiteralPath $WorkRoot).Path
} else {
  $tempBase = [System.IO.Path]::GetTempPath()
}
$work = Join-Path $tempBase "SkitBoxReleaseVerify-$safeVersion-$([System.Guid]::NewGuid().ToString('N'))"
$downloadedZip = Join-Path $work "SkitBox-$Version.zip"
$extractDir = Join-Path $work "unzipped"
$dataDir = Join-Path $work "data"

function Remove-TempWork {
  if (-not (Test-Path -LiteralPath $work)) {
    return
  }
  $tempResolved = (Resolve-Path -LiteralPath $tempBase).Path
  $workResolved = (Resolve-Path -LiteralPath $work).Path
  if (-not $workResolved.StartsWith($tempResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside work root: $workResolved"
  }
  Remove-Item -LiteralPath $workResolved -Recurse -Force
}

try {
  New-Item -ItemType Directory -Force -Path $work, $extractDir, $dataDir | Out-Null

  if (-not $ZipPath) {
    throw "Pass -ZipPath for local verification. Published release download is not configured yet."
  }

  $sourceZip = (Resolve-Path -LiteralPath $ZipPath).Path
  Copy-Item -LiteralPath $sourceZip -Destination $downloadedZip -Force
  Write-Host "Using local ZIP: $sourceZip"

  Expand-Archive -LiteralPath $downloadedZip -DestinationPath $extractDir -Force

  $required = @(
    "START_SkitBox_WINDOWS.bat",
    "STOP_SkitBox_WINDOWS.bat",
    "README.md",
    "scripts\stop_dev_processes.ps1",
    "sitcom_engine_app\app.py",
    "sitcom_engine_app\engine.py",
    "sitcom_engine_app\seeds\default_show.json",
    "sitcom_engine_app\seeds\templates.json",
    "sitcom_engine_app\templates\index.html",
    "sitcom_engine_app\static\assets\sitcom-set-bg.png"
  )
  foreach ($relative in $required) {
    $path = Join-Path $extractDir $relative
    if (-not (Test-Path -LiteralPath $path)) {
      throw "Missing required release file: $relative"
    }
  }

  $forbidden = Get-ChildItem -LiteralPath $extractDir -Force -Recurse |
    Where-Object { $_.Name -in @(".git", "__pycache__", ".pytest_cache", "user_data", "dist") }
  if ($forbidden) {
    throw "Release ZIP contains forbidden generated files: $($forbidden[0].FullName)"
  }

  if (-not $SkipDoctor) {
    Push-Location $extractDir
    try {
      $env:SKITBOX_HOME = $dataDir
      python -m sitcom_engine_app.app --doctor | Out-Host
      if ($LASTEXITCODE -ne 0) {
        throw "Doctor command failed."
      }
    } finally {
      Pop-Location
      Remove-Item Env:\SKITBOX_HOME -ErrorAction SilentlyContinue
    }
  }

  Write-Host "Release ZIP verified for $Version"
} finally {
  Remove-TempWork
}
