# 🚀 QUICK START - Autonomous GitHub Agent

## ONE-LINE INSTALLATION
```cmd
cd C:\Users\aw789\autonomous-github-agent && python install.py
```

**Alternative:** Double-click `SIMPLE_INSTALL.bat`

---

## INSTALLATION SCRIPTS AVAILABLE

1. **install.py** - Main installer (RECOMMENDED) ⭐
2. **SIMPLE_INSTALL.bat** - One-click batch file
3. **run_install.js** - Node.js wrapper
4. **run_install.go** - Go wrapper

---

## AFTER INSTALLATION

### 1. Configure API Keys (REQUIRED)
Edit `.env` file:
```env
GITHUB_TOKEN=ghp_your_actual_token_here
OPENAI_API_KEY=sk-your_actual_key_here
```

### 2. Verify
```cmd
python verify_installation.py
```

### 3. Test CLI
```cmd
autonomous-agent --help
autonomous-agent list-agents
```

---

## WHAT GETS INSTALLED

- ✅ 8 specialized AI agents
- ✅ GitHub client integration
- ✅ LLM provider (OpenAI/Anthropic)
- ✅ CLI tool (`autonomous-agent`)
- ✅ Database & logging
- ✅ Complete test suite

---

## DIRECTORY STRUCTURE
```
autonomous_agent/
  ├── core/         (orchestrator, github_client, config)
  ├── agents/       (8 specialized agents)
  └── utils/        (helper functions)
tests/              (test suite)
config/             (configuration files)
logs/               (log files)
```

---

## CLI COMMANDS (After Installation)

```cmd
# List all agents
autonomous-agent list-agents

# Check configuration
autonomous-agent config-check

# Health check a repository
autonomous-agent health-check --repo owner/repo

# Analyze issues
autonomous-agent analyze-issues --repo owner/repo

# Review pull requests
autonomous-agent review-pr --repo owner/repo --pr 123

# Code quality check
autonomous-agent code-quality --repo owner/repo

# Security scan
autonomous-agent security-scan --repo owner/repo
```

---

## TROUBLESHOOTING

**Problem:** `python: command not found`
**Solution:** Use full path or add Python to PATH

**Problem:** `pip install fails`
**Solution:** `python -m pip install -e . --force-reinstall`

**Problem:** `CLI not available`
**Solution:** Run `pip install -e .` again

**Problem:** `.env file missing`
**Solution:** `copy .env.example .env`

---

## FILE LOCATIONS

- **Installation scripts:** `C:\Users\aw789\autonomous-github-agent\`
- **Main installer:** `install.py`
- **Verification:** `verify_installation.py`
- **Configuration:** `.env`
- **Full guide:** `INSTALLATION_REPORT.md`
- **This file:** `QUICK_START.md`

---

## SUPPORT FILES

- **SUMMARY.md** - Installation summary
- **INSTALLATION_REPORT.md** - Comprehensive guide
- **QUICK_START.md** - This file
- **verify_installation.py** - Post-install verification

---

## TIME REQUIRED

- Installation: ~2-3 minutes
- Configuration: ~1 minute
- Total: **~5 minutes**

---

## READY TO GO?

```cmd
cd C:\Users\aw789\autonomous-github-agent
python install.py
```

That's it! 🎉
