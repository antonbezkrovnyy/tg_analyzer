# TG Analyzer - Quick Start Script for Windows
# Run this script to set up the development environment

Write-Host "=== TG Analyzer Quick Start ===" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1 | Out-String
$pythonVersion = $pythonVersion.Trim()

if ($pythonVersion -match "Python 3\.(1[1-9]|[2-9][0-9])") {
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
    exit 1
}

# Create virtual environment
if (Test-Path ".venv") {
    Write-Host "[OK] Virtual environment already exists" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements-dev.txt
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# Create .env file if not exists
if (Test-Path ".env") {
    Write-Host "[OK] .env file already exists" -ForegroundColor Green
} else {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "[OK] .env file created - EDIT IT AND ADD YOUR GIGACHAT_API_KEY!" -ForegroundColor Yellow
}

# Install pre-commit hooks
Write-Host "Installing pre-commit hooks..." -ForegroundColor Yellow
pre-commit install
Write-Host "[OK] Pre-commit hooks installed" -ForegroundColor Green

# Run code quality checks
Write-Host ""
Write-Host "Running code quality checks..." -ForegroundColor Yellow
Write-Host "  - black..." -NoNewline
black . --check --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host " [OK]" -ForegroundColor Green
} else {
    Write-Host " [WARN] (run 'black .' to format)" -ForegroundColor Yellow
}

Write-Host "  - isort..." -NoNewline
isort . --check --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host " [OK]" -ForegroundColor Green
} else {
    Write-Host " [WARN] (run 'isort .' to fix imports)" -ForegroundColor Yellow
}

Write-Host "  - flake8..." -NoNewline
flake8 . --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host " [OK]" -ForegroundColor Green
} else {
    Write-Host " [WARN] (check flake8 output)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env and add your GIGACHAT_API_KEY"
Write-Host "2. Run: python -m src.main analyze --chat ru_python --date 2025-11-06"
Write-Host "3. Check output/ directory for results"
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  pytest                  # Run tests"
Write-Host "  black . && isort .      # Format code"
Write-Host "  mypy .                  # Type checking"
Write-Host "  docker-compose up       # Run with Docker"
Write-Host ""
