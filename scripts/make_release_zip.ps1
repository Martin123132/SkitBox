param(
  [string]$Version = ""
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

$dist = Join-Path $repoRoot "dist"
$packageName = "SkitBox-$Version"
$stage = Join-Path $dist $packageName
$zipPath = Join-Path $dist "$packageName.zip"

New-Item -ItemType Directory -Force -Path $dist | Out-Null

function Remove-If-In-Dist($PathToRemove) {
  if (-not (Test-Path -LiteralPath $PathToRemove)) {
    return
  }
  $distResolved = (Resolve-Path -LiteralPath $dist).Path
  $targetResolved = (Resolve-Path -LiteralPath $PathToRemove).Path
  if (-not $targetResolved.StartsWith($distResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside dist: $targetResolved"
  }
  Remove-Item -LiteralPath $targetResolved -Recurse -Force
}

function Get-RepoRelativePath($FullName) {
  $full = (Resolve-Path -LiteralPath $FullName).Path
  if (-not $full.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Path is outside repo root: $full"
  }
  return $full.Substring($repoRoot.Length).TrimStart("\", "/")
}

Remove-If-In-Dist $stage
if (Test-Path -LiteralPath $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Force -Path $stage | Out-Null

$gitRoot = ""
try {
  $gitRoot = (git -C $repoRoot rev-parse --show-toplevel 2>$null).Trim()
} catch {
  $gitRoot = ""
}

$files = @()
if ($gitRoot -and ((Resolve-Path -LiteralPath $gitRoot).Path -eq $repoRoot)) {
  $files = git -C $repoRoot ls-files -- .
}
if (-not $files) {
  $files = Get-ChildItem -LiteralPath $repoRoot -Force -Recurse |
    Where-Object {
      -not $_.PSIsContainer -and
      $_.FullName -notlike "$dist*" -and
      $_.FullName -notlike "$(Join-Path $repoRoot 'user_data')*" -and
      $_.FullName -notlike "$(Join-Path $repoRoot 'temp')*" -and
      $_.FullName -notlike "$(Join-Path $repoRoot '.git')*" -and
      $_.FullName -notlike "*\__pycache__\*" -and
      $_.FullName -notlike "*\.pytest_cache\*"
    } |
    ForEach-Object { Get-RepoRelativePath $_.FullName }
}

foreach ($file in $files) {
  $source = Join-Path $repoRoot $file
  if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    continue
  }
  $target = Join-Path $stage $file
  $targetDir = Split-Path -Parent $target
  New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
  Copy-Item -LiteralPath $source -Destination $target -Force
}

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zipPath -Force

$size = [math]::Round((Get-Item -LiteralPath $zipPath).Length / 1KB, 1)
Write-Host "Created $zipPath ($size KB)"
