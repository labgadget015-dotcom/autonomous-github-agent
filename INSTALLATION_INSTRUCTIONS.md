# Autonomous GitHub Agent - Installation Instructions

## Current Environment Status

PowerShell 6+ (pwsh) is not available in the current environment, but we have prepared multiple installation methods for you.

## Quick Installation (Choose One Method)

### METHOD 1: Using Python Script (RECOMMENDED)
```cmd
cd C:\Users\aw789\autonomous-github-agent
python RUN_INSTALLATION.py
```

### METHOD 2: Using install.py (Alternative)
```cmd
cd C:\Users\aw789\autonomous-github-agent
python install.py
```

### METHOD 3: Using Master Install Script
```cmd
cd C:\Users\aw789\autonomous-github-agent
python master_install.py
```

### METHOD 4: Manual Step-by-Step
Run these commands in sequence in Command Prompt (cmd.exe):

```cmd
cd C:\Users\aw789\autonomous-github-agent

REM Step 1: Create directory structure
python quick_setup.py

REM Step 2: Create core modules
python create_core_files.py

REM Step 3: Create agent modules
python create_agents.py

REM Step 4: Create CLI and tests
python create_cli.py

REM Step 5: Install the package
pip install -e .

REM Step 6: Create .env file (copy template)
copy .env.example .env

REM Step 7: Verify installation
python verify_installation.py
```

### METHOD 5: Using Batch File
Simply double-click:
```
C:\Users\aw789\autonomous-github-agent\run_install.bat
```

Or run in Command Prompt:
```cmd
C:\Users\aw789\autonomous-github-agent\run_install.bat
```

## Installation Steps Explained

### Step 1: Create Directories
**Script:** `quick_setup.py`

Creates the following directory structure:
- `autonomous_agent/core/` - Core system modules
- `autonomous_agent/agents/` - Specialized agent implementations
- `autonomous_agent/utils/` - Utility functions
- `tests/` - Test suite
- `config/` - Configuration files
- `workflows/` - GitHub Actions workflows
- `docs/` - Documentation
- `logs/` - Log files

### Step 2: Create Core Modules
**Script:** `create_core_files.py`

Creates core system components:
- `core/config.py` - Configuration management using Pydantic
- `core/github_client.py` - GitHub API integration
- `core/orchestrator.py` - Main orchestration system
- `core/database.py` - Database models (SQLAlchemy)
- `core/llm_provider.py` - LLM provider integration
- `core/base_agent.py` - Base agent class
- `core/audit_logger.py` - Audit logging

### Step 3: Create Agent Modules
**Script:** `create_agents.py`

Creates specialized agents:
- `agents/health_monitor.py` - Repository health monitoring
- `agents/security_scanner.py` - Security vulnerability detection
- `agents/issue_analyzer.py` - Issue analysis
- `agents/pr_reviewer.py` - Pull request review
- `agents/code_quality.py` - Code quality analysis
- `agents/documentation.py` - Documentation generation
- `agents/test_generator.py` - Test generation
- `agents/dependency_manager.py` - Dependency management
- `agents/release_manager.py` - Release management

### Step 4: Create CLI
**Script:** `create_cli.py`

Creates command-line interface:
- `cli/main.py` - CLI main entry point
- `cli/commands.py` - CLI command definitions
- `tests/test_cli.py` - CLI tests
- `tests/test_agents.py` - Agent tests
- `tests/test_core.py` - Core module tests

### Step 5: Install Package
**Command:** `pip install -e .`

This installs the package in development mode, making it available system-wide.

### Step 6: Create .env File
**Command:** `copy .env.example .env`

Creates your configuration file. You MUST edit this file before running!

### Step 7: Verify Installation
**Script:** `verify_installation.py`

Verifies that everything was installed correctly.

## Post-Installation Configuration

After running the installation, you MUST configure the `.env` file:

### Edit .env File
```cmd
# Open the file in your editor
notepad C:\Users\aw789\autonomous-github-agent\.env
```

### Required Configuration
Add these values to your .env file:

