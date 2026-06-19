# GitHub Autopilot - Daily Usage Guide

## 📌 Overview

This guide covers daily operations, troubleshooting, and best practices for running GitHub Autopilot in production.

## 🚀 Quick Daily Workflow

### Morning Check (5 minutes)

```bash
# 1. Pull latest changes
cd autonomous-github-agent
git pull origin main

# 2. Review yesterday's summary
cat DAILY_SUMMARY_$(date -d "yesterday" +%Y%m%d).md

# 3. Check autopilot status
python autopilot/autopilot.py --status
```

### Generate Today's Summary (1 minute)

```bash
# Run autopilot for current day
python autopilot/autopilot.py

# Output will be saved as DAILY_SUMMARY_YYYYMMDD.md
```

### Evening Review (5 minutes)

```bash
# 1. Review generated summary
cat DAILY_SUMMARY_$(date +%Y%m%d).md

# 2. Commit and push (if auto-commit disabled)
git add DAILY_SUMMARY_*.md
git commit -m "Add daily summary for $(date +%Y-%m-%d)"
git push origin main

# 3. Check for issues or anomalies
python autopilot/autopilot.py --check-health
```

## 🛠️ Command Reference

### Basic Commands

```bash
# Generate summary for today
python autopilot/autopilot.py

# Generate summary for specific date
python autopilot/autopilot.py --date 2025-01-15

# Generate summary for date range
python autopilot/autopilot.py --start-date 2025-01-01 --end-date 2025-01-07

# Dry run (preview without saving)
python autopilot/autopilot.py --dry-run

# Verbose output
python autopilot/autopilot.py --verbose
```

### Monitoring Commands

```bash
# Check autopilot health
python autopilot/autopilot.py --check-health

# View current status
python autopilot/autopilot.py --status

# List all repositories being monitored
python autopilot/autopilot.py --list-repos

# Test GitHub API connection
python autopilot/autopilot.py --test-connection
```

### Configuration Commands

```bash
# Validate configuration
python autopilot/autopilot.py --validate-config

# Show current configuration
python autopilot/autopilot.py --show-config

# Add new repository to monitor
python autopilot/autopilot.py --add-repo owner/repo-name

# Remove repository from monitoring
python autopilot/autopilot.py --remove-repo owner/repo-name
```

## 📅 Scheduling Options

### Option 1: Cron (Linux/Mac)

Add to crontab (`crontab -e`):

```bash
# Run daily at 11:00 PM
0 23 * * * cd /path/to/autonomous-github-agent && python autopilot/autopilot.py >> /var/log/autopilot.log 2>&1
```

### Option 2: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 11:00 PM
4. Action: Start a program
5. Program: `python`
6. Arguments: `/path/to/autopilot.py`
7. Start in: `/path/to/autonomous-github-agent`

### Option 3: GitHub Actions (Cloud)

Create `.github/workflows/daily-summary.yml`:

```yaml
name: Daily Summary

on:
  schedule:
    - cron: '0 23 * * *'  # 11 PM UTC daily
  workflow_dispatch:  # Manual trigger

jobs:
  generate-summary:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python autopilot/autopilot.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - run: |
          git config user.name "GitHub Autopilot"
          git config user.email "autopilot@example.com"
          git add DAILY_SUMMARY_*.md
          git commit -m "Add daily summary for $(date +%Y-%m-%d)"
          git push
```

## 🐞 Troubleshooting

### Issue: "Authentication failed"

**Solution:**
```bash
# Check token is set
echo $GITHUB_TOKEN

# Verify token has correct permissions
python autopilot/autopilot.py --test-connection

# Regenerate token if needed
# https://github.com/settings/tokens
```

### Issue: "Rate limit exceeded"

**Solution:**
```bash
# Check rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Wait for reset or reduce check frequency in config.yaml
# Edit: check_interval_hours: 6  # Increase from 1 to 6
```

### Issue: "No activity found"

**Solution:**
```bash
# Verify date range
python autopilot/autopilot.py --start-date 2025-01-01 --end-date 2025-01-31 --verbose

# Check repository access
python autopilot/autopilot.py --list-repos

# Verify repository exists and is accessible
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/owner/repo
```

### Issue: "Script hangs"

**Solution:**
```bash
# Run with timeout
timeout 300 python autopilot/autopilot.py  # 5 minute timeout

# Check for network issues
ping github.com

# Increase timeout in config.yaml
# api:
#   timeout: 60  # Increase from 30 to 60 seconds
```

