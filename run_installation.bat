@echo off
REM Complete installation script for Autonomous GitHub Agent
echo ========================================
echo   Autonomous GitHub Agent Installation
echo ========================================
echo.

cd /d C:\Users\aw789\autonomous-github-agent

echo Step 1/7: Running quick_setup.py...
python quick_setup.py
if %errorlevel% neq 0 (
    echo ERROR: quick_setup.py failed
    pause
    exit /b 1
)
echo.

echo Step 2/7: Running create_core_files.py...
python create_core_files.py
if %errorlevel% neq 0 (
    echo ERROR: create_core_files.py failed
    pause
    exit /b 1
)
echo.

echo Step 3/7: Running create_agents.py...
python create_agents.py
if %errorlevel% neq 0 (
    echo ERROR: create_agents.py failed
    pause
    exit /b 1
)
echo.

echo Step 4/7: Running create_cli.py...
python create_cli.py
if %errorlevel% neq 0 (
    echo ERROR: create_cli.py failed
    pause
    exit /b 1
)
echo.

echo Step 5/7: Installing package with pip...
pip install -e .
if %errorlevel% neq 0 (
    echo WARNING: pip install failed - may need manual intervention
)
echo.

echo Step 6/7: Creating .env file from .env.example...
if exist .env.example (
    if not exist .env (
        copy .env.example .env
        echo ✓ Created .env file
    ) else (
        echo .env file already exists, skipping...
    )
) else (
    echo WARNING: .env.example not found
)
echo.

echo Step 7/7: Verifying installation...
python -c "import sys; print(f'Python version: {sys.version}')"
python -c "try: import autonomous_agent; print(f'✓ Package imported successfully, version: {autonomous_agent.__version__}'); except Exception as e: print(f'✗ Import failed: {e}')"
echo.

echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Check the output above for any errors.
echo If pip install failed, you may need to:
echo   1. Install dependencies manually
echo   2. Check your Python environment
echo.
pause
