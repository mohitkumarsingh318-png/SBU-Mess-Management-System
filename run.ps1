# SBU Mess Management - Automated Run Script
# This script sets up the virtual environment and runs the application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SBU Mess Management System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "[*] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}
else {
    Write-Host "[OK] Virtual environment found" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[*] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "[OK] Virtual environment activated" -ForegroundColor Green

# Install/upgrade requirements
Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# Start the application
Write-Host ""
Write-Host "[*] Starting application..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Open browser: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host ""
Write-Host "Login Credentials:" -ForegroundColor Cyan
Write-Host "  Admin:   admin / admin123" -ForegroundColor White
Write-Host "  Staff:   staff / staff123" -ForegroundColor White
Write-Host "  Student: student1 / student123" -ForegroundColor White
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python run.py

Write-Host ""
Write-Host "Server stopped." -ForegroundColor Yellow
