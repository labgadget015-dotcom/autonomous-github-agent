# Branch Protection Setup Guide

This guide explains how to protect the main branch of your repository using the automated branch protection setup script.

## Overview

Branch protection rules help prevent accidental or unauthorized changes to important branches by:
- Requiring pull request reviews before merging
- Preventing direct pushes to protected branches
- Requiring status checks to pass
- Preventing force pushes and branch deletion
- Requiring conversation resolution before merging

## Quick Start

### Prerequisites

1. **GitHub Personal Access Token** with the following scopes:
   - `repo` (Full control of private repositories)
   - Admin access to the repository

2. **Python 3.9+** installed on your system

3. **PyGithub** library installed:
   ```bash
   pip install PyGithub
   ```

### Setup Instructions

#### Option 1: Run the Script Locally (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/labgadget015-dotcom/autonomous-github-agent.git
   cd autonomous-github-agent
   ```

2. **Set your GitHub token:**
   ```bash
   export GITHUB_TOKEN='your_github_personal_access_token'
   ```

3. **Run the branch protection script:**
   ```bash
   python .github/scripts/setup_branch_protection.py
   ```

4. **Follow the prompts:**
   - The script will show current protection status
   - Confirm to apply the protection rules
   - Review the success message

#### Option 2: Use GitHub Actions

1. **Go to Actions tab** in your GitHub repository

2. **Select "Branch Protection Setup" workflow**

3. **Click "Run workflow"**

4. **Configure options:**
   - Branch name (default: main)
   - Verify only mode (to check current settings)

**Note:** The default `GITHUB_TOKEN` in GitHub Actions may not have admin permissions. For full functionality, you may need to use a Personal Access Token stored as a secret.

## Protection Rules Applied

The script configures the following protection rules:

### Pull Request Requirements
- ✅ **Require pull request reviews before merging**
  - Minimum of 1 approving review required
  - Stale reviews are dismissed when new commits are pushed
  
### Status Checks
- ✅ **Require status checks to pass**
  - Branches must be up to date before merging
  - Can be configured to require specific CI checks

### Branch Restrictions
- ✅ **Prevent direct pushes** to the main branch
- ✅ **Prevent force pushes** (disabled)
- ✅ **Prevent branch deletion** (disabled)
- ✅ **Require conversation resolution** before merging

### Admin Enforcement
- ⚠️  **Admin enforcement disabled** by default
  - Allows administrators to bypass restrictions for emergency fixes
  - Can be enabled in the script configuration if needed

## Customization

To customize the protection rules, edit the `get_branch_protection_config()` function in `.github/scripts/setup_branch_protection.py`:

```python
def get_branch_protection_config() -> Dict[str, Any]:
    return {
        "require_pull_request_reviews": {
            "required_approving_review_count": 2,  # Change to 2 reviews
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,  # Enable CODEOWNERS
        },
        # ... other settings
    }
```

### Common Customizations

**Require more reviewers:**
```python
"required_approving_review_count": 2,  # Require 2 approvals
```

**Enable CODEOWNERS requirement:**
```python
"require_code_owner_reviews": True,
```

**Add required status checks:**
```python
"contexts": ["ci/test", "ci/lint", "ci/security"],
```

**Enforce rules for admins:**
```python
"enforce_admins": True,
```

**Require linear history (no merge commits):**
```python
"require_linear_history": True,
```

## Verification

After applying branch protection, verify the settings:

### Using the Script
```bash
python .github/scripts/setup_branch_protection.py
# Select 'no' when prompted to apply changes
# The script will show current protection status
```

### Using GitHub Web Interface
1. Go to repository Settings
2. Click on "Branches" in the left sidebar
3. Look for branch protection rules for `main`
4. Click "Edit" to view all configured rules

### Using GitHub CLI
```bash
gh api repos/{owner}/{repo}/branches/main/protection
```

## Troubleshooting

### Error: "Token doesn't have sufficient permissions"

**Solution:** Ensure your GitHub token has:
- `repo` scope (full repository access)
- Admin access to the repository

### Error: "Branch 'main' not found"

**Solution:** 
- Check if your default branch is named `main` or `master`
- Specify the correct branch name:
  ```bash
  # Edit the script or use environment variable
  export BRANCH_NAME='master'
  ```

### Error: "GITHUB_TOKEN environment variable is not set"

**Solution:**
```bash
export GITHUB_TOKEN='your_github_personal_access_token'
```

### Protection not working in GitHub Actions

**Solution:** The default `GITHUB_TOKEN` in Actions has limited permissions. Create a Personal Access Token with admin access and add it as a repository secret:
1. Go to Settings → Secrets and variables → Actions
2. Add new secret named `ADMIN_TOKEN`
3. Update workflow to use `${{ secrets.ADMIN_TOKEN }}`

## Security Best Practices

1. **Never commit tokens to the repository**
   - Always use environment variables
   - Add `.env` to `.gitignore`

2. **Use minimum required permissions**
   - Create tokens with only necessary scopes
   - Use different tokens for different purposes

3. **Rotate tokens regularly**
   - Change tokens every 90 days
   - Immediately rotate if compromised

4. **Monitor branch protection changes**
   - Review GitHub audit logs regularly
   - Set up notifications for protection rule changes

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

## Support

For issues or questions:
- Open an issue in the repository
- Check existing issues for solutions
- Review GitHub documentation for branch protection

---

**Last Updated:** January 2025
