#!/usr/bin/env python3
"""
Local Testing Script
Run all code quality checks locally before pushing to GitHub
"""

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class LocalTester:
    """Run local tests and quality checks"""
    
    def __init__(self, verbose: bool = False, fast: bool = False):
        self.verbose = verbose
        self.fast = fast
        self.failures = []
        
    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """Run a command and return success status"""
        print(f"\n{'='*60}")
        print(f"🔍 {description}")
        print(f"{'='*60}")
        
        if self.verbose:
            print(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=not self.verbose,
                text=True,
                timeout=300
            )
            
            success = result.returncode == 0
            output = result.stdout if not self.verbose else ""
            
            if success:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                if not self.verbose and result.stdout:
                    print(result.stdout[:500])
            
            return success, output
            
        except subprocess.TimeoutExpired:
            print("❌ TIMEOUT")
            return False, ""
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False, str(e)
    
    def check_black(self) -> bool:
        """Check code formatting with Black"""
        success, _ = self.run_command(
            ['black', '--check', '.'],
            "Checking code formatting (Black)"
        )
        
        if not success:
            print("💡 Run 'black .' to auto-format")
            self.failures.append("Black formatting")
        
        return success
    
    def check_isort(self) -> bool:
        """Check import sorting"""
        success, _ = self.run_command(
            ['isort', '--check-only', '.'],
            "Checking import sorting (isort)"
        )
        
        if not success:
            print("💡 Run 'isort .' to auto-sort imports")
            self.failures.append("Import sorting")
        
        return success
    
    def check_flake8(self) -> bool:
        """Run Flake8 linting"""
        success, _ = self.run_command(
            ['flake8', '.', '--max-line-length=100', '--extend-ignore=E203,W503'],
            "Running Flake8 linter"
        )
        
        if not success:
            self.failures.append("Flake8 linting")
        
        return success
    
    def check_pylint(self) -> bool:
        """Run Pylint analysis"""
        if self.fast:
            print("\n⚡ Skipping Pylint (fast mode)")
            return True
        
        success, _ = self.run_command(
            ['pylint', '.github/scripts', '--fail-under=8.0'],
            "Running Pylint analysis"
        )
        
        if not success:
            self.failures.append("Pylint analysis")
        
        return success
    
    def check_mypy(self) -> bool:
        """Run mypy type checking"""
        if self.fast:
            print("\n⚡ Skipping mypy (fast mode)")
            return True
        
        success, _ = self.run_command(
            ['mypy', '.github/scripts', '--ignore-missing-imports'],
            "Running mypy type checker"
        )
        
        if not success:
            self.failures.append("Type checking")
        
        return success
    
    def check_bandit(self) -> bool:
        """Run Bandit security scan"""
        success, _ = self.run_command(
            ['bandit', '-r', '.github/scripts', '-c', '.bandit'],
            "Running Bandit security scan"
        )
        
        if not success:
            self.failures.append("Security scan")
        
        return success
    
    def check_tests(self) -> bool:
        """Run pytest"""
        cmd = ['pytest', '-v']
        
        if self.fast:
            cmd.extend(['-x', '--tb=short'])  # Stop on first failure
        else:
            cmd.extend(['--cov=.github/scripts', '--cov-fail-under=80'])
        
        success, _ = self.run_command(cmd, "Running tests")
        
        if not success:
            self.failures.append("Tests")
        
        return success
    
    def check_yaml(self) -> bool:
        """Validate YAML files"""
        yaml_files = list(Path('.').rglob('*.yml')) + list(Path('.').rglob('*.yaml'))
        
        print(f"\n{'='*60}")
        print(f"🔍 Validating YAML files ({len(yaml_files)} files)")
        print(f"{'='*60}")
        
        import yaml
        
        all_valid = True
        for yaml_file in yaml_files:
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"❌ {yaml_file}: {e}")
                all_valid = False
        
        if all_valid:
            print("✅ All YAML files valid")
        else:
            self.failures.append("YAML validation")
        
        return all_valid
    
    def check_json(self) -> bool:
        """Validate JSON files"""
        json_files = list(Path('.').rglob('*.json'))
        
        print(f"\n{'='*60}")
        print(f"🔍 Validating JSON files ({len(json_files)} files)")
        print(f"{'='*60}")
        
        import json
        
        all_valid = True
        for json_file in json_files:
            # Skip node_modules and other build directories
            if 'node_modules' in str(json_file) or '.venv' in str(json_file):
                continue
            
            try:
                with open(json_file) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ {json_file}: {e}")
                all_valid = False
        
        if all_valid:
            print("✅ All JSON files valid")
        else:
            self.failures.append("JSON validation")
        
        return all_valid
    
    def run_all_checks(self) -> bool:
        """Run all checks"""
        print("\n" + "="*60)
        print("🚀 Running Local Code Quality Checks")
        print("="*60)
        
        checks = [
            ("Code Formatting", self.check_black),
            ("Import Sorting", self.check_isort),
            ("Flake8 Linting", self.check_flake8),
            ("Pylint Analysis", self.check_pylint),
            ("Type Checking", self.check_mypy),
            ("Security Scan", self.check_bandit),
            ("Tests", self.check_tests),
            ("YAML Validation", self.check_yaml),
            ("JSON Validation", self.check_json),
        ]
        
        results = []
        for name, check_func in checks:
            try:
                success = check_func()
                results.append((name, success))
            except Exception as e:
                print(f"\n❌ {name} failed with exception: {e}")
                results.append((name, False))
                self.failures.append(name)
        
        # Print summary
        self.print_summary(results)
        
        return all(success for _, success in results)
    
    def print_summary(self, results: List[Tuple[str, bool]]):
        """Print final summary"""
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for name, success in results:
            emoji = "✅" if success else "❌"
            print(f"{emoji} {name}")
        
        print("\n" + "="*60)
        print(f"Result: {passed}/{total} checks passed")
        print("="*60)
        
        if self.failures:
            print("\n⚠️  Failed checks:")
            for failure in self.failures:
                print(f"  - {failure}")
            print("\n💡 Fix these issues before committing")
            return False
        else:
            print("\n✨ All checks passed! Ready to commit.")
            return True
    
    def auto_fix(self):
        """Auto-fix formatting issues"""
        print("\n🔧 Auto-fixing formatting issues...")
        
        # Format with Black
        subprocess.run(['black', '.'], check=False)
        print("✅ Black formatting applied")
        
        # Sort imports
        subprocess.run(['isort', '.'], check=False)
        print("✅ Import sorting applied")
        
        print("\n✨ Auto-fix complete. Re-run tests to verify.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run local code quality checks before pushing"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output'
    )
    parser.add_argument(
        '-f', '--fast',
        action='store_true',
        help='Run fast checks only (skip slow ones)'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Auto-fix formatting issues'
    )
    
    args = parser.parse_args()
    
    tester = LocalTester(verbose=args.verbose, fast=args.fast)
    
    if args.fix:
        tester.auto_fix()
        sys.exit(0)
    
    success = tester.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
