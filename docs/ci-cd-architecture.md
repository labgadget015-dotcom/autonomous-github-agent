# CI/CD Architecture

## Overview

This document describes the CI/CD architecture for the Autonomous GitHub Agent project. The system is built on GitHub Actions and implements comprehensive quality gates, security scanning, and automated monitoring.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Developer Workflow                       │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Pull Request│  │ Push to Main │  │   Schedule   │             │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘             │
└─────────┼────────────────┼──────────────────┼────────────────────┘
          │                │                  │
          ▼                ▼                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflows                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Pre-commit CI Enforcement                                   │ │
│  │  ├─ Run pre-commit hooks                                     │ │
│  │  ├─ Auto-fix issues                                          │ │
│  │  └─ Comment on PR                                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Code Quality & Security Analysis (Parallel)                 │ │
│  │  ├─ Pylint (quality score + badge)                           │ │
│  │  ├─ Flake8 (style checking)                                  │ │
│  │  ├─ Bandit (security scan + badge)                           │ │
│  │  └─ Radon (complexity analysis)                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Test Coverage                                                │ │
│  │  ├─ pytest with pytest-xdist (parallel)                      │ │
│  │  ├─ Generate coverage reports                                │ │
│  │  ├─ Create coverage badge                                    │ │
│  │  └─ Comment coverage on PR                                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Complexity Monitoring                                        │ │
│  │  ├─ Radon cyclomatic complexity                              │ │
│  │  ├─ Maintainability index                                    │ │
│  │  ├─ Enhanced PR comments with suggestions                    │ │
│  │  └─ Create issue on critical violations                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Security Scanning                                            │ │
│  │  ├─ Bandit (code vulnerabilities)                            │ │
│  │  ├─ pip-audit (dependency vulnerabilities)                   │ │
│  │  ├─ Gitleaks (secret detection)                              │ │
│  │  ├─ Comment security issues on PR                            │ │
│  │  └─ Create issue on critical vulns                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Monitoring & Metrics Export                                  │ │
│  │  ├─ Fetch workflow metrics                                   │ │
│  │  ├─ Calculate success rates                                  │ │
│  │  ├─ Track durations                                          │ │
│  │  ├─ Monitor API rate limits                                  │ │
│  │  └─ Export Prometheus metrics                                │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
          │                │                  │
          ▼                ▼                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                         Artifacts & Reports                        │
