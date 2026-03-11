#!/usr/bin/env python3
"""
Branch Protection Setup Script

This script configures comprehensive branch protection rules for the main branch
to prevent direct pushes, require PR reviews, and enforce status checks.

Usage:
    python setup_branch_protection.py
    python setup_branch_protection.py --verify-only

Environment Variables:
    GITHUB_TOKEN: GitHub Personal Access Token with repo admin access
    GITHUB_REPOSITORY: Repository in format "owner/repo" (optional, defaults to current repo)
"""

import os
import sys
import argparse
import traceback
from typing import Dict, Any

try:
    from github import Github, GithubException
except ImportError:
    print("Error: PyGithub is not installed. Install it with: pip install PyGithub")
    sys.exit(1)


def get_branch_protection_config() -> Dict[str, Any]:
    """
    Define comprehensive branch protection rules for the main branch.
    
    Returns:
        Dictionary containing branch protection configuration
    """
    return {
        # Require pull request reviews before merging
        "require_pull_request_reviews": {
            "dismiss_stale_reviews": True,  # Dismiss approvals when new commits are pushed
            "require_code_owner_reviews": False,  # Require review from code owners
            "required_approving_review_count": 1,  # Number of approvals required
            "require_last_push_approval": False,  # Require approval of most recent push
        },
        
        # Require status checks to pass before merging
        "require_status_checks": {
            "strict": True,  # Require branches to be up to date before merging
            "contexts": [],  # List of status checks that must pass (can be populated later)
        },
        
        # Enforce restrictions for who can push to the branch
        "enforce_admins": False,  # Don't enforce restrictions for admins (allows emergency fixes)
        
        # Require linear history (no merge commits)
        "require_linear_history": False,  # Allow merge commits for flexibility
        
        # Allow force pushes (disabled for safety)
        "allow_force_pushes": False,
        
        # Allow deletions (disabled for safety)
        "allow_deletions": False,
        
        # Require conversation resolution before merging
        "required_conversation_resolution": True,  # All PR comments must be resolved
        
        # Lock branch (read-only)
        "lock_branch": False,  # Keep branch active
        
        # Allow fork syncing
        "allow_fork_syncing": True,
    }


