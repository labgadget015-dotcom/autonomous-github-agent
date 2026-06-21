# Run the autonomous agent using Python directly

**Instead of:** `autonomous-agent config-check`

**Use:** `python -m autonomous_agent.cli config-check`

## All Commands (Updated)

```powershell
# Check configuration
python -m autonomous_agent.cli config-check

# List agents
python -m autonomous_agent.cli list-agents

# Health check
python -m autonomous_agent.cli health-check --repo octocat/Hello-World

# Analyze repository
python -m autonomous_agent.cli analyze --repo owner/repo

# Review PRs
python -m autonomous_agent.cli review --repo owner/repo

# View logs
python -m autonomous_agent.cli logs --limit 10

# Show help
python -m autonomous_agent.cli --help
```

## Why This Happens

Windows Store Python doesn't always add the Scripts folder to PATH correctly.

Using `python -m autonomous_agent.cli` runs the CLI module directly and works every time!

## Quick Alias (Optional)

To make it shorter, you can create an alias in PowerShell:

```powershell
Set-Alias -Name aa -Value "python -m autonomous_agent.cli"
```

Then you can just type:
```powershell
aa config-check
aa list-agents
```
