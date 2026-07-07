@echo off
setlocal

set "ROOT=%~dp0.."
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "BACKEND_PY=%BACKEND%\.venv\Scripts\python.exe"
set "PNPM_CMD=pnpm.cmd"

if not exist "%BACKEND_PY%" (
  echo [ERROR] Backend virtual environment was not found.
  echo Run this first:
  echo   cd "%BACKEND%"
  echo   py -3.12 -m venv .venv
  echo   .venv\Scripts\python.exe -m pip install -e ".[test]"
  exit /b 1
)

where pnpm.cmd >nul 2>nul
if errorlevel 1 (
  where corepack.cmd >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] pnpm.cmd was not found and corepack.cmd is unavailable.
    echo Install Node.js LTS, then run:
    echo   corepack enable
    exit /b 1
  )
  echo [INFO] pnpm.cmd was not found. Falling back to Corepack.
  set "PNPM_CMD=corepack.cmd pnpm"
)

if not exist "%FRONTEND%\node_modules" (
  echo [INFO] Frontend dependencies are not installed. Installing now...
  pushd "%FRONTEND%"
  call %PNPM_CMD% install
  if errorlevel 1 exit /b 1
  popd
)

echo [INFO] Starting backend at http://localhost:8000
start "HWPX AI Agent Backend" cmd /k "cd /d ""%BACKEND%"" && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

echo [INFO] Starting frontend at http://localhost:5173
start "HWPX AI Agent Frontend" cmd /k "cd /d ""%FRONTEND%"" && %PNPM_CMD% dev"

timeout /t 3 /nobreak >nul
start "" "http://localhost:5173"

echo [OK] Backend and frontend were started in separate windows.
echo Close each server window or press Ctrl+C in each window to stop them.
