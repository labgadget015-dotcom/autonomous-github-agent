# 🚀 QUICK START - Autonomous GitHub Agent

## ONE COMMAND TO INSTALL

```cmd
cd C:\Users\aw789\autonomous-github-agent
python install.py
```

**OR double-click:** `RUN_INSTALL.bat`

## CONFIGURE (REQUIRED)

Edit `.env` file:
```env
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk_your_key_here
```

Get tokens:
- GitHub: https://github.com/settings/tokens
- OpenAI: https://platform.openai.com/api-keys

## VERIFY

```cmd
autonomous-agent config-check
autonomous-agent list-agents
```

## USE IT

```cmd
# Analyze repository
autonomous-agent analyze --repo owner/repo

# Review PRs
autonomous-agent review --repo owner/repo

# Health check
autonomous-agent health-check --repo owner/repo

# View logs
autonomous-agent logs
```

## WHAT YOU GET

✅ 7 AI Agents:
- Health Monitor
- Code Reviewer
- Issue Manager  
- Branch Manager
- Security Scanner
- Workflow Optimizer
- Documentation Generator

✅ Full automation with safety controls
✅ Complete audit logging
✅ CLI + GitHub Actions integration

## TROUBLESHOOTING

**ModuleNotFoundError?**
```cmd
pip install -e .
```

**Config issues?**
```cmd
autonomous-agent config-check
```

**Need help?**
- See INSTALL.md
- See START_HERE.md
- Run: `autonomous-agent --help`

---

**Time to install:** ~5 minutes
**Ready to use:** Immediately after config
