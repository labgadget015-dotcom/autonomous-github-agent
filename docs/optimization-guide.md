# CI/CD Optimization Guide

This guide provides strategies and best practices for optimizing GitHub Actions workflows to reduce execution time and resource usage.

## Table of Contents

- [Quick Wins](#quick-wins)
- [Caching Strategies](#caching-strategies)
- [Parallel Execution](#parallel-execution)
- [Workflow Optimization](#workflow-optimization)
- [Resource Management](#resource-management)
- [Advanced Techniques](#advanced-techniques)

---

## Quick Wins

### 1. Enable Concurrency Cancellation

Cancel outdated workflow runs when new commits are pushed:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

**Impact:** Saves 30-50% of CI/CD minutes

### 2. Use Shallow Clones

Don't fetch full git history when not needed:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 1  # Only fetch last commit
```

**Impact:** Reduces checkout time by 50-80%

### 3. Cache Dependencies

Cache Python packages, pre-commit hooks, etc.:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

**Impact:** Reduces dependency installation from 2-3 min to 10-20 sec

### 4. Parallel Test Execution

Use pytest-xdist for parallel testing:

```bash
pytest -n auto  # Uses all available CPU cores
```

**Impact:** Reduces test time by 60-80% (depends on test count)

### 5. Smart Workflow Triggers

Only run workflows when necessary:

```yaml
on:
  pull_request:
    paths:
      - '**.py'              # Only Python files
      - 'requirements.txt'    # Or dependencies
      - '.github/workflows/**'  # Or workflow changes
```

**Impact:** Reduces unnecessary workflow runs by 40-60%

---

## Caching Strategies

### Python Dependencies

**Best Practice:**
```yaml
- name: Cache Python dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      .venv
    key: ${{ runner.os }}-python-${{ hashFiles('requirements.txt', 'setup.py') }}
    restore-keys: |
      ${{ runner.os }}-python-
```

**Advanced:** Layer caching
```yaml
# Cache Python runtime separately
- name: Cache Python
  uses: actions/cache@v4
  with:
    path: /opt/hostedtoolcache/Python
    key: ${{ runner.os }}-python-${{ env.PYTHON_VERSION }}

# Cache packages
- name: Cache pip packages
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

### Pre-commit Hooks

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pre-commit
    key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}
    restore-keys: |
      pre-commit-
```

### Pylint Cache

```yaml
- uses: actions/cache@v4
  with:
    path: .pylint_cache
    key: pylint-${{ runner.os }}-${{ hashFiles('**/*.py') }}
```

### Test Cache

```yaml
- uses: actions/cache@v4
  with:
    path: .pytest_cache
    key: pytest-${{ runner.os }}-${{ hashFiles('tests/**/*.py') }}
```

### Cache Invalidation

Increment version when cache becomes stale:

```yaml
env:
  CACHE_VERSION: v2  # Increment to invalidate all caches

- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ env.CACHE_VERSION }}-${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

---

## Parallel Execution

### Matrix Strategy

Run multiple versions or configurations in parallel:

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
        os: [ubuntu-latest, macos-latest, windows-latest]
      fail-fast: false  # Don't cancel others on failure
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
```

**Impact:** 3x Python versions = 1/3 the time (if run sequentially)

### Independent Jobs

Run unrelated tasks in parallel:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [...]  # Runs immediately

  test:
    runs-on: ubuntu-latest
    steps: [...]  # Runs immediately (parallel with lint)

  security:
    runs-on: ubuntu-latest
    steps: [...]  # Runs immediately (parallel with lint and test)
```

### Matrix for Tools

Parallelize static analysis tools:

```yaml
jobs:
  analysis:
    strategy:
      matrix:
        tool: [pylint, flake8, bandit, radon]
    runs-on: ubuntu-latest
    steps:
      - name: Run ${{ matrix.tool }}
        run: make ${{ matrix.tool }}
```

**Impact:** 4 tools in parallel vs sequential = 4x faster

### Parallel Testing with pytest-xdist

```bash
# Use all CPU cores
pytest -n auto

# Specific number of workers
pytest -n 4

# Load balancing strategy
pytest -n auto --dist loadscope
```

**Configuration (pytest.ini):**
```ini
[pytest]
addopts = -n auto --dist loadscope
```

---

## Workflow Optimization

### Minimize Checkout

Skip checkout when not needed:

```yaml
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      # No checkout needed for simple API calls
      - name: Send notification
        run: curl -X POST ${{ secrets.WEBHOOK_URL }}
```

### Conditional Steps

Skip unnecessary steps:

```yaml
- name: Upload coverage (main only)
  if: github.ref == 'refs/heads/main'
  run: codecov upload

- name: Comment on PR (PRs only)
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  # ...
```

### Step Timeouts

Prevent hanging steps:

```yaml
- name: Long-running task
  timeout-minutes: 10
  run: ./long-task.sh
```

### Job Timeouts

Prevent hanging jobs:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps: [...]
```

### Workflow Timeouts

Set maximum workflow duration:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 60  # Entire workflow max
```

### Skip CI

Add `[skip ci]` to commit message when appropriate:

```bash
git commit -m "docs: update README [skip ci]"
```

---

## Resource Management

### Artifact Optimization

Only upload necessary files:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: coverage-html
    path: htmlcov/  # Specific directory, not entire workspace
    retention-days: 7  # Don't keep forever
```

### Log Optimization

Reduce log verbosity:

```bash
# Instead of verbose
pytest -vvv

# Use minimal output
pytest --tb=short --quiet
```

**Collapse log groups:**
```bash
echo "::group::Installing dependencies"
pip install -r requirements.txt
echo "::endgroup::"
```

### Dependency Installation

**Faster installation:**
```bash
# Use binary wheels
pip install --only-binary=:all: numpy scipy

# Skip unnecessary packages
pip install --no-deps specific-package

# Use pip-tools for faster resolution
pip-sync requirements.txt
```

**Minimal installation:**
```bash
# Production dependencies only
pip install -r requirements.txt --no-dev

# Specific extras only
pip install -e .[test]
```

---

## Advanced Techniques

### Reusable Workflows

Create reusable workflow templates:

```yaml
# .github/workflows/reusable-test.yml
name: Reusable Test Workflow
on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}
      - run: pytest
```

**Usage:**
```yaml
# .github/workflows/ci.yml
jobs:
  test-3-9:
    uses: ./.github/workflows/reusable-test.yml
    with:
      python-version: '3.9'

  test-3-11:
    uses: ./.github/workflows/reusable-test.yml
    with:
      python-version: '3.11'
```

### Composite Actions

Create reusable action steps:

```yaml
# .github/actions/setup-python/action.yml
name: Setup Python Environment
description: Setup Python with caching
inputs:
  python-version:
    required: true
runs:
  using: composite
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}
        cache: pip
    - run: pip install -r requirements.txt
      shell: bash
```

### Docker Layer Caching

For Docker-based workflows:

```yaml
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Conditional Jobs

Skip entire jobs based on conditions:

```yaml
jobs:
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps: [...]
```

### Path Filtering

Only run on relevant file changes:

```yaml
on:
  pull_request:
    paths:
      - 'src/**'
      - 'tests/**'
      - 'requirements.txt'
```

**With path ignore:**
```yaml
on:
  pull_request:
    paths-ignore:
      - 'docs/**'
      - '**.md'
      - '.github/**'
```

---

## Performance Benchmarks

### Before Optimization
```
┌─────────────────┬──────────┐
│ Workflow Step   │ Duration │
├─────────────────┼──────────┤
│ Checkout        │   45s    │
│ Setup Python    │   30s    │
│ Install deps    │  180s    │
│ Run tests       │  240s    │
│ Lint            │  120s    │
│ Security scan   │   90s    │
├─────────────────┼──────────┤
│ Total           │  705s    │
│                 │ (11.75m) │
└─────────────────┴──────────┘
```

### After Optimization
```
┌─────────────────┬──────────┬────────────────┐
│ Workflow Step   │ Duration │ Optimization   │
├─────────────────┼──────────┼────────────────┤
│ Checkout        │   10s    │ Shallow clone  │
│ Setup Python    │   15s    │ Caching        │
│ Install deps    │   20s    │ Caching        │
│ Run tests       │   60s    │ Parallel (-n)  │
│ Lint (parallel) │   40s    │ Matrix jobs    │
│ Security scan   │   45s    │ Parallel jobs  │
├─────────────────┼──────────┼────────────────┤
│ Total           │  190s    │ 73% faster     │
│                 │  (3.17m) │                │
└─────────────────┴──────────┴────────────────┘
```

## Best Practices Summary

1. **✅ DO:**
   - Use caching for dependencies and build artifacts
   - Run independent jobs in parallel
   - Use matrix strategy for multiple configurations
   - Set appropriate timeouts
   - Cancel in-progress runs on new commits
   - Use shallow clones when possible
   - Minimize artifact uploads

2. **❌ DON'T:**
   - Run all workflows on every commit
   - Install unnecessary dependencies
   - Upload large artifacts with long retention
   - Use verbose logging unnecessarily
   - Fetch full git history when not needed
   - Run sequential jobs that could be parallel

## Monitoring Performance

Track workflow performance over time:

```bash
# Using GitHub CLI
gh run list --workflow=ci.yml --limit 50 --json conclusion,durationMs

# Calculate average duration
gh run list --workflow=ci.yml --limit 50 --json durationMs \
  | jq '[.[].durationMs] | add / length / 1000'
```

Set up alerts for slow workflows:

```yaml
# In monitoring_export.yml
- name: Alert on slow workflows
  if: ${{ env.AVG_DURATION > 600 }}  # 10 minutes
  run: |
    echo "::warning::Average workflow duration is ${{ env.AVG_DURATION }}s"
```

## Related Documentation

- [CI/CD Architecture](./ci-cd-architecture.md)
- [Workflow README](./workflows/README.md)
- [Troubleshooting Guide](./troubleshooting.md)
