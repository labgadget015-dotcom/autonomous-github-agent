#!/usr/bin/env python3
"""
Dependency Updater
Checks for outdated dependencies and optionally updates them.
"""

import json
import subprocess
import sys


class DependencyUpdater:
    """Check and update project dependencies."""

    def __init__(self, requirements_file: str = "requirements.txt"):
        self.requirements_file = requirements_file
        self.outdated = []

    def check_outdated(self) -> list[dict]:
        """Check for outdated packages."""
        try:
            print("🔍 Checking for outdated packages...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
            )

            self.outdated = json.loads(result.stdout)
            return self.outdated
        except subprocess.CalledProcessError as e:
            print(f"❌ Error checking outdated packages: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing pip output: {e}")
            return []

    def get_security_updates(self) -> list[dict]:
        """Check for security vulnerabilities using pip-audit."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "pip-audit"],
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [sys.executable, "-m", "pip_audit", "--format=json"],
                capture_output=True,
                text=True,
                check=False,  # Don't fail if vulnerabilities found
            )

            if result.stdout:
                return json.loads(result.stdout)
            return []
        except Exception as e:
            print(f"⚠️ Could not check security vulnerabilities: {e}")
            return []

    def categorize_updates(self) -> dict[str, list[dict]]:
        """Categorize updates by severity."""
        categories = {
            "major": [],
            "minor": [],
            "patch": [],
        }

        for package in self.outdated:
            current = package["version"]
            latest = package["latest_version"]

            current_parts = current.split(".")
            latest_parts = latest.split(".")

            if len(current_parts) >= 1 and len(latest_parts) >= 1:
                if current_parts[0] != latest_parts[0]:
                    categories["major"].append(package)
                elif (
                    len(current_parts) >= 2
                    and len(latest_parts) >= 2
                    and current_parts[1] != latest_parts[1]
                ):
                    categories["minor"].append(package)
                else:
                    categories["patch"].append(package)

        return categories

    def generate_report(self) -> str:
        """Generate dependency update report."""
        if not self.outdated:
            return "✅ All dependencies are up to date!"

        categories = self.categorize_updates()

        report = ["# Dependency Update Report\n"]
        report.append(
            f"**Generated**: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}\n"
        )
        report.append(f"**Total Outdated**: {len(self.outdated)}\n")

        # Summary
        report.append("\n## Summary\n")
        report.append(f"- 🔴 Major updates: {len(categories['major'])}")
        report.append(f"- 🟡 Minor updates: {len(categories['minor'])}")
        report.append(f"- 🟢 Patch updates: {len(categories['patch'])}\n")

        # Major updates
        if categories["major"]:
            report.append("\n## 🔴 Major Updates (Breaking Changes Possible)\n")
            report.append("| Package | Current | Latest | Type |")
            report.append("|---------|---------|--------|------|")
            for pkg in categories["major"]:
                report.append(
                    f"| {pkg['name']} | {pkg['version']} | {pkg['latest_version']} | {pkg.get('latest_filetype', 'wheel')} |"
                )

        # Minor updates
        if categories["minor"]:
            report.append("\n## 🟡 Minor Updates (New Features)\n")
            report.append("| Package | Current | Latest | Type |")
            report.append("|---------|---------|--------|------|")
            for pkg in categories["minor"]:
                report.append(
                    f"| {pkg['name']} | {pkg['version']} | {pkg['latest_version']} | {pkg.get('latest_filetype', 'wheel')} |"
                )

        # Patch updates
        if categories["patch"]:
            report.append("\n## 🟢 Patch Updates (Bug Fixes)\n")
            report.append("| Package | Current | Latest | Type |")
            report.append("|---------|---------|--------|------|")
            for pkg in categories["patch"]:
                report.append(
                    f"| {pkg['name']} | {pkg['version']} | {pkg['latest_version']} | {pkg.get('latest_filetype', 'wheel')} |"
                )

        report.append("\n## Recommendations\n")
        report.append("1. Review major updates carefully for breaking changes")
        report.append("2. Test minor and patch updates in development first")
        report.append("3. Update dependencies regularly to avoid large jumps")
        report.append("4. Check release notes for each package before updating\n")

        report.append("\n## Update Commands\n")
        report.append("```bash")
        report.append("# Update all to latest")
        report.append("pip install --upgrade -r requirements.txt\n")
        report.append("# Update specific package")
        report.append("pip install --upgrade <package-name>\n")
        report.append("# Generate new requirements.txt")
        report.append("pip freeze > requirements.txt")
        report.append("```\n")

        return "\n".join(report)

    def save_report(self, report: str, filename: str = "dependency-update-report.md"):
        """Save report to file."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"✅ Report saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")

    def update_package(self, package_name: str) -> bool:
        """Update a specific package."""
        try:
            print(f"📦 Updating {package_name}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
                check=True,
            )
            print(f"✅ {package_name} updated successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error updating {package_name}: {e}")
            return False

    def update_all_patch(self) -> int:
        """Update all patch-level updates (safest)."""
        categories = self.categorize_updates()
        updated = 0

        for package in categories["patch"]:
            if self.update_package(package["name"]):
                updated += 1

        return updated


def main():
    """Main execution."""
    updater = DependencyUpdater()

    print("🔍 Checking dependencies...\n")
    outdated = updater.check_outdated()

    if not outdated:
        print("✅ All dependencies are up to date!")
        return

    print(f"\n📊 Found {len(outdated)} outdated packages\n")

    # Generate report
    report = updater.generate_report()
    print(report)

    # Save report
    updater.save_report(report)

    # Ask if user wants to update patch versions
    if "--auto-patch" in sys.argv:
        print("\n🔧 Auto-updating patch versions...")
        updated = updater.update_all_patch()
        print(f"\n✅ Updated {updated} packages")

    print("\n✅ Dependency check complete!")


if __name__ == "__main__":
    main()
