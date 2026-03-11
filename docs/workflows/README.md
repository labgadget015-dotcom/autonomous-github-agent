# GitHub Actions Workflows

This directory contains all GitHub Actions workflows for the Autonomous GitHub Agent project.

## Workflow Index

### 1. Pre-commit CI Enforcement
**File:** `pre-commit-ci.yml`

Enforces code quality standards using pre-commit hooks.

**Triggers:**
- Pull requests (opened, synchronized, ready_for_review)
- Push to main/develop

**What it does:**
- Runs all pre-commit hooks defined in `.pre-commit-config.yaml`
- Auto-fixes issues when possible
- Comments on PR with results
- Commits fixes back to the branch

**When to use manually:**
Never needed - runs automatically on all PRs

---

### 2. Code Quality & Security Analysis
**File:** `code-quality.yml`

Comprehensive parallel static analysis for code quality and security.

**Triggers:**
- Pull requests
- Push to main
- Weekly schedule (Mondays at 2 AM)

**Matrix Jobs:**
- **Pylint:** Python code quality (threshold: 8.0/10)
- **Flake8:** PEP 8 style compliance
- **Bandit:** Security vulnerability scanning
- **Radon:** Code complexity analysis

**Features:**
- Parallel execution for speed
- Generates badges for coverage, quality, security
- Comments on PRs with results
- Creates consolidated quality summary

**Manual Trigger:**
```bash
gh workflow run code-quality.yml
```

---

### 3. Complexity Monitoring
**File:** `complexity_monitor.yml`

Monitors and reports code complexity using Radon.

**Triggers:**
- Pull requests
- Push to main/develop
- Weekly schedule (Mondays at 3 AM)
- Manual dispatch

**Metrics Analyzed:**
- Cyclomatic complexity
- Maintainability index
- Raw metrics
- Halstead complexity

**PR Comments Include:**
- List of high-complexity functions
- Severity-based recommendations
- Refactoring suggestions
- Links to documentation

**Thresholds:**
- Warning: Complexity > 10
- Critical: Complexity > 15

**Manual Trigger:**
```bash
gh workflow run complexity_monitor.yml
```

---

### 4. Security Scanning
**File:** `security_scan.yml`

Multi-layered security vulnerability detection.

**Triggers:**
- Pull requests
- Push to main/develop
- Daily schedule (2 AM)
- Manual dispatch

**Security Tools:**
1. **Bandit:** Python code security issues
2. **pip-audit:** Dependency vulnerabilities
3. **Gitleaks:** Secret detection in commits

**Features:**
- SARIF upload to GitHub Security tab
- PR comments with security summary
- Auto-creates issues for critical vulnerabilities
- Zero-tolerance for high-severity issues (blocks merge)

**Manual Trigger:**
```bash
gh workflow run security_scan.yml
```

---

### 5. Monitoring & Metrics Export
**File:** `monitoring_export.yml`

Exports workflow metrics for observability and monitoring.

**Triggers:**
- Every 15 minutes (scheduled)
- Push to main
- Manual dispatch

**Exports:**
- Workflow run statistics
- Success/failure rates
- Duration metrics
- API rate limit usage
- Prometheus-compatible metrics

**Artifacts:**
- `latest.json` - Current metrics snapshot
- Timestamped historical metrics
- `prometheus.txt` - Prometheus format
- `rate_limit.json` - API usage

**Manual Trigger:**
```bash
gh workflow run monitoring_export.yml
```

---

### 6. AI Agent Workflow
**File:** `ai_agent_workflow.yml`

Main autonomous AI agent execution workflow.

**Triggers:**
- Workflow dispatch (manual)
- Issues (labeled, opened)

**Purpose:**
Runs the autonomous GitHub agent to process issues and create automated solutions.

---

### 7. Branch Protection
**File:** `branch_protection.yml`

Configures and enforces branch protection rules.

**Triggers:**
- Manual dispatch

**Purpose:**
Sets up branch protection rules for main and other important branches.

---

### 8. Release and Publish
**File:** `release-and-publish.yml`

Handles version releases and package publishing.

**Triggers:**
- Manual dispatch
- Tag creation

**Purpose:**
Automates the release process including changelog generation and package publishing.

---

## Workflow Dependencies

```
┌─────────────────────┐
│  Pull Request       │
└──────┬──────────────┘
       │
       ├─► pre-commit-ci.yml
       ├─► code-quality.yml
       │   ├─► static-analysis (matrix)
       │   │   ├─► pylint
       │   │   ├─► flake8
       │   │   ├─► bandit
       │   │   └─► radon
       │   ├─► test-coverage
       │   └─► quality-summary (needs: static-analysis, test-coverage)
       │
       ├─► complexity_monitor.yml
       │   ├─► radon-complexity-analysis
       │   └─► create-complexity-issue (needs: radon-complexity-analysis, if: failure)
       │
       └─► security_scan.yml
           ├─► bandit-scan
           ├─► dependency-scan
           ├─► secret-scan
           ├─► comment-security-issues (needs: all scans)
           └─► create-security-issue (needs: bandit-scan, if: failure)

┌─────────────────────┐
│  Schedule           │
└──────┬──────────────┘
       │
       ├─► code-quality.yml (weekly)
       ├─► complexity_monitor.yml (weekly)
       ├─► security_scan.yml (daily)
       └─► monitoring_export.yml (every 15 min)
```

