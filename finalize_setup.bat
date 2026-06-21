@echo off
REM Final setup script to create remaining directories and files

echo.
echo ========================================
echo   Finalizing Setup
echo ========================================
echo.

cd /d C:\Users\aw789\autonomous-github-agent

REM Create remaining directories
mkdir config 2>nul
mkdir workflows 2>nul

REM Create workflow files
echo Creating GitHub Actions workflows...

REM CI Workflow
(
echo name: CI - Autonomous Agent Tests
echo.
echo on:
echo   push:
echo     branches: [ main, develop ]
echo   pull_request:
echo     branches: [ main ]
echo.
echo jobs:
echo   test:
echo     runs-on: ubuntu-latest
echo     strategy:
echo       matrix:
echo         python-version: ["3.11", "3.12"]
echo.
echo     steps:
echo     - uses: actions/checkout@v4
echo     - name: Set up Python
echo       uses: actions/setup-python@v5
echo       with:
echo         python-version: $${{ matrix.python-version }}
echo     - name: Install dependencies
echo       run: pip install -e ".[dev]"
echo     - name: Run tests
echo       run: pytest --cov=autonomous_agent
) > workflows\ci.yml

REM Config example
(
echo github:
echo   token: ${GITHUB_TOKEN}
echo   api_url: https://api.github.com
echo.
echo llm:
echo   provider: openai
echo   api_key: ${OPENAI_API_KEY}
echo   model: gpt-4-turbo-preview
echo.
echo automation_level: semi-auto
) > config\config.example.yaml

echo.
echo ========================================
echo   ✓ Setup Complete!
echo ========================================
echo.
echo Next Steps:
echo   1. Run: python install.py
echo   2. Or manually run:
echo      - python quick_setup.py
echo      - python create_core_files.py
echo      - python create_agents.py
echo      - python create_cli.py
echo      - pip install -e .
echo.
pause
