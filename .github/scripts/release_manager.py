#!/usr/bin/env python3
"""
Release Automation Script
Automates version bumping, changelog generation, and release creation.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


class ReleaseManager:
    """Manage software releases."""

    VERSION_FILES = [
        "setup.py",
        "__init__.py",
        "version.py",
    ]

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.root = Path.cwd()

    def get_current_version(self) -> str | None:
        """Get current version from git tags."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                check=True,
            )
            version = result.stdout.strip()
            # Remove 'v' prefix if present
            return version.lstrip("v")
        except subprocess.CalledProcessError:
            # No tags yet
            return "0.0.0"

    def parse_version(self, version: str) -> tuple:
        """Parse semantic version."""
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")
        return (
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            match.group(4),
        )

    def bump_version(self, current: str, bump_type: str) -> str:
        """Bump version number."""
        major, minor, patch, pre = self.parse_version(current)

        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

    def update_version_files(self, old_version: str, new_version: str):
        """Update version in source files."""
        for filename in self.VERSION_FILES:
            file_path = self.root / filename
            if file_path.exists():
                self._update_file_version(file_path, old_version, new_version)

    def _update_file_version(self, file_path: Path, old_version: str, new_version: str):
        """Update version in a specific file."""
        try:
            content = file_path.read_text(encoding="utf-8")

            # Common version patterns
            patterns = [
                (
                    rf'version\s*=\s*["\']({re.escape(old_version)})["\']',
                    f'version = "{new_version}"',
                ),
                (
                    rf'__version__\s*=\s*["\']({re.escape(old_version)})["\']',
                    f'__version__ = "{new_version}"',
                ),
                (
                    rf'VERSION\s*=\s*["\']({re.escape(old_version)})["\']',
                    f'VERSION = "{new_version}"',
                ),
            ]

            updated = False
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    updated = True

            if updated:
                if not self.dry_run:
                    file_path.write_text(content, encoding="utf-8")
                print(f"✅ Updated version in {file_path}")
            else:
                print(f"⚠️ No version found in {file_path}")

        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")

    def generate_changelog(self):
        """Generate CHANGELOG.md."""
        try:
            from changelog_generator import ChangelogGenerator

            generator = ChangelogGenerator()
            generator.generate_changelog()
            print("✅ CHANGELOG.md generated")
        except Exception as e:
            print(f"⚠️ Could not generate changelog: {e}")

    def create_git_tag(self, version: str, message: str):
        """Create annotated git tag."""
        tag_name = f"v{version}"

        if self.dry_run:
            print(f"[DRY RUN] Would create tag: {tag_name}")
            return

        try:
            subprocess.run(["git", "tag", "-a", tag_name, "-m", message], check=True)
            print(f"✅ Created tag: {tag_name}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating tag: {e}")
            sys.exit(1)

    def commit_changes(self, version: str):
        """Commit version bump changes."""
        if self.dry_run:
            print(f"[DRY RUN] Would commit version bump to {version}")
            return

        try:
            # Add changed files
            subprocess.run(["git", "add", "-A"], check=True)

            # Commit
            subprocess.run(
                ["git", "commit", "-m", f"chore: bump version to {version}"], check=True
            )
            print("✅ Committed version bump")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error committing changes: {e}")
            sys.exit(1)

    def push_release(self):
        """Push commits and tags to remote."""
        if self.dry_run:
            print("[DRY RUN] Would push commits and tags")
            return

        try:
            # Push commits
            subprocess.run(["git", "push"], check=True)
            # Push tags
            subprocess.run(["git", "push", "--tags"], check=True)
            print("✅ Pushed release to remote")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error pushing: {e}")
            sys.exit(1)

    def create_github_release(self, version: str, changelog: str):
        """Create GitHub release."""
        if self.dry_run:
            print(f"[DRY RUN] Would create GitHub release for v{version}")
            return

        print("ℹ️ To create GitHub release, use GitHub CLI:")
        print(
            f"gh release create v{version} --title 'Release v{version}' --notes-file CHANGELOG.md"
        )

    def perform_release(self, bump_type: str):
        """Perform complete release process."""
        print(f"\n🚀 Starting {bump_type} release...\n")

        # Get current version
        current = self.get_current_version()
        print(f"📌 Current version: {current}")

        # Bump version
        new_version = self.bump_version(current, bump_type)
        print(f"📈 New version: {new_version}\n")

        # Update version files
        print("📝 Updating version files...")
        self.update_version_files(current, new_version)

        # Generate changelog
        print("\n📖 Generating changelog...")
        self.generate_changelog()

        # Commit changes
        print("\n💾 Committing changes...")
        self.commit_changes(new_version)

        # Create tag
        print(f"\n🏷️ Creating tag v{new_version}...")
        self.create_git_tag(new_version, f"Release version {new_version}")

        # Push
        print("\n📤 Pushing to remote...")
        self.push_release()

        # GitHub release
        print("\n🎉 Creating GitHub release...")
        self.create_github_release(new_version, "See CHANGELOG.md")

        print(f"\n✅ Release v{new_version} complete!")
        print("\nNext steps:")
        print("1. Verify the release on GitHub")
        print("2. Create release notes if needed")
        print("3. Announce the release")


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Automate software releases")
    parser.add_argument(
        "bump_type", choices=["major", "minor", "patch"], help="Type of version bump"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    manager = ReleaseManager(dry_run=args.dry_run)

    try:
        manager.perform_release(args.bump_type)
    except KeyboardInterrupt:
        print("\n\n❌ Release cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during release: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