## Environment Variables

Common environment variables across workflows:

```yaml
env:
  PYTHON_VERSION: '3.11'
  PYLINT_THRESHOLD: '8.0'
  COVERAGE_THRESHOLD: '80'
  COMPLEXITY_THRESHOLD: 'C'  # A-F scale
  MAX_CYCLOMATIC_COMPLEXITY: 10
  BANDIT_SEVERITY_THRESHOLD: 'MEDIUM'
  MAX_CRITICAL_VULNS: 0
  CACHE_VERSION: v2
```

## Permissions

Each workflow specifies minimal required permissions:

```yaml
permissions:
  contents: read          # Read repository contents
  security-events: write  # Upload security results
  issues: write          # Create/comment on issues
  pull-requests: write   # Comment on PRs
```

## Concurrency Control

All workflows use concurrency groups to prevent redundant runs:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This means:
- Only one instance per workflow per branch
- Newer runs cancel older ones
- Saves CI/CD minutes

## Artifact Management

### Artifact Types

| Artifact | Workflow | Retention | Size |
|----------|----------|-----------|------|
| `pylint-report` | code-quality.yml | 30 days | ~1 MB |
| `flake8-report` | code-quality.yml | 30 days | ~1 MB |
| `bandit-report` | code-quality.yml | 30 days | ~1 MB |
| `radon-report` | code-quality.yml | 30 days | ~1 MB |
| `coverage-reports` | code-quality.yml | 30 days | ~5 MB |
| `radon-complexity-reports` | complexity_monitor.yml | 30 days | ~1 MB |
| `bandit-security-reports` | security_scan.yml | 30 days | ~1 MB |
| `pip-audit-reports` | security_scan.yml | 30 days | ~1 MB |
| `gitleaks-report` | security_scan.yml | 30 days | ~1 MB |
| `workflow-metrics` | monitoring_export.yml | 90 days | ~100 KB |
| `pre-commit-results` | pre-commit-ci.yml | 7 days | ~1 KB |

### Downloading Artifacts

Via GitHub UI:
1. Go to Actions tab
2. Click on workflow run
3. Scroll to "Artifacts" section
4. Click to download

Via GitHub CLI:
```bash
# List artifacts for a run
gh run view <run-id> --log

# Download specific artifact
gh run download <run-id> -n artifact-name
```

## Workflow Badges

Add workflow status badges to README:

```markdown
[![Code Quality](https://github.com/labgadget015-dotcom/autonomous-github-agent/workflows/Code%20Quality%20%26%20Security%20Analysis/badge.svg)](https://github.com/labgadget015-dotcom/autonomous-github-agent/actions)
```

## Best Practices

### 1. Keep Workflows Fast
- Use caching for dependencies
- Run jobs in parallel when possible
- Use concurrency cancellation
- Minimize unnecessary steps

### 2. Fail Fast
- Set `fail-fast: false` in matrix for comprehensive results
- Use `continue-on-error: true` for non-blocking checks
- Set appropriate timeouts

### 3. Secure Secrets
- Never echo secrets in logs
- Use `secrets.GITHUB_TOKEN` when possible
- Minimize secret exposure

### 4. Optimize Checkout
- Use shallow clones when full history not needed
- Skip checkout for jobs that don't need code

### 5. Monitor Performance
- Review workflow metrics regularly
- Identify slow steps
- Optimize or parallelize bottlenecks

## Troubleshooting

### Workflow Not Triggering

**Check:**
1. Workflow file syntax (use yamllint)
2. Trigger conditions match your action
3. Branch protection rules
4. Workflow permissions

### Workflow Failing

**Common Issues:**
1. **Cache miss:** Clear caches and retry
2. **Rate limits:** Check API usage
3. **Dependency issues:** Update requirements.txt
4. **Permission errors:** Check workflow permissions

### Slow Workflows

**Solutions:**
1. Enable caching
2. Parallelize jobs
3. Use matrix for independent tasks
4. Reduce scope of operations

## Manual Workflow Dispatch

Trigger any workflow manually:

```bash
# Via GitHub CLI
gh workflow run <workflow-file.yml>

# With inputs
gh workflow run <workflow-file.yml> -f input_name=value

# List recent runs
gh run list --workflow=<workflow-file.yml>

# View specific run
gh run view <run-id>

# Watch a running workflow
gh run watch <run-id>
```

## Related Documentation

- [CI/CD Architecture](../ci-cd-architecture.md)
- [Troubleshooting Guide](../troubleshooting.md)
- [Optimization Guide](../optimization-guide.md)
- [Contributing Guide](../../CONTRIBUTING.md)
