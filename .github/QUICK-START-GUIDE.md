# 🚀 CI/CD Quick Start Guide

## 5-Minute Setup

### Step 1: Clone & Install
```bash
git clone <repo-url>
cd <repo-directory>
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Install Pre-Commit Hooks
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Step 3: Set Environment (Optional)
```bash
cp .env.development.example .env.development
# Edit .env.development with your GitHub token
```

---

## 🔍 Run Analysis Locally

### All Tools
```bash
pre-commit run --all-files
```

### Individual Tools
```bash
# Code quality
pylint agents/
flake8 agents/
black --check agents/
isort --check agents/

# Security
bandit -r agents/

# Complexity
radon cc agents/ -s

# Tests
pytest --cov=agents agents/
```

---

## ✅ Before Committing

1. **Run Pre-Commit** (catches issues before push)
   ```bash
   pre-commit run --all-files
   ```

2. **Fix Any Issues**
   ```bash
   black agents/    # Auto-format
   isort agents/    # Fix imports
   # Manual fixes for other issues
   ```

3. **Commit**
   ```bash
   git add .
   git commit -m "Your message"
   ```

---

## 📊 What Runs on PR?

✅ Parallel analysis (Pylint, Flake8, Bandit) - **5 min**
✅ Multi-version testing (Python 3.10, 3.11, 3.12)
✅ Coverage reports with PR comments
✅ Complexity analysis with warnings
✅ Security scanning with blocking on critical issues

---

## 🆘 Common Issues

### Pre-Commit Fails
```bash
# Reinstall
pre-commit install
pre-commit run --all-files

# Skip (not recommended)
git commit --no-verify
```

### Coverage Below 80%
```bash
# Check what's not covered
pytest --cov=agents --cov-report=html agents/
open htmlcov/index.html
```

### Bandit Security Issues
```bash
# Review findings
bandit -r agents/ -v
```

---

## 📚 Documentation

- **Detailed Guide**: `CI-CD-OPTIMIZATION-GUIDE.md`
- **Implementation Summary**: `CI-CD-IMPLEMENTATION-SUMMARY.md`
- **Configuration**: `.env.development.example`

---

## 🎯 Key Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Coverage | 80% | PR blocked if below |
| Complexity | CC > 10 | PR warning |
| Security | Critical | PR blocked |
| Docs | 80% | Pre-commit fails |

---

## ⚡ Performance

- **Sequential analysis**: ~15 min
- **Parallel analysis** (optimized): ~5 min ✨
- **Pre-commit hooks**: ~30-60 sec

---

## 🔐 Security Checks

✅ Bandit: Code vulnerabilities
✅ Safety: Dependency CVEs
✅ mypy: Type checking
✅ Pre-commit: File security

---

## 🎓 Pro Tips

1. **Run pre-commit before pushing** - Saves time on PR reviews
2. **Check coverage early** - Fix gaps before merge
3. **Address complexity warnings** - Refactor high-CC functions
4. **Review security findings** - Don't ignore Bandit warnings
5. **Keep deps updated** - Run Safety checks regularly

---

## 📞 Need Help?

1. Check CI/CD logs in GitHub Actions
2. Review detailed documentation
3. Run tools locally to reproduce issues
4. Check `.env.development.example` for configuration

---

**Ready to code!** 🚀
