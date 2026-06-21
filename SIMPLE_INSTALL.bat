REM ===================================================================
REM AUTONOMOUS GITHUB AGENT - ONE-COMMAND INSTALLATION
REM ===================================================================
REM Copy and paste this entire block into Command Prompt (cmd.exe)
REM ===================================================================

@echo off
cd /d C:\Users\aw789\autonomous-github-agent
echo.
echo ========================================
echo   Installing Autonomous GitHub Agent
echo ========================================
echo.
echo Running install.py...
python install.py
echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo IMPORTANT: Edit .env file and add your API tokens
echo.
pause
