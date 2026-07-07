$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$EnvFile = Join-Path $Backend ".env"
$EnvExample = Join-Path $Backend ".env.example"

function Test-Command($Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Refresh-Path {
  $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
  $user = [Environment]::GetEnvironmentVariable("Path", "User")
  $env:Path = "$machine;$user"
}

function Install-WingetPackage($Id, $DisplayName) {
  if (Test-Command $DisplayName.Split(" ")[0].ToLower()) {
    return
  }
  if (!(Test-Command "winget")) {
    Write-Warning "winget was not found. Install $DisplayName manually."
    return
  }
  Write-Host "[INFO] Installing $DisplayName with winget..."
  winget install --id $Id --exact --silent --accept-package-agreements --accept-source-agreements
  Refresh-Path
}

Write-Host "[INFO] Checking required programs..."

if (!(Test-Command "py") -and !(Test-Command "python")) {
  Install-WingetPackage "Python.Python.3.12" "Python"
}

if (!(Test-Command "node")) {
  Install-WingetPackage "OpenJS.NodeJS.LTS" "Node.js"
}

if (!(Test-Command "git")) {
  Install-WingetPackage "Git.Git" "Git"
}

if (!(Test-Command "ollama")) {
  Install-WingetPackage "Ollama.Ollama" "Ollama"
}

Refresh-Path

if (!(Test-Command "pnpm.cmd")) {
  if (Test-Command "corepack.cmd") {
    Write-Host "[INFO] Enabling pnpm with Corepack..."
    corepack.cmd enable
    corepack.cmd prepare pnpm@latest --activate
  } elseif (Test-Command "npm.cmd") {
    Write-Host "[INFO] Installing pnpm with npm..."
    npm.cmd install -g pnpm
  } else {
    Write-Warning "pnpm could not be installed automatically because npm/corepack was not found."
  }
  Refresh-Path
}

if (!(Test-Path $EnvFile) -and (Test-Path $EnvExample)) {
  Write-Host "[INFO] Creating backend .env from .env.example..."
  Copy-Item $EnvExample $EnvFile
}

$BackendPython = Join-Path $Backend ".venv\Scripts\python.exe"
if (!(Test-Path $BackendPython)) {
  Write-Host "[INFO] Creating backend virtual environment..."
  Push-Location $Backend
  if (Test-Command "py") {
    py -3.12 -m venv .venv
  } else {
    python -m venv .venv
  }
  Pop-Location
}

Write-Host "[INFO] Installing backend dependencies..."
Push-Location $Backend
& $BackendPython -m pip install --upgrade pip
& $BackendPython -m pip install -e ".[test]"
Pop-Location

if (Test-Command "pnpm.cmd") {
  Write-Host "[INFO] Installing frontend dependencies..."
  Push-Location $Frontend
  pnpm.cmd install
  Pop-Location
} elseif (Test-Command "corepack.cmd") {
  Write-Host "[INFO] Installing frontend dependencies with Corepack..."
  Push-Location $Frontend
  corepack.cmd pnpm install
  Pop-Location
} else {
  Write-Warning "Skipping frontend dependency install because pnpm is unavailable."
}

if (Test-Command "ollama") {
  Write-Host "[INFO] Ollama models currently registered:"
  ollama list
  $models = (ollama list) -join "`n"
  if ($models -notmatch "hwpx-agent-q4" -and $models -match "qwen3\.5-deepseek-q4") {
    Write-Host "[INFO] Creating hwpx-agent-q4 alias from qwen3.5-deepseek-q4..."
    ollama cp qwen3.5-deepseek-q4:latest hwpx-agent-q4
  }
  if ($models -notmatch "hwpx-agent-q8" -and $models -match "qwen3\.5-deepseek-q8") {
    Write-Host "[INFO] Creating hwpx-agent-q8 alias from qwen3.5-deepseek-q8..."
    ollama cp qwen3.5-deepseek-q8:latest hwpx-agent-q8
  }
}

Write-Host "[OK] Setup complete."
Write-Host "Start both servers with:"
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1"

