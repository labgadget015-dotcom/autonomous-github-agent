@echo off
REM Quick Setup Script for CI/CD Optimization (Windows)
REM Run this script to set up everything quickly

echo ================================
echo CI/CD Optimization - Quick Setup
echo ================================
echo.

REM Check Python version
echo 1. Checking Python version...
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    exit /b 1
)
echo OK: Python found
echo.

REM Install dependencies
echo 2. Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)
echo OK: Dependencies installed
echo.

REM Setup pre-commit hooks
echo 3. Setting up pre-commit hooks...
pre-commit install
if errorlevel 1 (
    echo WARNING: Pre-commit not installed
)
echo OK: Pre-commit hooks installed
echo.

REM Create .env from template
if not exist .env (
    echo 4. Creating .env file...
    copy .env.example .env
    echo WARNING: Please edit .env and add your API keys
    echo OK: .env created
) else (
    echo 4. .env already exists, skipping...
)
echo.

REM Validate installation
echo 5. Validating installation...
python scripts/validate-implementation.py
if errorlevel 1 (
    echo WARNING: Validation had warnings (this is OK if PyYAML not installed)
)
echo.

REM Run local tests
echo 6. Running local tests (fast mode)...
python scripts/test-local.py --fast
echo.

echo ================================
echo Setup Complete!
echo ================================
echo.
echo Next Steps:
echo 1. Edit .env and add your API keys
echo 2. Run 'python scripts/test-local.py' before committing
echo 3. Push to trigger CI/CD workflow
echo 4. Monitor at http://localhost:3000 (Grafana)
echo.
echo Documentation: docs\CICD_QUICKSTART.md
echo.
pause