│  ├─ Coverage reports (HTML, XML)                                  │
│  ├─ Quality analysis results (JSON)                               │
│  ├─ Security scan reports (SARIF, JSON)                           │
│  ├─ Complexity metrics (JSON)                                     │
│  ├─ Workflow metrics (JSON, Prometheus)                           │
│  └─ Badges (JSON for shields.io)                                  │
└────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Monitoring & Observability                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Prometheus  │  │   Grafana    │  │ GitHub Issues│             │
│  │   Metrics    │  │  Dashboards  │  │ (Auto-created)│            │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└────────────────────────────────────────────────────────────────────┘
```

## Workflow Components

### 1. Pre-commit CI Enforcement
**File:** `.github/workflows/pre-commit-ci.yml`

- **Triggers:** Pull requests, push to main/develop
- **Purpose:** Enforce code style and quality standards
- **Features:**
  - Runs pre-commit hooks on all files
  - Auto-fixes issues when possible
  - Comments on PR with results
  - Fails if non-fixable issues found

### 2. Code Quality & Security Analysis
**File:** `.github/workflows/code-quality.yml`

- **Triggers:** Pull requests, push to main, weekly schedule
- **Purpose:** Parallel static analysis for code quality and security
- **Matrix Jobs:**
  - **Pylint:** Code quality scoring (threshold: 8.0/10)
  - **Flake8:** PEP 8 style checking
  - **Bandit:** Security vulnerability detection
  - **Radon:** Code complexity analysis
- **Features:**
  - Parallel execution for speed
  - Badge generation (quality, security, coverage)
  - PR comments with results
  - Consolidated quality summary

### 3. Test Coverage
**File:** `.github/workflows/code-quality.yml` (test-coverage job)

- **Purpose:** Execute tests and measure coverage
- **Features:**
  - Parallel test execution with pytest-xdist
  - Coverage threshold enforcement (80%)
  - HTML and XML coverage reports
  - Coverage badge generation
  - PR comments with coverage percentage

### 4. Complexity Monitoring
**File:** `.github/workflows/complexity_monitor.yml`

- **Triggers:** Pull requests, push, weekly schedule, manual
- **Purpose:** Monitor and report code complexity
- **Features:**
  - Cyclomatic complexity analysis
  - Maintainability index calculation
  - Enhanced PR comments with:
    - Severity-based recommendations
    - Refactoring suggestions
    - Documentation links
  - Auto-create issues for critical violations

### 5. Security Scanning
**File:** `.github/workflows/security_scan.yml`

- **Triggers:** Pull requests, push, daily schedule, manual
- **Purpose:** Comprehensive security vulnerability detection
- **Jobs:**
  - **Bandit:** Python code security analysis
  - **pip-audit:** Dependency vulnerability checking
  - **Gitleaks:** Secret detection in commits
- **Features:**
  - SARIF report upload to GitHub Security
  - PR comments with security summary
  - Auto-create issues for critical vulnerabilities
  - Zero-tolerance for high-severity issues

### 6. Monitoring & Metrics Export
**File:** `.github/workflows/monitoring_export.yml`

- **Triggers:** Every 15 minutes, push to main, manual
- **Purpose:** Export workflow metrics for observability
- **Features:**
  - Fetch recent workflow run data
  - Calculate success rates and durations
  - Monitor GitHub API rate limits
  - Export Prometheus-compatible metrics
  - Generate timestamped historical data

## Quality Gates

### Mandatory Gates (Block Merge)
1. **Pre-commit:** All hooks must pass
2. **Pylint:** Score ≥ 8.0/10
3. **Test Coverage:** ≥ 80%
4. **Security:** Zero critical vulnerabilities
5. **Complexity:** No functions with complexity > 15

### Advisory Gates (Warning Only)
1. **Flake8:** Style violations
2. **Medium Security Issues:** ≤ 5 issues
3. **Code Complexity:** Functions with 10-15 complexity

## Caching Strategy

### Python Dependencies
- **Cache Key:** `${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}`
- **Restored:** On all workflow runs
- **Updated:** When requirements.txt changes

### Pre-commit Environments
- **Cache Key:** `pre-commit-${{ runner.os }}-${{ hashFiles('.pre-commit-config.yaml') }}`
- **Restored:** On pre-commit workflow runs

### Pylint Cache
- **Cache Key:** `${{ runner.os }}-pylint-${{ hashFiles('requirements.txt') }}`
- **Persistent:** Across workflow runs for faster analysis

## Artifact Retention

| Artifact Type | Retention Period | Purpose |
|--------------|------------------|---------|
| Coverage Reports | 30 days | Code coverage analysis |
| Quality Analysis | 30 days | Pylint, Flake8 results |
| Security Reports | 30 days | Bandit, pip-audit results |
| Complexity Metrics | 30 days | Radon analysis |
| Workflow Metrics | 90 days | Long-term trend analysis |
| Badges | Permanent (in repo) | README display |

## Badge System

Badges are automatically generated and updated in `.github/badges/`:

1. **Build Badge:** Workflow success/failure status
2. **Coverage Badge:** Test coverage percentage
3. **Quality Badge:** Pylint score out of 10
4. **Security Badge:** Security scan status

Badges are served via shields.io endpoint URLs pointing to the JSON files in the repository.

## Monitoring Setup

### Prometheus
- **Config:** `.github/config/prometheus.yml`
- **Scrape Interval:** 15 minutes
- **Metrics:**
  - `github_workflow_runs_total`
  - `github_workflow_success_rate`
  - `github_workflow_duration_seconds`
  - `github_api_rate_limit_usage`

### Grafana
- **Dashboard:** `.github/config/grafana-dashboard.json`
- **Panels:**
  - Workflow success rate
  - Duration trends
  - API rate limit usage
  - Code quality trends
  - Security vulnerability counts
  - Test coverage trends

## Performance Optimization

### Parallel Execution
- Static analysis tools run in parallel matrix jobs
- Tests run with pytest-xdist for parallel execution
- Independent jobs run concurrently

### Concurrency Control
- `cancel-in-progress: true` for outdated workflow runs
- Prevents redundant work on rapid commits

### Minimal Context
- Checkout with shallow clone for faster clones
- Targeted coverage analysis (only `.github/scripts/`)

## Security Considerations

1. **Secrets Management:**
   - All secrets stored in GitHub Secrets
   - Never exposed in logs or artifacts

2. **Token Permissions:**
   - Minimal required permissions per workflow
   - Read-only when write not needed

3. **SARIF Upload:**
   - Security results uploaded to GitHub Security tab
   - Integration with Dependabot alerts

4. **Secret Scanning:**
   - Gitleaks scans all commits
   - Blocks commits with detected secrets

## Troubleshooting

See [docs/troubleshooting.md](./troubleshooting.md) for common issues and solutions.

## Optimization Guide

See [docs/optimization-guide.md](./optimization-guide.md) for performance tuning recommendations.

## Related Documentation

- [Workflow README](./workflows/README.md)
- [contributing.md](../contributing.md)
- [README.md](../README.md)
