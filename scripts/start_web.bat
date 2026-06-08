@echo off
setlocal

set VENV_DIR=.venv
if not "%~1"=="" set VENV_DIR=%~1

if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo Virtual environment not found at %VENV_DIR%.
  echo Run: powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
  exit /b 1
)

if "%MIGRATION_RUNTIME_ROOT%"=="" set MIGRATION_RUNTIME_ROOT=%LOCALAPPDATA%\DigitalMigrationRuntime
if "%MIGRATION_WEB_HOST%"=="" set MIGRATION_WEB_HOST=127.0.0.1
if "%MIGRATION_WEB_PORT%"=="" set MIGRATION_WEB_PORT=8765

if not exist "%MIGRATION_RUNTIME_ROOT%" mkdir "%MIGRATION_RUNTIME_ROOT%"

echo Runtime root: %MIGRATION_RUNTIME_ROOT%
echo Web UI: http://%MIGRATION_WEB_HOST%:%MIGRATION_WEB_PORT%

"%VENV_DIR%\Scripts\python.exe" -B -m src.webapp.app --host %MIGRATION_WEB_HOST% --port %MIGRATION_WEB_PORT%