def setup_branch_protection(token: str, repository_name: str, branch_name: str = "main") -> bool:
    """
    Configure branch protection rules for the specified branch.
    
    Args:
        token: GitHub Personal Access Token
        repository_name: Repository in format "owner/repo"
        branch_name: Branch to protect (default: "main")
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize GitHub client
        g = Github(token)
        
        # Get repository
        print(f"Accessing repository: {repository_name}")
        repo = g.get_repo(repository_name)
        
        # Get branch
        print(f"Getting branch: {branch_name}")
        try:
            branch = repo.get_branch(branch_name)
        except GithubException as e:
            if e.status == 404:
                print(f"Error: Branch '{branch_name}' not found in repository")
                return False
            raise
        
        # Get protection configuration
        config = get_branch_protection_config()
        
        # Apply branch protection
        print(f"\nApplying branch protection rules to '{branch_name}' branch...")
        print("Configuration:")
        print(f"  ✓ Require pull request reviews: {config['require_pull_request_reviews']['required_approving_review_count']} approval(s)")
        print(f"  ✓ Dismiss stale reviews: {config['require_pull_request_reviews']['dismiss_stale_reviews']}")
        print(f"  ✓ Require status checks: {config['require_status_checks']['strict']}")
        print(f"  ✓ Enforce for admins: {config['enforce_admins']}")
        print(f"  ✓ Allow force pushes: {config['allow_force_pushes']}")
        print(f"  ✓ Allow deletions: {config['allow_deletions']}")
        print(f"  ✓ Require conversation resolution: {config['required_conversation_resolution']}")
        
        # Edit branch protection using PyGithub
        branch.edit_protection(
            # Require pull request reviews
            required_approving_review_count=config['require_pull_request_reviews']['required_approving_review_count'],
            dismiss_stale_reviews=config['require_pull_request_reviews']['dismiss_stale_reviews'],
            require_code_owner_reviews=config['require_pull_request_reviews']['require_code_owner_reviews'],
            
            # Require status checks
            strict=config['require_status_checks']['strict'],
            contexts=config['require_status_checks']['contexts'],
            
            # Enforcement and restrictions
            enforce_admins=config['enforce_admins'],
            require_linear_history=config['require_linear_history'],
            allow_force_pushes=config['allow_force_pushes'],
            allow_deletions=config['allow_deletions'],
            required_conversation_resolution=config['required_conversation_resolution'],
            lock_branch=config['lock_branch'],
            allow_fork_syncing=config['allow_fork_syncing'],
        )
        
        print(f"\n✅ Branch protection successfully configured for '{branch_name}' branch!")
        print(f"\nProtection Summary:")
        print(f"  • Direct pushes to {branch_name} are now blocked")
        print(f"  • Pull requests require at least {config['require_pull_request_reviews']['required_approving_review_count']} approval(s)")
        print(f"  • All conversations must be resolved before merging")
        print(f"  • Force pushes and deletions are disabled")
        
        return True
        
    except GithubException as e:
        print(f"\n❌ GitHub API Error: {e.status} - {e.data.get('message', 'Unknown error')}")
        if e.status == 401:
            print("Error: Invalid or missing GitHub token")
        elif e.status == 403:
            print("Error: Token doesn't have sufficient permissions. Ensure the token has 'repo' scope and admin access.")
        elif e.status == 404:
            print(f"Error: Repository '{repository_name}' not found or token doesn't have access")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        traceback.print_exc()
        return False


def verify_branch_protection(token: str, repository_name: str, branch_name: str = "main") -> bool:
    """
    Verify that branch protection is properly configured.
    
    Args:
        token: GitHub Personal Access Token
        repository_name: Repository in format "owner/repo"
        branch_name: Branch to verify (default: "main")
        
    Returns:
        True if protection is configured, False otherwise
    """
    try:
        g = Github(token)
        repo = g.get_repo(repository_name)
        branch = repo.get_branch(branch_name)
        
        # Try to get protection settings
        protection = branch.get_protection()
        
        print(f"\n✅ Branch protection is active on '{branch_name}' branch")
        print("\nCurrent protection settings:")
        
        # Display protection details
        if protection.required_pull_request_reviews:
            print(f"  • Required approving reviews: {protection.required_pull_request_reviews.required_approving_review_count}")
            print(f"  • Dismiss stale reviews: {protection.required_pull_request_reviews.dismiss_stale_reviews}")
        
        if protection.required_status_checks:
            print(f"  • Strict status checks: {protection.required_status_checks.strict}")
            contexts = protection.required_status_checks.contexts
            if contexts:
                print(f"  • Required status checks: {', '.join(contexts)}")
        
        print(f"  • Enforce for admins: {protection.enforce_admins.enabled if protection.enforce_admins else False}")
        print(f"  • Allow force pushes: {protection.allow_force_pushes.enabled if protection.allow_force_pushes else False}")
        print(f"  • Allow deletions: {protection.allow_deletions.enabled if protection.allow_deletions else False}")
        
        return True
        
    except GithubException as e:
        if e.status == 404:
            print(f"\n⚠️  No branch protection configured on '{branch_name}' branch")
            return False
        raise


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Configure branch protection for GitHub repositories'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing protection settings without applying changes'
    )
    parser.add_argument(
        '--branch',
        default='main',
        help='Branch name to protect (default: main)'
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("GitHub Branch Protection Setup")
    print("=" * 70)
    
    # Get GitHub token from environment
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("\n❌ Error: GITHUB_TOKEN environment variable is not set")
        print("\nTo fix this:")
        print("  1. Create a GitHub Personal Access Token with 'repo' scope")
        print("  2. Export it: export GITHUB_TOKEN='your_token_here'")
        print("  3. Run this script again")
        sys.exit(1)
    
    # Get repository name from environment or use default
    repository_name = os.environ.get("GITHUB_REPOSITORY")
    if not repository_name:
        # Try to detect from git remote
        try:
            import subprocess
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=True,
                shell=False  # Explicitly disable shell for security
            )
            git_url = result.stdout.strip()
            
            # Parse repository from git URL
            # Handle both HTTPS and SSH URLs
            # HTTPS: https://github.com/owner/repo.git
            # SSH: git@github.com:owner/repo.git
            # Note: We validate the URL starts with expected GitHub URL patterns
            # to prevent URL substring attacks
            if "github.com" in git_url:
                # Extract the owner/repo part more safely
                if git_url.startswith("https://github.com/"):
                    # HTTPS URL
                    repository_name = git_url.replace("https://github.com/", "")
                    repository_name = repository_name.replace(".git", "")
                elif git_url.startswith("git@github.com:"):
                    # SSH URL
                    repository_name = git_url.replace("git@github.com:", "")
                    repository_name = repository_name.replace(".git", "")
                else:
                    raise ValueError("Unrecognized GitHub URL format")
            else:
                raise ValueError("Could not parse repository name from git URL")
                
        except Exception:
            print("\n❌ Error: GITHUB_REPOSITORY environment variable is not set and could not detect from git")
            print("\nTo fix this:")
            print("  export GITHUB_REPOSITORY='owner/repo'")
            sys.exit(1)
    
    print(f"\nRepository: {repository_name}")
    print(f"Branch: {args.branch}")
    print()
    
    # Check current protection status
    print("Checking current branch protection status...")
    is_protected = verify_branch_protection(token, repository_name, args.branch)
    
    # If verify-only mode, exit after verification
    if args.verify_only:
        print("\n" + "=" * 70)
        if is_protected:
            print("Verification complete: Branch protection is configured")
        else:
            print("Verification complete: Branch protection is NOT configured")
        print("=" * 70)
        sys.exit(0 if is_protected else 1)
    
    # Ask for confirmation
    print("\n" + "-" * 70)
    valid_responses = {"yes", "y", "no", "n"}
    while True:
        response = input("\nDo you want to apply/update branch protection rules? (yes/no): ").strip().lower()
        if response in valid_responses:
            break
        print(f"Invalid response '{response}'. Please enter 'yes' or 'no'.")

    if response not in {"yes", "y"}:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    
    # Apply branch protection
    success = setup_branch_protection(token, repository_name, args.branch)
    
    if success:
        print("\n" + "=" * 70)
        print("Branch protection setup completed successfully!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("Branch protection setup failed!")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
