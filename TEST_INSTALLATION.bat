@echo off
echo.
echo ========================================================================
echo              TESTING YOUR AUTONOMOUS GITHUB AGENT
echo ========================================================================
echo.

cd /d "%~dp0"

echo [TEST 1/5] Checking configuration...
echo.
autonomous-agent config-check
echo.

if errorlevel 1 (
    echo.
    echo ❌ Configuration check FAILED!
    echo.
    echo This usually means:
    echo   - Tokens are not set correctly in .env file
    echo   - There are extra spaces or quotes
    echo   - The .env file wasn't saved
    echo.
    echo Please run: CONFIGURE_WIZARD.bat
    echo.
    pause
    exit /b 1
)

echo ✅ Configuration OK!
echo.
pause

echo.
echo [TEST 2/5] Listing available agents...
echo.
autonomous-agent list-agents
echo.
pause

echo.
echo [TEST 3/5] Running health check on test repository...
echo This will analyze GitHub's "Hello-World" demo repository.
echo.
autonomous-agent health-check --repo octocat/Hello-World
echo.

if errorlevel 1 (
    echo.
    echo ❌ Health check failed!
    echo Check the error message above.
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Health check completed!
echo.
pause

echo.
echo [TEST 4/5] Running security scan on test repository...
echo.
autonomous-agent analyze --repo octocat/Hello-World --agent security
echo.
pause

echo.
echo [TEST 5/5] Viewing audit logs...
echo.
autonomous-agent logs --limit 5
echo.

echo.
echo ========================================================================
echo              ✅ ALL TESTS PASSED!
echo ========================================================================
echo.
echo Your Autonomous GitHub Agent is fully operational!
echo.
echo You can now use it on your own repositories:
echo.
echo   autonomous-agent analyze --repo YOUR_USERNAME/YOUR_REPO
echo   autonomous-agent review --repo YOUR_USERNAME/YOUR_REPO
echo   autonomous-agent --help
echo.
echo See NEXT_STEPS.md for more usage examples.
echo.
pause
