param(
  [string]$OutDir = "dist"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outRoot = if ([System.IO.Path]::IsPathRooted($OutDir)) { $OutDir } else { Join-Path $root $OutDir }
$target = Join-Path $outRoot "digital-migration-stand-$stamp"
$zipPath = "$target.zip"

New-Item -ItemType Directory -Path $target -Force | Out-Null

$include = @(
  "src",
  "agents",
  "experiments",
  "queries",
  "codebooks",
  "docs",
  "examples",
  "tests\fixtures",
  "scripts",
  "run_pipeline.py",
  "config.yaml",
  "requirements.txt",
  "README.md",
  "pytest.ini"
)

foreach ($item in $include) {
  $source = Join-Path $root $item
  if (Test-Path $source) {
    Copy-Item $source -Destination $target -Recurse -Force
  }
}

New-Item -ItemType Directory -Path (Join-Path $target "data\input") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $target "data\output") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $target "data\interim") -Force | Out-Null

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$target\*" -DestinationPath $zipPath -Force

Write-Host "Package directory: $target"
Write-Host "Package zip: $zipPath"
