# start.ps1 - One-click launcher for the Agentic Text-to-SQL Engine
# Usage: Right-click > Run with PowerShell  OR  .\start.ps1 in terminal

$ErrorActionPreference = "Continue"
$ProjectDir = $PSScriptRoot
$VenvDir = Join-Path (Split-Path $ProjectDir -Parent) ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Agentic Text-to-SQL Engine - Launcher" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# -- Step 1: Check Docker --
Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    docker info *> $null
} catch {
    Write-Host "  ERROR: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  Docker is running." -ForegroundColor Green

# -- Step 2: Start PostgreSQL --
Write-Host "[2/5] Starting PostgreSQL container..." -ForegroundColor Yellow
docker compose -f "$ProjectDir\docker-compose.yml" up -d 2>$null
Start-Sleep -Seconds 3

# Wait for PostgreSQL to be ready (max 30 seconds)
$maxWait = 30
$waited = 0
while ($waited -lt $maxWait) {
    $ready = docker exec sql-agent-project-postgres-1 pg_isready -U admin -d business_sandbox 2>&1
    if ($ready -match "accepting connections") { break }
    Start-Sleep -Seconds 2
    $waited += 2
}
if ($waited -ge $maxWait) {
    Write-Host "  ERROR: PostgreSQL did not start in time." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  PostgreSQL is ready on port 5432." -ForegroundColor Green

# -- Step 3: Ensure virtual environment exists --
Write-Host "[3/5] Checking Python environment..." -ForegroundColor Yellow
if (-Not (Test-Path $PythonExe)) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    python -m venv $VenvDir
    & $PipExe install -q -r "$ProjectDir\requirements.txt"
}
Write-Host "  Python environment ready." -ForegroundColor Green

# -- Step 4: Start FastAPI backend --
Write-Host "[4/5] Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Yellow
$env:PYTHONPATH = $ProjectDir
$apiProcess = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory $ProjectDir `
    -PassThru -WindowStyle Normal
Start-Sleep -Seconds 3
Write-Host "  FastAPI backend started (PID: $($apiProcess.Id))." -ForegroundColor Green

# -- Step 5: Start Streamlit frontend --
Write-Host "[5/5] Starting Streamlit dashboard on http://localhost:8501 ..." -ForegroundColor Yellow
$uiProcess = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "streamlit", "run", "ui/app.py", "--server.headless", "true" `
    -WorkingDirectory $ProjectDir `
    -PassThru -WindowStyle Normal
Start-Sleep -Seconds 2
Write-Host "  Streamlit dashboard started (PID: $($uiProcess.Id))." -ForegroundColor Green

# -- Done --
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  ALL SYSTEMS RUNNING" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API:       http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "  Press Enter to STOP all services..." -ForegroundColor Yellow
Write-Host ""

# Open the dashboard in the default browser
Start-Process "http://localhost:8501"

# Wait for user to press Enter, then clean up
Read-Host | Out-Null

Write-Host ""
Write-Host "Shutting down..." -ForegroundColor Yellow

# Stop FastAPI and Streamlit
if (!$apiProcess.HasExited) { Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue }
if (!$uiProcess.HasExited) { Stop-Process -Id $uiProcess.Id -Force -ErrorAction SilentlyContinue }

# Stop PostgreSQL container
docker compose -f "$ProjectDir\docker-compose.yml" down 2>$null

Write-Host "All services stopped. Goodbye!" -ForegroundColor Green
