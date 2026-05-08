# 🎯 CI/CD Optimization - Integration Examples

## Quick Integration Guide

### 1. Slack Notifications

**Setup:**
```bash
# Add to .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Usage in Workflow:**
```yaml
- name: Notify Slack
  if: always()
  run: |
    python .github/scripts/notification_manager.py
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

**Manual Notification:**
```python
from notification_manager import NotificationManager

manager = NotificationManager()
manager.notify_workflow_status('CI/CD', 'success', 180)
```

---

### 2. Discord Integration

**Setup:**
```bash
# Add to .env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK
```

**Auto-notify on Security Issues:**
```yaml
- name: Check Security
  run: python .github/scripts/threshold_monitor.py

- name: Notify Discord
  if: failure()
  run: |
    python -c "
    from notification_manager import NotificationManager
    manager = NotificationManager()
    manager.send_discord_notification('Security issues detected!', 'error')
    "
```

---

### 3. Grafana Dashboard

**Access:**
```bash
# Start monitoring
docker-compose up -d

# Access Grafana
open http://localhost:3000

# Default credentials
Username: admin
Password: admin
```

**Import Dashboard:**
1. Login to Grafana
2. Click "+" → "Import"
3. Upload `monitoring/grafana-dashboard.json`
4. Select Prometheus datasource
5. Click "Import"

**Custom Panels:**
```json
{
  "title": "Custom Metric",
  "targets": [{
    "expr": "your_custom_metric",
    "legendFormat": "{{label}}"
  }]
}
```

---

### 4. README Badges

**Auto-update Badges:**
```yaml
- name: Update Badges
  run: python .github/scripts/badge_generator.py

- name: Commit Badges
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add README.md badges.svg
    git commit -m "Update badges [skip ci]" || exit 0
    git push
```

**Manual Badge Update:**
```bash
python .github/scripts/badge_generator.py
```

---

### 5. Local Development Workflow

**Daily Development:**
```bash
# Morning: Pull latest
git pull origin main

# Before committing: Test locally
python scripts/test-local.py --fast

# Auto-fix formatting
python scripts/test-local.py --fix

# Commit (pre-commit hooks run automatically)
git commit -m "Your message"

# Push (CI/CD runs automatically)
git push
```

**Full Validation:**
```bash
# Run everything
make all

# Or manually
python scripts/test-local.py
python scripts/validate-implementation.py
```

---

### 6. PR Review Integration

**Automatic:**
- Workflow runs on PR open/sync
- Inline comments added automatically
- Status checks required before merge

**Manual Review Request:**
```bash
# Trigger workflow manually
gh workflow run code-quality-optimized.yml
```

---

### 7. Prometheus Metrics

**Export Metrics:**
```bash
# Manual export
python .github/scripts/prometheus_exporter.py

# View metrics
curl http://localhost:9090/api/v1/query?query=repo_health_score
```

**Custom Metrics:**
```python
from prometheus_client import Gauge, push_to_gateway

custom_metric = Gauge('custom_metric', 'Description')
custom_metric.set(42)

push_to_gateway('localhost:9091', job='my_job', registry=registry)
```

---

### 8. Health Dashboard

**Auto-generate:**
```yaml
- name: Generate Dashboard
  run: python .github/scripts/health_dashboard_generator.py

- name: Commit Dashboard
  run: |
    git add docs/HEALTH_DASHBOARD.md
    git commit -m "Update health dashboard [skip ci]"
    git push
```

**View Dashboard:**
```bash
# Generated at every workflow run
cat docs/HEALTH_DASHBOARD.md
```

---

### 9. Threshold Monitoring

**Configure Thresholds:**
```yaml
# .github/config/analysis-config.yml
thresholds:
  pylint: 8.5  # Increase minimum score
  coverage: 85  # Increase coverage requirement
  complexity: 8  # Lower complexity threshold
```

**Manual Check:**
```bash
python .github/scripts/threshold_monitor.py
```

---

### 10. Workflow Optimization

**Analyze Performance:**
```bash
python .github/scripts/workflow_optimizer.py
```

**View Recommendations:**
```bash
cat workflow-optimization-report.md
```

---

## Integration Checklist

- [ ] Add webhook URLs to `.env`
- [ ] Configure Grafana dashboard
- [ ] Set up pre-commit hooks
- [ ] Add badges to README
- [ ] Configure Slack/Discord notifications
- [ ] Test local workflow
- [ ] Review threshold configuration
- [ ] Monitor first workflow run
- [ ] Check Prometheus metrics
- [ ] Review health dashboard

---

## Common Patterns

### Pattern 1: Quality Gate
```yaml
- name: Run Analysis
  run: python .github/scripts/parallel_code_analyzer.py

- name: Check Thresholds
  run: python .github/scripts/threshold_monitor.py

- name: Block if Failed
  if: failure()
  run: exit 1
```

### Pattern 2: Progressive Feedback
```yaml
- name: Fast Checks
  run: flake8 . --select=E9,F63,F7,F82

- name: Full Analysis
  run: python .github/scripts/parallel_code_analyzer.py

- name: Deep Analysis
  run: python scripts/test-local.py
```

### Pattern 3: Auto-remediation
```yaml
- name: Check Formatting
  run: black --check .

- name: Auto-fix
  if: failure()
  run: |
    black .
    git commit -am "Auto-format code [skip ci]"
    git push
```

---

## Troubleshooting

**Issue: Pre-commit hooks failing**
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Update hooks
pre-commit autoupdate
```

**Issue: Grafana not accessible**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs grafana

# Restart
docker-compose restart grafana
```

**Issue: Metrics not appearing**
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Re-export metrics
python .github/scripts/prometheus_exporter.py
```

---

## Advanced Usage

### Custom Analysis Rules
```python
# Add to parallel_code_analyzer.py
def run_custom_analysis(target: str):
    # Your custom analysis logic
    pass
```

### Custom Notifications
```python
from notification_manager import NotificationManager

manager = NotificationManager()
manager.send_all_channels("Custom message", "warning")
```

### Custom Metrics
```python
from prometheus_client import Counter

deployments = Counter('deployments_total', 'Total deployments')
deployments.inc()
```

---

**For more examples, see:**
- `docs/CICD_OPTIMIZATION_IMPLEMENTATION.md`
- `docs/CICD_QUICKSTART.md`
- `.github/workflows/code-quality-optimized.yml`
