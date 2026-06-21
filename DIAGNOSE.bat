@echo off
echo.
echo ========================================================================
echo              DIAGNOSTIC CHECK - Let's see what's happening
echo ========================================================================
echo.

cd /d "%~dp0"

echo [CHECK 1] Verifying we're in the right directory...
echo Current directory: %CD%
echo.
if not exist "pyproject.toml" (
    echo ERROR: Not in the autonomous-github-agent directory!
    echo Please navigate to: C:\Users\aw789\autonomous-github-agent
    pause
    exit /b 1
)
echo ✅ Correct directory
echo.
pause

echo [CHECK 2] Checking if Python is installed...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    pause
    exit /b 1
)
echo ✅ Python is installed
echo.
pause

echo [CHECK 3] Checking if package is installed...
python -c "import autonomous_agent; print('Package version:', autonomous_agent.__version__)"
if errorlevel 1 (
    echo ERROR: Package not installed!
    echo Running: pip install -e .
    echo.
    pip install -e .
    echo.
    if errorlevel 1 (
        echo Installation failed!
        pause
        exit /b 1
    )
)
echo ✅ Package is installed
echo.
pause

echo [CHECK 4] Checking if autonomous-agent command works...
autonomous-agent --help > nul 2>&1
if errorlevel 1 (
    echo ERROR: autonomous-agent command not found!
    echo Trying to reinstall...
    pip install -e .
    pause
)
echo ✅ Command is available
echo.
pause

echo [CHECK 5] Checking .env file exists...
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Creating from template...
    copy .env.example .env
    echo.
    echo Please edit .env file and add your tokens!
    notepad .env
    pause
)
echo ✅ .env file exists
echo.
pause

echo [CHECK 6] Checking .env file has tokens configured...
findstr /C:"GITHUB_TOKEN=ghp_" .env > nul
if errorlevel 1 (
    echo WARNING: GitHub token may not be configured
    echo Opening .env for you to check...
    notepad .env
    pause
)
echo ✅ GitHub token appears to be set
echo.

findstr /C:"OPENAI_API_KEY=sk-" .env > nul
if errorlevel 1 (
    echo WARNING: OpenAI API key may not be configured
    echo Opening .env for you to check...
    notepad .env
    pause
)
echo ✅ OpenAI API key appears to be set
echo.
pause

echo [CHECK 7] Running actual config check...
echo.
autonomous-agent config-check
echo.
if errorlevel 1 (
    echo Config check failed! See error above.
    pause
    exit /b 1
)
echo.
echo ✅ Config check passed!
echo.
pause

echo.
echo ========================================================================
echo              ✅ ALL DIAGNOSTICS PASSED!
echo ========================================================================
echo.
echo Everything looks good! You should be able to run:
echo.
echo   autonomous-agent list-agents
echo   autonomous-agent health-check --repo octocat/Hello-World
echo.
echo Ready to try?
echo.
pause

echo.
echo Running a live test on GitHub's demo repository...
echo.
autonomous-agent health-check --repo octocat/Hello-World
echo.

if errorlevel 1 (
    echo.
    echo Test failed! Check the error above.
    echo.
) else (
    echo.
    echo ========================================================================
    echo              🎉 SUCCESS! EVERYTHING IS WORKING!
    echo ========================================================================
    echo.
)

pause
