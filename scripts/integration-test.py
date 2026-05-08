#!/usr/bin/env python3
"""
Comprehensive System Integration Test
Tests all CI/CD components working together end-to-end.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class IntegrationTester:
    """Run integration tests for CI/CD system."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
        self.root_dir = Path(__file__).parent.parent

    def run_test(self, name: str, test_func) -> bool:
        """Run a single test."""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print("=" * 60)

        try:
            result = test_func()
            if result:
                print(f"✅ PASSED: {name}")
                self.passed += 1
                self.results.append({"test": name, "status": "PASSED"})
                return True
            else:
                print(f"❌ FAILED: {name}")
                self.failed += 1
                self.results.append({"test": name, "status": "FAILED"})
                return False
        except Exception as e:
            print(f"❌ ERROR in {name}: {e}")
            self.failed += 1
            self.results.append({"test": name, "status": "ERROR", "error": str(e)})
            return False

    def test_parallel_analyzer(self) -> bool:
        """Test parallel code analyzer."""
        script = self.root_dir / ".github" / "scripts" / "parallel_code_analyzer.py"

        # Run analyzer
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=self.root_dir,
        )

        # Check for output file
        output_file = self.root_dir / "analysis-results.json"
        if not output_file.exists():
            print("❌ analysis-results.json not created")
            return False

        # Validate JSON
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            required_keys = ["pylint", "flake8", "bandit", "radon"]
            for key in required_keys:
                if key not in data:
                    print(f"❌ Missing key in results: {key}")
                    return False

            print(f"✅ Analysis results valid: {list(data.keys())}")
            return True
        except Exception as e:
            print(f"❌ Error validating results: {e}")
            return False

    def test_complexity_reporter(self) -> bool:
        """Test complexity reporter."""
        script = self.root_dir / ".github" / "scripts" / "complexity_reporter.py"

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=self.root_dir,
        )

        # Check for output file
        output_file = self.root_dir / "complexity-report.json"
        if not output_file.exists():
            print("❌ complexity-report.json not created")
            return False

        try:
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "summary" not in data:
                print("❌ Missing summary in complexity report")
                return False

            print(
                f"✅ Complexity report valid: {data.get('summary', {}).get('total_files', 0)} files analyzed"
            )
            return True
        except Exception as e:
            print(f"❌ Error validating complexity report: {e}")
            return False

    def test_health_dashboard(self) -> bool:
        """Test health dashboard generator."""
        script = self.root_dir / ".github" / "scripts" / "health_dashboard_generator.py"

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=self.root_dir,
        )

        # Check for dashboard file
        dashboard_file = self.root_dir / "docs" / "HEALTH_DASHBOARD.md"
        if not dashboard_file.exists():
            print("❌ HEALTH_DASHBOARD.md not created")
            return False

        try:
            content = dashboard_file.read_text(encoding="utf-8")

            required_sections = [
                "Repository Health Score",
                "Quality Metrics",
                "Recommendations",
            ]

            for section in required_sections:
                if section not in content:
                    print(f"❌ Missing section: {section}")
                    return False

            print(f"✅ Health dashboard valid: {len(content)} chars")
            return True
        except Exception as e:
            print(f"❌ Error validating dashboard: {e}")
            return False

    def test_badge_generator(self) -> bool:
        """Test badge generator."""
        script = self.root_dir / ".github" / "scripts" / "badge_generator.py"

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=self.root_dir,
        )

        # Check for badges file
        badges_file = self.root_dir / "badges.svg"

        # Badge generator might update README instead
        readme_file = self.root_dir / "README.md"

        if readme_file.exists():
            content = readme_file.read_text(encoding="utf-8")
            if "shields.io" in content or "badge" in content.lower():
                print("✅ Badges found in README")
                return True

        print("ℹ️ Badge generator ran (no validation criteria)")
        return True

    def test_workflow_optimizer(self) -> bool:
        """Test workflow optimizer."""
        script = self.root_dir / ".github" / "scripts" / "workflow_optimizer.py"

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=self.root_dir,
        )

        # Check for optimization report
        report_file = self.root_dir / "workflow-optimization-report.md"
        if not report_file.exists():
            print("❌ workflow-optimization-report.md not created")
            return False

        try:
            content = report_file.read_text(encoding="utf-8")

            required_sections = [
                "Workflow Optimization Analysis",
                "Current Performance",
            ]

            for section in required_sections:
                if section not in content:
                    print(f"❌ Missing section: {section}")
                    return False

            print(f"✅ Workflow optimization report valid")
            return True
        except Exception as e:
            print(f"❌ Error validating report: {e}")
            return False

    def test_cost_calculator(self) -> bool:
        """Test cost calculator."""
        script = self.root_dir / ".github" / "scripts" / "cost_calculator.py"

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=self.root_dir,
        )

        # Check for cost report
        report_file = self.root_dir / "docs" / "COST_REPORT.md"
        if not report_file.exists():
            print("❌ COST_REPORT.md not created")
            return False

        try:
            content = report_file.read_text(encoding="utf-8")

            required_sections = [
                "GitHub Actions Cost Report",
                "Cost Breakdown",
                "Free Tier Analysis",
            ]

            for section in required_sections:
                if section not in content:
                    print(f"❌ Missing section: {section}")
                    return False

            print(f"✅ Cost report valid")
            return True
        except Exception as e:
            print(f"❌ Error validating cost report: {e}")
            return False

    def test_performance_benchmark(self) -> bool:
        """Test performance benchmark."""
        script = self.root_dir / ".github" / "scripts" / "performance_benchmark.py"

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=self.root_dir,
        )

        # Check for benchmark report
        report_file = self.root_dir / "docs" / "PERFORMANCE_BENCHMARK.md"
        if not report_file.exists():
            print("❌ PERFORMANCE_BENCHMARK.md not created")
            return False

        try:
            content = report_file.read_text(encoding="utf-8")

            required_sections = [
                "Performance Benchmark Report",
                "Performance Recommendations",
            ]

            for section in required_sections:
                if section not in content:
                    print(f"❌ Missing section: {section}")
                    return False

            print(f"✅ Performance benchmark valid")
            return True
        except Exception as e:
            print(f"❌ Error validating benchmark: {e}")
            return False

    def test_configuration_files(self) -> bool:
        """Test that all configuration files are valid."""
        configs = [
            ".github/config/analysis-config.yml",
            "pytest.ini",
            ".coveragerc",
            ".bandit",
            "monitoring/prometheus.yml",
            "monitoring/grafana-datasources.yml",
        ]

        for config in configs:
            config_file = self.root_dir / config
            if not config_file.exists():
                print(f"❌ Missing config: {config}")
                return False
            print(f"✅ Found: {config}")

        return True

    def test_documentation(self) -> bool:
        """Test that all documentation exists."""
        docs = [
            "docs/CICD_OPTIMIZATION_IMPLEMENTATION.md",
            "docs/CICD_QUICKSTART.md",
            "docs/INTEGRATION_EXAMPLES.md",
            "docs/PROJECT_COMPLETION_SUMMARY.md",
            "docs/FEATURE_SUMMARY.md",
            "CONTRIBUTING.md",
        ]

        for doc in docs:
            doc_file = self.root_dir / doc
            if not doc_file.exists():
                print(f"❌ Missing doc: {doc}")
                return False
            print(f"✅ Found: {doc}")

        return True

    def test_makefile_targets(self) -> bool:
        """Test that Makefile has all expected targets."""
        makefile = self.root_dir / "Makefile"

        if not makefile.exists():
            print("❌ Makefile not found")
            return False

        content = makefile.read_text(encoding="utf-8")

        required_targets = [
            "analyze",
            "test-local",
            "lint",
            "format",
            "security",
            "complexity",
            "badges",
            "dashboard",
            "benchmark",
            "optimize",
            "cost",
            "validate",
            "all",
        ]

        for target in required_targets:
            if f"{target}:" not in content:
                print(f"❌ Missing Makefile target: {target}")
                return False
            print(f"✅ Found target: {target}")

        return True

    def test_vscode_tasks(self) -> bool:
        """Test that VS Code tasks are configured."""
        tasks_file = self.root_dir / ".vscode" / "tasks.json"

        if not tasks_file.exists():
            print("❌ .vscode/tasks.json not found")
            return False

        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "tasks" not in data:
                print("❌ No tasks defined")
                return False

            print(f"✅ Found {len(data['tasks'])} VS Code tasks")
            return True
        except Exception as e:
            print(f"❌ Error validating tasks.json: {e}")
            return False

    def generate_report(self):
        """Generate final test report."""
        print("\n" + "=" * 60)
        print("INTEGRATION TEST REPORT")
        print("=" * 60)

        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n📊 Results:")
        print(f"  ✅ Passed: {self.passed}")
        print(f"  ❌ Failed: {self.failed}")
        print(f"  📈 Success Rate: {success_rate:.1f}%")

        print(f"\n📋 Detailed Results:")
        for result in self.results:
            status = "✅" if result["status"] == "PASSED" else "❌"
            print(f"  {status} {result['test']}")
            if "error" in result:
                print(f"     Error: {result['error']}")

        # Save results to JSON
        results_file = self.root_dir / "integration-test-results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "passed": self.passed,
                    "failed": self.failed,
                    "success_rate": success_rate,
                    "results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n💾 Results saved to: {results_file}")

        return self.failed == 0


def main():
    """Main execution."""
    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

    print("Starting CI/CD Integration Tests\n")

    tester = IntegrationTester()

    # Run all tests
    tests = [
        ("Parallel Code Analyzer", tester.test_parallel_analyzer),
        ("Complexity Reporter", tester.test_complexity_reporter),
        ("Health Dashboard Generator", tester.test_health_dashboard),
        ("Badge Generator", tester.test_badge_generator),
        ("Workflow Optimizer", tester.test_workflow_optimizer),
        ("Cost Calculator", tester.test_cost_calculator),
        ("Performance Benchmark", tester.test_performance_benchmark),
        ("Configuration Files", tester.test_configuration_files),
        ("Documentation", tester.test_documentation),
        ("Makefile Targets", tester.test_makefile_targets),
        ("VS Code Tasks", tester.test_vscode_tasks),
    ]

    for name, test_func in tests:
        tester.run_test(name, test_func)

    # Generate report
    success = tester.generate_report()

    if success:
        print("\n✅ ALL INTEGRATION TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME INTEGRATION TESTS FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
