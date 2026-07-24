# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Autonomous GitHub Agent CI/CD system.

## Table of Contents

- [Workflow Issues](#workflow-issues)
- [Code Quality Issues](#code-quality-issues)
- [Security Scan Issues](#security-scan-issues)
- [Coverage Issues](#coverage-issues)
- [Pre-commit Issues](#pre-commit-issues)
- [Development Environment Issues](#development-environment-issues)
- [Performance Issues](#performance-issues)

---

## Workflow Issues

### Workflow Not Running

**Symptom:** Workflow doesn't trigger on PR or push

**Causes & Solutions:**

1. **Workflow syntax error**
   ```bash
   # Validate YAML syntax
   yamllint .github/workflows/your-workflow.yml

   # Or use online validator
   # https://www.yamllint.com/
   ```

2. **Branch doesn't match trigger**
   - Check `on.push.branches` in workflow file
   - Ensure your branch matches the pattern

3. **Workflow disabled**
   - Go to Actions tab → Workflows
   - Check if workflow is enabled

4. **Permissions issue**
   ```yaml
   # Add necessary permissions to workflow
   permissions:
     contents: read
     pull-requests: write
   ```

### Workflow Failing with "Unexpected Error"

**Solution:**
1. Check workflow run logs in Actions tab
2. Look for the specific error message
3. Common fixes:
   - Clear workflow caches
   - Update action versions
   - Check GitHub Actions status

### Workflow Stuck/Hanging

**Symptoms:** Workflow runs for hours without completing

**Solutions:**

1. **Add timeout**
   ```yaml
   jobs:
     my-job:
       runs-on: ubuntu-latest
       timeout-minutes: 30  # Add this
   ```

2. **Check for infinite loops**
   - Review custom scripts
   - Look for waiting processes

3. **Cancel and retry**
   ```bash
   gh run cancel <run-id>
   gh run rerun <run-id>
   ```

---

## Code Quality Issues

### Pylint Score Below Threshold

**Error:** `Pylint score 7.5 is below threshold 8.0`

**Solutions:**

1. **Run Pylint locally**
   ```bash
   pylint .github/scripts --fail-under=8.0
   ```

2. **Fix common issues**
   ```bash
   # Add docstrings
   # Fix naming conventions
   # Remove unused imports
   # Add type hints
   ```

3. **View detailed report**
   ```bash
   pylint .github/scripts --output-format=text > pylint-report.txt
   ```

4. **Disable specific warnings** (use sparingly)
   ```python
   # pylint: disable=line-too-long
   long_line_of_code = "..."
   ```

### Flake8 Errors

**Error:** `E501 line too long (120 > 79 characters)`

**Solutions:**

1. **Format with Black**
   ```bash
   black .github/scripts
   ```

2. **Configure line length**
   ```ini
   # In setup.cfg or .flake8
   [flake8]
   max-line-length = 120
   ```

3. **Fix common issues**
   ```bash
   # Unused imports
   isort .github/scripts --remove-unused

   # Trailing whitespace
   autopep8 --in-place --aggressive .github/scripts/*.py
   ```

### Radon Complexity Too High

**Error:** `Function 'process_data' has complexity 15 (threshold: 10)`

**Solutions:**

1. **Identify complex functions**
   ```bash
   radon cc .github/scripts -s -a
   ```

2. **Refactoring strategies:**

   **a) Extract Method**
   ```python
   # Before (complexity: 15)
   def process_data(data):
       if validate(data):
           if transform(data):
               if save(data):
                   return True
       return False

   # After (complexity: 4)
   def process_data(data):
       if not validate(data):
           return False
       if not transform(data):
           return False
       return save(data)
   ```

   **b) Use Guard Clauses**
   ```python
   # Before
   def func(x):
       if x > 0:
           if x < 100:
               return x * 2
       return None

   # After
   def func(x):
       if x <= 0 or x >= 100:
           return None
       return x * 2
   ```

   **c) Extract to Separate Functions**
   ```python
   # Before (complexity: 12)
   def big_function(data):
       # 50 lines of logic
       pass

   # After (complexity: 3 each)
   def big_function(data):
       validated = _validate(data)
       processed = _process(validated)
       return _save(processed)

   def _validate(data):
       # validation logic
       pass

   def _process(data):
       # processing logic
       pass

   def _save(data):
       # saving logic
       pass
   ```

---

## Security Scan Issues

### Bandit High Severity Issues

**Error:** `B608: Possible SQL injection`

**Solutions:**

1. **Use parameterized queries**
   ```python
   # Bad
   query = f"SELECT * FROM users WHERE id = {user_id}"

   # Good
   query = "SELECT * FROM users WHERE id = ?"
   cursor.execute(query, (user_id,))
   ```

2. **View detailed report**
   ```bash
   bandit -r .github/scripts -f screen
   ```

3. **False positives** (use carefully)
   ```python
   # nosec - Skip this check
   subprocess.call(cmd, shell=True)  # nosec
   ```

### pip-audit Vulnerabilities

**Error:** `Package 'requests' has known vulnerabilities`

**Solutions:**

1. **Update dependencies**
   ```bash
   pip install --upgrade requests
   pip freeze > requirements.txt
   ```

2. **Check specific package**
   ```bash
   pip-audit --desc requests
   ```

3. **View all vulnerabilities**
   ```bash
   pip-audit --format json > vulnerabilities.json
   ```

### Gitleaks Secret Detection

**Error:** `Potential secret found in commit`

**Solutions:**

1. **Remove secret from history**
   ```bash
   # For recent commits
   git reset --soft HEAD~1
   git commit -m "Remove secret"

   # For old commits, use git-filter-repo
   git filter-repo --path path/to/file --invert-paths
   ```

2. **Rotate compromised secrets**
   - Immediately invalidate leaked secret
   - Generate new secret
   - Update in GitHub Secrets

3. **Prevent future leaks**
   ```bash
   # Install gitleaks pre-commit hook
   pre-commit install
   ```

---

## Coverage Issues

### Coverage Below Threshold

**Error:** `Coverage 75% is below threshold 80%`

**Solutions:**

1. **Identify uncovered code**
   ```bash
   pytest --cov=.github/scripts --cov-report=html
   # Open htmlcov/index.html in browser
   ```

2. **Write missing tests**
   ```python
   # Test edge cases
   def test_edge_case():
       result = my_function(edge_case_input)
       assert result == expected_output

   # Test error handling
   def test_error_handling():
       with pytest.raises(ValueError):
           my_function(invalid_input)
   ```

3. **Exclude non-testable code**
   ```ini
   # In .coveragerc
   [run]
   omit =
       */tests/*
       */venv/*
       */__init__.py
   ```

### Tests Failing

**Error:** `FAILED tests/test_module.py::test_function`

**Solutions:**

1. **Run tests locally**
   ```bash
   pytest tests/test_module.py::test_function -v
   ```

2. **Check test fixtures**
   ```python
   @pytest.fixture
   def sample_data():
       return {"key": "value"}
   ```

3. **Update test expectations**
   - Code may have changed behavior
   - Update test assertions accordingly

4. **Check test dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov pytest-xdist
   ```

---

## Pre-commit Issues

### Pre-commit Hooks Failing

**Error:** `[FAILED] black`

**Solutions:**

1. **Run pre-commit manually**
   ```bash
   pre-commit run --all-files
   ```

2. **Auto-fix issues**
   ```bash
   black .
   isort .
   pre-commit run --all-files
   ```

3. **Update hooks**
   ```bash
   pre-commit autoupdate
   pre-commit run --all-files
   ```

4. **Skip specific hook** (last resort)
   ```bash
   SKIP=black git commit -m "message"
   ```

### Pre-commit Not Running

**Solution:**

1. **Install hooks**
   ```bash
   pre-commit install
   ```

2. **Verify installation**
   ```bash
   ls -la .git/hooks/pre-commit
   ```

3. **Test hooks**
   ```bash
   pre-commit run --all-files
   ```

---

## Development Environment Issues

### Virtual Environment Issues

**Error:** `ModuleNotFoundError: No module named 'pytest'`

**Solutions:**

1. **Activate virtual environment**
   ```bash
   # Linux/Mac
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

2. **Reinstall dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Recreate venv**
   ```bash
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### VS Code Not Using Correct Python

**Solution:**

1. **Select interpreter**
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Choose `./venv/bin/python`

2. **Verify in terminal**
   ```bash
   which python
   # Should show: /path/to/project/venv/bin/python
   ```

3. **Check settings.json**
   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python"
   }
   ```

### Dev Container Issues

**Error:** `Container failed to start`

**Solutions:**

1. **Rebuild container**
   - `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

2. **Check Docker**
   ```bash
   docker ps
   docker logs <container-id>
   ```

3. **Clear Docker cache**
   ```bash
   docker system prune -a
   ```

---

## Performance Issues

### Workflow Taking Too Long

**Symptom:** Workflow runs for > 10 minutes

**Solutions:**

1. **Enable caching**
   ```yaml
   - uses: actions/cache@v4
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
   ```

2. **Parallelize jobs**
   ```yaml
   jobs:
     test:
       strategy:
         matrix:
           python-version: [3.9, 3.10, 3.11]
   ```

3. **Reduce scope**
   ```bash
   # Only run tests on changed files
   pytest $(git diff --name-only origin/main... | grep test_)
   ```

4. **Profile tests**
   ```bash
   pytest --durations=10
   ```

### Cache Not Working

**Symptom:** Dependencies reinstalled every run

**Solutions:**

1. **Verify cache key**
   ```yaml
   key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
   # Ensure requirements.txt exists and is committed
   ```

2. **Check cache hit**
   - Look for "Cache restored successfully" in logs

3. **Clear and rebuild cache**
   - Increment `CACHE_VERSION` in workflow

### API Rate Limit Exceeded

**Error:** `API rate limit exceeded`

**Solutions:**

1. **Check current usage**
   ```bash
   gh api rate_limit
   ```

2. **Reduce API calls**
   - Use caching
   - Batch requests
   - Increase intervals

3. **Use authenticated requests**
   ```yaml
   env:
     GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
   ```

---

## Getting Help

If none of these solutions work:

1. **Check workflow logs**
   - Actions tab → Select run → View logs

2. **Search existing issues**
   - GitHub Issues for this project

3. **Create a new issue**
   - Include workflow logs
   - Describe what you've tried
   - Environment details

4. **Community resources**
   - GitHub Community Forums
   - Stack Overflow (tag: github-actions)

## Related Documentation

- [CI/CD Architecture](./ci-cd-architecture.md)
- [Workflow README](./workflows/README.md)
- [Optimization Guide](./optimization-guide.md)
- [Contributing Guide](../contributing.md)
