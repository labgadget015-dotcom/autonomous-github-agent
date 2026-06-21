@echo off
echo.
echo ========================================================================
echo              TOKEN CONFIGURATION WIZARD
echo ========================================================================
echo.
echo This wizard will help you configure your API tokens.
echo.
echo You need TWO tokens:
echo   1. GitHub Personal Access Token (starts with ghp_)
echo   2. OpenAI API Key (starts with sk-)
echo.
echo ========================================================================
echo                 STEP 1: GET GITHUB TOKEN
echo ========================================================================
echo.
echo 1. Open your browser and go to:
echo    https://github.com/settings/tokens
echo.
echo 2. Click "Generate new token (classic)"
echo.
echo 3. Give it a name: "Autonomous Agent"
echo.
echo 4. Check the box: [X] repo (this checks all sub-items)
echo.
echo 5. Optionally check: [X] workflow
echo.
echo 6. Click "Generate token" at the bottom
echo.
echo 7. Copy the token (looks like: ghp_xxxxxxxxxxxx...)
echo.
pause
echo.
echo ========================================================================
echo                 STEP 2: GET OPENAI API KEY
echo ========================================================================
echo.
echo 1. Open your browser and go to:
echo    https://platform.openai.com/api-keys
echo.
echo 2. Sign in to your OpenAI account
echo.
echo 3. Click "+ Create new secret key"
echo.
echo 4. Give it a name: "Autonomous Agent"
echo.
echo 5. Click "Create secret key"
echo.
echo 6. Copy the key (looks like: sk-proj-xxxxx... or sk-xxxxx...)
echo.
echo NOTE: If you don't have OpenAI, you can use Anthropic Claude:
echo       https://console.anthropic.com/
echo       (Get a key that starts with: sk-ant-xxxxx...)
echo.
pause
echo.
echo ========================================================================
echo                 STEP 3: EDIT THE .ENV FILE
echo ========================================================================
echo.
echo Opening .env file in Notepad...
echo.
echo When Notepad opens:
echo.
echo 1. Find the line: GITHUB_TOKEN=ghp_your_github_personal_access_token_here
echo    Replace the part after = with YOUR GitHub token
echo.
echo 2. Find the line: OPENAI_API_KEY=sk-your_openai_api_key_here
echo    Replace the part after = with YOUR OpenAI key
echo.
echo 3. Save the file (Ctrl+S or File -^> Save)
echo.
echo 4. Close Notepad
echo.
pause

:: Open .env in Notepad
if exist .env (
    notepad .env
) else (
    echo ERROR: .env file not found!
    echo Creating it now from template...
    copy .env.example .env
    notepad .env
)

echo.
echo ========================================================================
echo                 STEP 4: VERIFY CONFIGURATION
echo ========================================================================
echo.
echo Running configuration check...
echo.

autonomous-agent config-check

if errorlevel 1 (
    echo.
    echo ⚠️  Configuration check failed!
    echo.
    echo Common issues:
    echo   - Tokens not pasted correctly
    echo   - Extra spaces or quotes in .env file
    echo   - .env file not saved
    echo.
    echo Please check the .env file and try again.
    echo.
) else (
    echo.
    echo ========================================================================
    echo                 ✅ CONFIGURATION SUCCESSFUL!
    echo ========================================================================
    echo.
    echo Your autonomous GitHub agent is now ready to use!
    echo.
    echo Try these commands:
    echo.
    echo   autonomous-agent list-agents
    echo   autonomous-agent health-check --repo octocat/Hello-World
    echo   autonomous-agent analyze --repo YOUR_USERNAME/YOUR_REPO
    echo.
)

pause