```env
# GitHub API Token (from https://github.com/settings/tokens)
GITHUB_TOKEN=ghp_your_github_personal_access_token_here

# LLM Provider (openai, anthropic, or local)
LLM_PROVIDER=openai

# If using OpenAI
OPENAI_API_KEY=sk-your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# OR if using Anthropic
ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-opus-20240229

# Optional: Database URL
DATABASE_URL=sqlite:///./autonomous_agent.db

# Optional: Automation Level
AUTOMATION_LEVEL=semi-auto

# Optional: Logging
LOG_LEVEL=INFO
```

## Verification Commands

After installation, verify everything works:

```cmd
# Check package import
python -c "import autonomous_agent; print(f'Version: {autonomous_agent.__version__}')"

# Check CLI availability
autonomous-agent --help

# List available agents
autonomous-agent list-agents

# Check configuration
autonomous-agent config-check

# Run health check on a repository
autonomous-agent health-check --repo owner/repo
```

## Troubleshooting

### Issue: "python: command not found"
**Solution:**
- Ensure Python 3.11+ is installed
- Add Python to PATH
- Or use full path: `C:\Python311\python.exe RUN_INSTALLATION.py`

### Issue: "pip: command not found"
**Solution:**
- Use: `python -m pip install -e .`

### Issue: Permission denied
**Solution:**
- Run Command Prompt as Administrator
- Or use: `python -m pip install --user -e .`

### Issue: "ModuleNotFoundError: No module named 'autonomous_agent'"
**Solution:**
- Ensure `pip install -e .` completed successfully
- Try: `pip install -e . --force-reinstall`
- Check that you're in the correct directory

### Issue: Import errors after installation
**Solution:**
- Clear pip cache: `pip cache purge`
- Reinstall: `pip install -e . --force-reinstall --no-cache-dir`
- Check Python version: `python --version` (requires 3.11+)

## Directory Structure After Installation

```
C:\Users\aw789\autonomous-github-agent\
├── autonomous_agent/              # Main package
│   ├── __init__.py
│   ├── core/                      # Core modules
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── github_client.py
│   │   ├── orchestrator.py
│   │   ├── database.py
│   │   ├── llm_provider.py
│   │   ├── base_agent.py
│   │   └── audit_logger.py
│   ├── agents/                    # Specialized agents
│   │   ├── __init__.py
│   │   ├── health_monitor.py
│   │   ├── security_scanner.py
│   │   ├── issue_analyzer.py
│   │   ├── pr_reviewer.py
│   │   ├── code_quality.py
│   │   ├── documentation.py
│   │   ├── test_generator.py
│   │   ├── dependency_manager.py
│   │   └── release_manager.py
│   ├── cli/                       # CLI interface
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── commands.py
│   └── utils/                     # Utilities
│       └── __init__.py
├── tests/                         # Test suite
│   ├── test_cli.py
│   ├── test_agents.py
│   └── test_core.py
├── config/                        # Configuration
├── workflows/                     # GitHub Actions
├── docs/                          # Documentation
├── logs/                          # Log files
├── .env                           # YOUR CONFIG (create from .env.example)
├── .env.example                   # Configuration template
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Package configuration
├── setup.py                       # Setup script
└── README.md                      # Documentation
```

## Using the Agent

Once installed and configured, you can use the autonomous agent:

```cmd
# Show available commands
autonomous-agent --help

# List all agents
autonomous-agent list-agents

# Run health check on a repository
autonomous-agent health-check --repo github/github-cli

# Analyze a repository
autonomous-agent analyze --repo owner/repo

# Run security scan
autonomous-agent security-scan --repo owner/repo
```

## Support Resources

- **Documentation:** See README.md
- **Issues:** Check INSTALL.md for detailed install info
- **Logs:** Check `logs/agent.log` for execution logs
- **Configuration:** See `.env.example` for all available options

## Next Steps

1. ✅ Run installation script (one of the methods above)
2. ✅ Edit `.env` file with your API tokens
3. ✅ Verify with: `autonomous-agent --help`
4. ✅ Try: `autonomous-agent health-check --repo owner/repo`
5. ✅ Read README.md for usage guide

---

**Installation prepared for:** `C:\Users\aw789\autonomous-github-agent`
**Python version required:** 3.11+
**Status:** Ready to execute
