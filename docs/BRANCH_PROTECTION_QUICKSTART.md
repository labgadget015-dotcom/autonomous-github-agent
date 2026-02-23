# Quick Start: Protect Your Main Branch

This repository now includes an automated branch protection setup tool.

## 🚀 Quick Setup (2 minutes)

```bash
# 1. Set your GitHub token
export GITHUB_TOKEN='your_github_personal_access_token'

# 2. Run the setup script
python .github/scripts/setup_branch_protection.py
```

## ✅ What This Does

- ✅ Blocks direct pushes to main branch
- ✅ Requires 1 pull request approval before merging
- ✅ Dismisses stale reviews when new commits are pushed
- ✅ Requires all conversations to be resolved
- ✅ Prevents force pushes and branch deletion

## 📖 Full Documentation

See [docs/BRANCH_PROTECTION_GUIDE.md](docs/BRANCH_PROTECTION_GUIDE.md) for:
- Detailed setup instructions
- Customization options
- Troubleshooting guide
- Security best practices

## 🔧 Requirements

- GitHub Personal Access Token with `repo` scope
- Admin access to the repository
- Python 3.9+ with PyGithub installed

## 📝 Files Added

- `.github/scripts/setup_branch_protection.py` - Main setup script
- `.github/workflows/branch_protection.yml` - GitHub Actions workflow
- `docs/BRANCH_PROTECTION_GUIDE.md` - Complete documentation
- `tests/test_branch_protection.py` - Test suite

---

**Note:** The GitHub token must have admin permissions to set up branch protection rules.
