#!/usr/bin/env python3
"""
Test script for branch protection setup

This script tests the branch protection configuration without actually
applying it to a repository.
"""

import sys
import os

# Add .github/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".github", "scripts"))


def test_import():
    """Test that the module can be imported."""
    try:
        import setup_branch_protection

        print("✅ Module import successful")
        return True
    except ImportError as e:
        print(f"❌ Failed to import module: {e}")
        return False


def test_config_generation():
    """Test that the configuration can be generated."""
    try:
        import setup_branch_protection

        config = setup_branch_protection.get_branch_protection_config()

        print("✅ Configuration generation successful")
        print("\nConfiguration preview:")
        print(
            f"  • Require PR reviews: {config.get('require_pull_request_reviews', {}).get('required_approving_review_count')} approval(s)"
        )
        print(
            f"  • Dismiss stale reviews: {config.get('require_pull_request_reviews', {}).get('dismiss_stale_reviews')}"
        )
        print(
            f"  • Require status checks: {config.get('require_status_checks', {}).get('strict')}"
        )
        print(f"  • Allow force pushes: {config.get('allow_force_pushes')}")
        print(f"  • Allow deletions: {config.get('allow_deletions')}")

        # Validate required fields
        assert "require_pull_request_reviews" in config
        assert "require_status_checks" in config
        assert "enforce_admins" in config

        print("\n✅ Configuration validation successful")
        return True

    except Exception as e:
        print(f"❌ Configuration generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pygithub_available():
    """Test that PyGithub is available."""
    try:
        import github

        try:
            version = github.__version__
        except AttributeError:
            # PyGithub doesn't always expose __version__
            try:
                from importlib.metadata import version as get_version
            except ImportError:
                # Fallback for Python < 3.8
                try:
                    from importlib_metadata import version as get_version
                except ImportError:
                    get_version = None

            if get_version:
                try:
                    version = get_version("PyGithub")
                except Exception:
                    version = "unknown"
            else:
                version = "unknown"
        print(f"✅ PyGithub is available (version: {version})")
        return True
    except ImportError:
        print("⚠️  PyGithub is not installed. Install with: pip install PyGithub")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Branch Protection Setup - Test Suite")
    print("=" * 70)
    print()

    results = []

    # Run tests
    print("1. Testing module import...")
    results.append(test_import())
    print()

    print("2. Testing PyGithub availability...")
    results.append(test_pygithub_available())
    print()

    print("3. Testing configuration generation...")
    results.append(test_config_generation())
    print()

    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if all(results):
        print("\n✅ All tests passed! The branch protection script is ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
