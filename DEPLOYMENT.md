# 🎯 Autonomous GitHub Agent - Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Installation Complete
- [ ] Run `python install.py` (or manual setup scripts)
- [ ] All directories created
- [ ] All Python files in place
- [ ] Dependencies installed (`pip install -e .`)

### 2. Configuration
- [ ] `.env` file created from `.env.example`
- [ ] `GITHUB_TOKEN` set (with repo, workflow permissions)
- [ ] LLM API key set (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
- [ ] Automation level configured
- [ ] Run `autonomous-agent config-check` to verify

### 3. Testing
- [ ] `autonomous-agent list-agents` shows all 7 agents
- [ ] `autonomous-agent health-check --repo test/repo` works
- [ ] `pytest` runs successfully (optional)

### 4. Documentation
- [ ] README.md reviewed
- [ ] INSTALL.md read
- [ ] Architecture docs checked

## 🚀 Deployment Options

### Option A: Local/Manual Use
```bash
# Run on-demand
autonomous-agent analyze --repo owner/repo
autonomous-agent review --repo owner/repo --pr 123
autonomous-agent monitor --repo owner/repo
```

### Option B: GitHub Actions (Recommended)
1. Copy workflows to `.github/workflows/` in your target repo
2. Add secrets to repository:
   - `GITHUB_TOKEN` (auto-provided)
   - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
3. Enable workflows
4. Agents run automatically on PR events and schedule

### Option C: Continuous Server
```bash
# Run as background service
autonomous-agent monitor --repo owner/repo &

# Or use systemd/pm2/supervisor
```

## 📊 Monitoring

### View Activity
```bash
# Check audit logs
autonomous-agent logs --limit 50

# Filter by repository
autonomous-agent logs --repo owner/repo

# Check configuration
autonomous-agent config-check
```

### Database
- Audit logs stored in `autonomous_agent.db`
- Backup regularly
- Review rollback instructions

## 🛡️ Security Considerations

- [ ] GitHub token has minimum required permissions
- [ ] LLM API keys stored securely (not in code)
- [ ] `.env` file in `.gitignore`
- [ ] Automation level appropriate (start with `semi-auto`)
- [ ] Review audit logs regularly
- [ ] Enable branch protection on default branch

## 🔧 Customization

### Enable/Disable Agents
Edit `.env`:
```bash
# Comma-separated list
ENABLED_AGENTS=health_monitor,code_reviewer,security_scanner
```

### Adjust Automation Level
```bash
AUTOMATION_LEVEL=manual      # All actions require approval
AUTOMATION_LEVEL=semi-auto   # Destructive actions require approval (recommended)
AUTOMATION_LEVEL=full-auto   # Full automation (use with caution)
```

### Add Custom Agent
1. Create `autonomous_agent/agents/your_agent.py`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Add to enabled agents list
5. Update orchestrator to load it

## 📈 Success Metrics

Track these to measure effectiveness:
- PRs reviewed automatically
- Issues triaged and labeled
- Stale branches cleaned up
- Security vulnerabilities detected
- Documentation updates
- Audit log entries
- Time saved on manual reviews

## 🆘 Troubleshooting

### Common Issues

**Agent not found**
```bash
# Ensure installed correctly
pip install -e .
python -c "import autonomous_agent; print('OK')"
```

**GitHub API rate limit**
```bash
# Check rate limit in audit logs
# Adjust polling frequency
# Use conditional execution
```

**LLM API failures**
```bash
# Check API key in .env
# Verify credits/quota
# Test with: autonomous-agent config-check
```

**Permission denied**
```bash
# Ensure GitHub token has:
# - repo (full)
# - workflow (if modifying workflows)
# - admin:org (if managing org repos)
```

## 🎓 Best Practices

1. **Start Small**: Begin with 1-2 agents, expand gradually
2. **Monitor First**: Use `semi-auto` mode initially
3. **Review Logs**: Check audit logs daily at first
4. **Test on Non-Critical Repos**: Validate before production
5. **Keep Updated**: Update dependencies regularly
6. **Backup Audit DB**: Regular backups of `autonomous_agent.db`
7. **Document Custom Rules**: Track any custom configurations

## 📞 Support Resources

- **Documentation**: See `docs/` directory
- **Examples**: Check `INSTALL.md` and `README.md`
- **Audit Logs**: `autonomous-agent logs`
- **Configuration**: `autonomous-agent config-check`
- **Agent List**: `autonomous-agent list-agents`

## 🎉 You're Ready!

Once all checks are complete:
1. Start with health checks and analysis
2. Enable automated PR reviews
3. Gradually increase automation level
4. Monitor and adjust based on results
5. Enjoy your autonomous GitHub management! 🚀

---

**Remember**: The system is designed to assist, not replace human judgment. Always review critical actions and maintain oversight of automated operations.
