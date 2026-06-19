@echo off
echo Creating directory structure for Autonomous GitHub Agent...

cd /d C:\Users\aw789\autonomous-github-agent

mkdir autonomous_agent\core 2>nul
mkdir autonomous_agent\agents 2>nul
mkdir autonomous_agent\utils 2>nul
mkdir tests 2>nul
mkdir config 2>nul
mkdir workflows 2>nul
mkdir docs 2>nul
mkdir logs 2>nul

echo.
echo Directory structure created successfully!
echo.
echo Next steps:
echo 1. Run: pip install -e .
echo 2. Copy .env.example to .env and configure
echo 3. Start building!
echo.
pause
