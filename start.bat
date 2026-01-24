@echo off
REM Quick start script for Autonomous GitHub Agent (Windows)

echo ================================================
echo Autonomous GitHub Agent - Docker Quick Start
echo ================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [1/5] Checking environment configuration...
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env
        echo.
        echo IMPORTANT: Please edit .env file with your configuration before continuing!
        echo Press any key to open .env in notepad...
        pause >nul
        notepad .env
    ) else (
        echo ERROR: .env.example not found
        pause
        exit /b 1
    )
) else (
    echo .env file found
)

echo.
echo [2/5] Creating context.json if needed...
if not exist "context.json" (
    if exist "context.json.example" (
        copy context.json.example context.json
        echo Created context.json from example
    )
)

echo.
echo [3/5] Building Docker image...
docker-compose build
if %errorlevel% neq 0 (
    echo ERROR: Docker build failed
    pause
    exit /b 1
)

echo.
echo [4/5] Starting containers...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Failed to start containers
    pause
    exit /b 1
)

echo.
echo [5/5] Checking status...
docker-compose ps

echo.
echo ================================================
echo Setup complete!
echo ================================================
echo.
echo Useful commands:
echo   docker-compose logs -f agent    - View logs
echo   docker-compose down             - Stop containers
echo   docker-compose restart          - Restart containers
echo.
echo Or use the Makefile:
echo   make logs    - View logs
echo   make down    - Stop containers
echo   make restart - Restart containers
echo.
echo Press any key to exit...
pause >nul
