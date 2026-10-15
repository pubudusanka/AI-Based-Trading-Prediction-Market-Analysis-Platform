# Local Development Environment Setup Script (PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " AI Trading Platform - Local Environment Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Environment file check
if (-not (Test-Path ".env")) {
    Write-Host "[1/4] Copying .env.example to .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
} else {
    Write-Host "[1/4] .env already exists." -ForegroundColor Green
}

# 2. Python Virtual Environment
Write-Host "[2/4] Setting up Python virtual environment in ml/..." -ForegroundColor Yellow
if (-not (Test-Path "ml/venv")) {
    python -m venv ml/venv
    Write-Host "Virtual environment created at ml/venv" -ForegroundColor Green
}
& ml/venv/Scripts/python.exe -m pip install --upgrade pip
& ml/venv/Scripts/python.exe -m pip install -r ml/requirements.txt

# 3. Frontend Dependencies
Write-Host "[3/4] Installing Next.js frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Setup Complete! You can now run docker-compose or individual services." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
