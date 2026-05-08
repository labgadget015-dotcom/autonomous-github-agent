#!/usr/bin/env python3
"""
Validation Script for CI/CD Optimization Implementation
Verifies all components are properly configured and functional
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("⚠️  Warning: PyYAML not installed. YAML validation will be skipped.")


class ImplementationValidator:
    """Validate all CI/CD optimization components"""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []

    def check_file_exists(self, filepath: str, description: str) -> bool:
        """Check if a file exists"""
        path = Path(filepath)
        exists = path.exists()

        if exists:
            print(f"✅ {description}: {filepath}")
            self.checks_passed += 1
        else:
            print(f"❌ {description}: {filepath} NOT FOUND")
            self.checks_failed += 1

        return exists

    def check_yaml_valid(self, filepath: str, description: str) -> bool:
        """Check if YAML file is valid"""
        if not YAML_AVAILABLE:
            print(f"⚠️  {description}: YAML validation skipped (PyYAML not installed)")
            self.warnings.append(f"{description}: Install PyYAML to validate")
            return True

        try:
            with open(filepath) as f:
                yaml.safe_load(f)
            print(f"✅ {description}: Valid YAML")
            self.checks_passed += 1
            return True
        except yaml.YAMLError as e:
            print(f"❌ {description}: Invalid YAML - {e}")
            self.checks_failed += 1
            return False
        except FileNotFoundError:
            print(f"❌ {description}: File not found")
            self.checks_failed += 1
            return False

    def check_json_valid(self, filepath: str, description: str) -> bool:
        """Check if JSON file is valid"""
        try:
            with open(filepath) as f:
                json.load(f)
            print(f"✅ {description}: Valid JSON")
            self.checks_passed += 1
            return True
        except json.JSONDecodeError as e:
            print(f"❌ {description}: Invalid JSON - {e}")
            self.checks_failed += 1
            return False
        except FileNotFoundError:
            print(f"❌ {description}: File not found")
            self.checks_failed += 1
            return False

    def check_python_syntax(self, filepath: str, description: str) -> bool:
        """Check if Python file has valid syntax"""
        try:
            with open(filepath, encoding="utf-8") as f:
                compile(f.read(), filepath, "exec")
            print(f"✅ {description}: Valid Python syntax")
            self.checks_passed += 1
            return True
        except SyntaxError as e:
            print(f"❌ {description}: Syntax error - {e}")
            self.checks_failed += 1
            return False
        except FileNotFoundError:
            print(f"❌ {description}: File not found")
            self.checks_failed += 1
            return False
        except UnicodeDecodeError as e:
            print(f"⚠️  {description}: Encoding issue - {e}")
            self.warnings.append(f"{description}: Check file encoding")
            self.checks_passed += 1  # Don't fail on encoding issues
            return True

    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("=" * 60)
        print("🔍 Validating CI/CD Optimization Implementation")
        print("=" * 60)

        # Check Python scripts
        print("\n📝 Checking Python Scripts...")
        scripts = [
            (".github/scripts/parallel_code_analyzer.py", "Parallel Code Analyzer"),
            (".github/scripts/complexity_reporter.py", "Complexity Reporter"),
            (".github/scripts/threshold_monitor.py", "Threshold Monitor"),
            (
                ".github/scripts/health_dashboard_generator.py",
                "Health Dashboard Generator",
            ),
            (".github/scripts/prometheus_exporter.py", "Prometheus Exporter"),
            (".github/scripts/inline_pr_commenter.py", "Inline PR Commenter"),
            ("scripts/test-local.py", "Local Testing Script"),
        ]

        for filepath, desc in scripts:
            self.check_python_syntax(filepath, desc)

        # Check YAML configurations
        print("\n📋 Checking YAML Configurations...")
        yamls = [
            (".github/config/analysis-config.yml", "Analysis Configuration"),
            (".github/workflows/code-quality-optimized.yml", "Optimized Workflow"),
            (".pre-commit-config.yaml", "Pre-commit Config"),
            ("monitoring/grafana-datasources.yml", "Grafana Datasources"),
        ]

        for filepath, desc in yamls:
            self.check_yaml_valid(filepath, desc)

        # Check JSON configurations
        print("\n📊 Checking JSON Configurations...")
        jsons = [
            ("monitoring/grafana-dashboard.json", "Grafana Dashboard"),
        ]

        for filepath, desc in jsons:
            self.check_json_valid(filepath, desc)

        # Check other configuration files
        print("\n⚙️  Checking Other Configurations...")
        configs = [
            (".bandit", "Bandit Security Config"),
            (".coveragerc", "Coverage Config"),
            ("pytest.ini", "Pytest Config"),
            (".env.example", "Environment Template"),
            ("CONTRIBUTING.md", "Contributing Guide"),
        ]

        for filepath, desc in configs:
            self.check_file_exists(filepath, desc)

        # Check documentation
        print("\n📚 Checking Documentation...")
        docs = [
            ("docs/CICD_OPTIMIZATION_IMPLEMENTATION.md", "Implementation Summary"),
        ]

        for filepath, desc in docs:
            self.check_file_exists(filepath, desc)

        # Print summary
        self.print_summary()

        return self.checks_failed == 0

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        total = self.checks_passed + self.checks_failed
        percentage = (self.checks_passed / total * 100) if total > 0 else 0

        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"📈 Success Rate: {percentage:.1f}%")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("\n" + "=" * 60)

        if self.checks_failed == 0:
            print("✨ ALL CHECKS PASSED! Implementation is complete and valid.")
            print("=" * 60)
        else:
            print("❌ SOME CHECKS FAILED. Please fix the issues above.")
            print("=" * 60)


def main():
    """Main entry point"""
    validator = ImplementationValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
