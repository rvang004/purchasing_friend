# Windows Setup Script for Purchase Bot
# Run this in PowerShell as Administrator

Write-Host "🛒 Purchase Bot Setup" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found. Download from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install requirements
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --upgrade
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install Playwright browsers
Write-Host "🌐 Installing Playwright browsers..." -ForegroundColor Yellow
playwright install
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Playwright browsers installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install Playwright browsers" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Success!
Write-Host "✨ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Configure accounts: python main.py setup" -ForegroundColor White
Write-Host "2. Test with dry-run: python main.py run --dry-run" -ForegroundColor White
Write-Host "3. Run scheduler:     python main.py run" -ForegroundColor White
Write-Host ""
Write-Host "See QUICKSTART.md for Windows Task Scheduler setup" -ForegroundColor Cyan