## 📊 Monitoring Dashboard

### Key Metrics to Track

1. **Execution Time**: Should be < 2 minutes for single repo
2. **API Calls**: Should stay under rate limits
3. **Success Rate**: Target 100% daily execution
4. **Error Rate**: Should be 0%

### Log Files

```bash
# View recent logs
tail -f logs/autopilot.log

# Search for errors
grep ERROR logs/autopilot.log

# Check execution history
grep "Summary generated" logs/autopilot.log | tail -10
```

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

echo "Checking GitHub Autopilot Health..."

# Check last execution
LAST_SUMMARY=$(ls -t DAILY_SUMMARY_*.md | head -1)
if [ -z "$LAST_SUMMARY" ]; then
  echo "❌ No summaries found"
  exit 1
fi

# Check if summary is from today
TODAY=$(date +%Y%m%d)
if [[ $LAST_SUMMARY == *$TODAY* ]]; then
  echo "✅ Summary generated today: $LAST_SUMMARY"
else
  echo "⚠️  Latest summary is old: $LAST_SUMMARY"
fi

# Check API connection
if python autopilot/autopilot.py --test-connection > /dev/null 2>&1; then
  echo "✅ GitHub API connection OK"
else
  echo "❌ GitHub API connection failed"
  exit 1
fi

echo "✅ All checks passed"
```

## 📝 Best Practices

### Daily Operations

1. **Review Summaries**: Always review generated summaries before sharing
2. **Check Logs**: Monitor logs for errors or warnings
3. **Validate Output**: Ensure metrics are accurate
4. **Backup Data**: Keep backups of critical summaries

### Security

1. **Token Management**:
   - Never commit `.env` files
   - Rotate tokens every 90 days
   - Use minimal required scopes
   - Store tokens in secure vaults (production)

2. **Access Control**:
   - Limit repository access to necessary repos
   - Use read-only tokens when possible
   - Review token permissions regularly

### Performance

1. **Optimize API Calls**:
   - Use caching when possible
   - Batch requests
   - Respect rate limits

2. **Resource Management**:
   - Clean up old logs (> 30 days)
   - Archive old summaries
   - Monitor disk space

### Maintenance

1. **Weekly Tasks**:
   - Review error logs
   - Check API rate limit usage
   - Validate all repositories accessible

2. **Monthly Tasks**:
   - Update dependencies: `pip install -r requirements.txt --upgrade`
   - Review and update configuration
   - Clean up old logs and summaries

3. **Quarterly Tasks**:
   - Rotate GitHub tokens
   - Review security settings
   - Update documentation

## 📦 Example Daily Summary

A good daily summary should include:

```markdown
# Daily Summary - 2025-01-15

## High Priority Activities
- 3 pull requests merged
- 5 issues closed
- 12 commits across 4 repositories

## Key Changes
- Feature: New authentication module (#PR-123)
- Fix: Critical security patch (#PR-124)
- Docs: Updated API documentation (#PR-125)

## Metrics
- Total commits: 12
- Active contributors: 4
- Files changed: 47
- Lines added: +892
- Lines removed: -234

## Next Actions
- Review remaining open PRs (2 pending)
- Address high-priority issues (3 open)
```

## 🆘 FAQ

**Q: How often should I run the autopilot?**
A: Once daily is recommended. Running more frequently may hit rate limits.

**Q: Can I monitor multiple repositories?**
A: Yes! Add them to `autopilot/config.yaml` under the repositories section.

**Q: What if I miss a day?**
A: Run with a date range to catch up: `--start-date YYYY-MM-DD --end-date YYYY-MM-DD`

**Q: Can I customize the summary format?**
A: Yes! Edit templates in `autopilot/templates/` directory.

**Q: Is there a web interface?**
A: Not in v0. Web dashboard is planned for v0.2 (see ROADMAP).

## 🔗 Related Documentation

- [README](README_AUTOPILOT.md) - Installation and features
- [SPEC](SPEC_v0.md) - Technical specification
- [ARCHITECTURE](ARCHITECTURE.md) - System design
- [ROADMAP](ROADMAP_AUTOPILOT.md) - Future plans

## 📞 Support

If you encounter issues:

1. Check this guide first
2. Review logs in `logs/autopilot.log`
3. Search [existing issues](../../issues)
4. Create a new issue with:
   - Error message
   - Log output
   - Configuration (sanitized)
   - Steps to reproduce

---

**Happy automating! 🤖**
