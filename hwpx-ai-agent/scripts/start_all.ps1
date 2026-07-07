$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$BackendPython = Join-Path $Backend ".venv\Scripts\python.exe"

if (!(Test-Path $BackendPython)) {
  Write-Error "Backend virtual environment was not found. Create it and install dependencies first."
}

if (!(Get-Command "pnpm.cmd" -ErrorAction SilentlyContinue)) {
  Write-Error "pnpm.cmd was not found. Install pnpm or enable Corepack."
}

if (!(Test-Path (Join-Path $Frontend "node_modules"))) {
  Write-Host "[INFO] Frontend dependencies are not installed. Installing now..."
  Push-Location $Frontend
  pnpm.cmd install
  Pop-Location
}

Write-Host "[INFO] Starting backend at http://localhost:8000"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$Backend`" && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

Write-Host "[INFO] Starting frontend at http://localhost:5173"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$Frontend`" && pnpm.cmd dev"

Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Host "[OK] Backend and frontend were started in separate windows."
Write-Host "Close each server window or press Ctrl+C in each window to stop them."
