param(
  [string]$Host = "127.0.0.1",
  [int]$Port = 8765,
  [string]$VenvDir = ".venv",
  [string]$RuntimeRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path "$VenvDir\Scripts\python.exe")) {
  throw "Virtual environment not found at $VenvDir. Run scripts/setup_windows.ps1 first."
}

if ([string]::IsNullOrWhiteSpace($RuntimeRoot)) {
  $RuntimeRoot = Join-Path $env:LOCALAPPDATA "DigitalMigrationRuntime"
}

New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null

$env:MIGRATION_RUNTIME_ROOT = $RuntimeRoot
$env:MIGRATION_WEB_HOST = $Host
$env:MIGRATION_WEB_PORT = "$Port"

Write-Host "Runtime root: $RuntimeRoot"
Write-Host "Web UI: http://$Host`:$Port"

& "$VenvDir\Scripts\python.exe" -B -m src.webapp.app --host $Host --port $Port

