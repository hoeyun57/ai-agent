$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$BackendPython = Join-Path $Backend ".venv\Scripts\python.exe"
$PnpmCommand = "pnpm.cmd"

function Test-OllamaReady {
  try {
    Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 2 | Out-Null
    return $true
  } catch {
    return $false
  }
}

if (!(Test-Path $BackendPython)) {
  Write-Error "Backend virtual environment was not found. Create it and install dependencies first."
}

if (!(Get-Command "ollama.exe" -ErrorAction SilentlyContinue) -and !(Get-Command "ollama" -ErrorAction SilentlyContinue)) {
  Write-Error "ollama was not found. Install Ollama first, then run this script again."
}

if (Test-OllamaReady) {
  Write-Host "[INFO] Ollama is already running at http://localhost:11434"
} else {
  Write-Host "[INFO] Ollama is not running. Starting Ollama server..."
  Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "ollama serve" -WindowStyle Normal
  $ollamaStarted = $false
  for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    if (Test-OllamaReady) {
      $ollamaStarted = $true
      break
    }
  }
  if ($ollamaStarted) {
    Write-Host "[OK] Ollama server is running."
  } else {
    Write-Warning "Ollama server was started, but it did not respond yet. Keep the Ollama window open and check it if model calls fail."
  }
}

if (!(Get-Command "pnpm.cmd" -ErrorAction SilentlyContinue)) {
  if (Get-Command "corepack.cmd" -ErrorAction SilentlyContinue) {
    Write-Host "[INFO] pnpm.cmd was not found. Falling back to Corepack."
    $PnpmCommand = "corepack.cmd pnpm"
  } else {
    Write-Error "pnpm.cmd was not found and corepack.cmd is unavailable. Install Node.js LTS, then run: corepack enable"
  }
}

if (!(Test-Path (Join-Path $Frontend "node_modules"))) {
  Write-Host "[INFO] Frontend dependencies are not installed. Installing now..."
  Push-Location $Frontend
  cmd.exe /c "$PnpmCommand install"
  Pop-Location
}

Write-Host "[INFO] Starting backend at http://localhost:8000"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$Backend`" && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

Write-Host "[INFO] Starting frontend at http://localhost:5173"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$Frontend`" && $PnpmCommand dev"

Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Host "[OK] Backend and frontend were started in separate windows."
Write-Host "Close each server window or press Ctrl+C in each window to stop them."
