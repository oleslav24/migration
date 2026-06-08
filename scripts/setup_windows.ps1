param(
  [string]$PythonExe = "py -3.12",
  [string]$VenvDir = ".venv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $VenvDir)) {
  Invoke-Expression "$PythonExe -m venv $VenvDir --without-pip"
  Invoke-Expression "$PythonExe -m pip --python `"$VenvDir\Scripts\python.exe`" install --upgrade pip"
}

& "$VenvDir\Scripts\python.exe" -m pip install -r requirements.txt

Write-Host "Environment is ready: $VenvDir"

