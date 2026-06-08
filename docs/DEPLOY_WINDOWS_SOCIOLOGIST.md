# Deploy on Windows Laptop (Sociologist Guide)

## 1) Prerequisites

- Windows 10/11
- Python 3.12 installed
- ~6-8 GB free disk space for dependencies and outputs

## 2) Project setup

From project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_windows.ps1
```

This creates `.venv` and installs all dependencies.

## 3) Start web interface

Recommended (local runtime outside cloud-sync folders):

```powershell
$env:MIGRATION_RUNTIME_ROOT="$env:LOCALAPPDATA\DigitalMigrationRuntime"
powershell -ExecutionPolicy Bypass -File scripts/start_web.ps1 -Host 127.0.0.1 -Port 8765
```

Open:

- http://127.0.0.1:8765

## 4) Run pipeline from CLI (optional)

```powershell
.venv\Scripts\python.exe run_pipeline.py --config config.yaml
```

## 5) Common troubleshooting

- `PermissionError` in `tmp_write_check`:
  set `MIGRATION_RUNTIME_ROOT` to local non-synced path (example above).
- `python` command not found:
  use explicit interpreter path, e.g. `.venv\Scripts\python.exe`.
- Port already in use:
  run web with another port, e.g. `-Port 8770`.

## 6) Build a portable handoff package

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_portable_package.ps1
```

Result appears in `dist\` as folder + zip archive.
