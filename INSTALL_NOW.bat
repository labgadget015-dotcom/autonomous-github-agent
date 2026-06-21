@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: AUTONOMOUS GITHUB AGENT - COMPLETE INSTALLATION
:: This script does EVERYTHING - just double-click and wait!
:: ============================================================================

cd /d "%~dp0"

echo.
echo ========================================================================
echo                AUTONOMOUS GITHUB AGENT - AUTO INSTALLER
echo ========================================================================
echo.
echo This will install the complete framework automatically.
echo Please wait 2-3 minutes for completion...
echo.
pause

:: Step 1: Run installation scripts
echo.
echo [1/5] Creating directory structure...
python quick_setup.py
if errorlevel 1 (
    echo WARNING: Some directories may already exist - continuing...
)

echo.
echo [2/5] Creating core modules...
python create_core_files.py
if errorlevel 1 (
    echo ERROR: Failed to create core modules!
    echo Please check that Python is installed and working.
    pause
    exit /b 1
)

echo.
echo [3/5] Creating specialized agents...
python create_agents.py
if errorlevel 1 (
    echo ERROR: Failed to create agents!
    pause
    exit /b 1
)

echo.
echo [4/5] Creating CLI interface and tests...
python create_cli.py
if errorlevel 1 (
    echo ERROR: Failed to create CLI!
    pause
    exit /b 1
)

echo.
echo [5/5] Installing package with pip...
pip install -e .
if errorlevel 1 (
    echo ERROR: Package installation failed!
    echo You may need to run: pip install -e .
    pause
    exit /b 1
)

:: Create .env from template
echo.
echo Creating .env configuration file...
if not exist .env (
    copy .env.example .env >nul 2>&1
    echo Created .env from template
) else (
    echo .env already exists
)

:: Verify installation
echo.
echo ========================================================================
echo                    INSTALLATION COMPLETE!
echo ========================================================================
echo.
echo Next steps:
echo.
echo 1. CONFIGURE YOUR TOKENS (REQUIRED):
echo    Edit the .env file and add:
echo    - GITHUB_TOKEN=ghp_your_token_here
echo    - OPENAI_API_KEY=sk_your_key_here
echo.
echo    Get tokens from:
echo    - GitHub: https://github.com/settings/tokens
echo    - OpenAI: https://platform.openai.com/api-keys
echo.
echo 2. VERIFY INSTALLATION:
echo    autonomous-agent config-check
echo    autonomous-agent list-agents
echo.
echo 3. TEST IT:
echo    autonomous-agent health-check --repo octocat/Hello-World
echo.
echo ========================================================================
echo.
echo Press any key to verify installation...
pause >nul

:: Run verification
python verify_installation.py

echo.
echo Installation process complete!
echo See QUICKSTART.md for usage examples.
echo.
pause
