@echo off
:: This is the SIMPLEST installation method - just double-click this file!

cd /d "%~dp0"

echo.
echo ========================================================================
echo              STARTING INSTALLATION - PLEASE WAIT
echo ========================================================================
echo.

:: Run the main installer
call INSTALL_NOW.bat

echo.
echo Installation complete!
pause
