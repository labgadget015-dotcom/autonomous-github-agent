#!/usr/bin/env python3
"""
Parallel Code Analysis Runner
Executes Pylint, Flake8, Bandit, and Radon concurrently for faster CI/CD
"""

import asyncio
import concurrent.futures
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml


class ParallelCodeAnalyzer:
    """Run multiple code analysis tools in parallel"""

    def __init__(self, config_path: str = ".github/config/analysis-config.yml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.results = {}

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        return self._default_config()

    def _default_config(self) -> dict:
        """Default configuration if no config file exists"""
        return {
            "thresholds": {"pylint": 8.0, "complexity": 10, "security": "medium"},
            "targets": [".github/scripts", "tests"],
            "exclude_patterns": ["__pycache__", "*.pyc", ".git"],
        }

    def run_pylint(self, target: str) -> tuple[int, str, str]:
        """Run Pylint analysis"""
        cmd = [
            "pylint",
            target,
            f"--fail-under={self.config['thresholds']['pylint']}",
            "--output-format=json",
            "--reports=y",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Pylint timeout after 5 minutes"
        except Exception as e:
            return 1, "", f"Pylint error: {str(e)}"

    def run_flake8(self, target: str) -> tuple[int, str, str]:
        """Run Flake8 analysis"""
        cmd = [
            "flake8",
            target,
            "--max-line-length=100",
            "--extend-ignore=E203,W503",
            "--format=json",
            "--count",
            "--statistics",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", f"Flake8 error: {str(e)}"

    def run_bandit(self, target: str) -> tuple[int, str, str]:
        """Run Bandit security analysis"""
        cmd = [
            "bandit",
            "-r",
            target,
            "-f",
            "json",
            "--severity-level",
            self.config["thresholds"]["security"],
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", f"Bandit error: {str(e)}"

    def run_radon_complexity(self, target: str) -> tuple[int, str, str]:
        """Run Radon complexity analysis"""
        cmd = [
            "radon",
            "cc",
            target,
            "-a",
            "-j",  # JSON output
            f"--min={chr(ord('A') + min(self.config['thresholds']['complexity'] // 2, 5))}",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", f"Radon error: {str(e)}"

    def run_radon_maintainability(self, target: str) -> tuple[int, str, str]:
        """Run Radon maintainability index"""
        cmd = ["radon", "mi", target, "-j"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", f"Radon MI error: {str(e)}"

    async def run_all_async(self) -> dict:
        """Run all analysis tools concurrently using asyncio"""
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            loop = asyncio.get_event_loop()

            # Create tasks for all analysis tools
            tasks = []
            for target in self.config["targets"]:
                tasks.extend(
                    [
                        loop.run_in_executor(executor, self.run_pylint, target),
                        loop.run_in_executor(executor, self.run_flake8, target),
                        loop.run_in_executor(executor, self.run_bandit, target),
                        loop.run_in_executor(
                            executor, self.run_radon_complexity, target
                        ),
                        loop.run_in_executor(
                            executor, self.run_radon_maintainability, target
                        ),
                    ]
                )

            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        elapsed = time.time() - start_time
        return self._process_results(results, elapsed)

    def _process_results(self, results: list, elapsed: float) -> dict:
        """Process and structure analysis results"""
        processed = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_seconds": round(elapsed, 2),
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "tools": {},
            "passed": True,
        }

        tool_names = ["pylint", "flake8", "bandit", "radon_cc", "radon_mi"] * len(
            self.config["targets"]
        )

        for i, (returncode, stdout, stderr) in enumerate(results):
            if isinstance(results[i], Exception):
                continue

            tool = tool_names[i]

            if tool not in processed["tools"]:
                processed["tools"][tool] = {
                    "status": "passed" if returncode == 0 else "failed",
                    "output": stdout,
                    "errors": stderr,
                }

            # Count issues
            if returncode != 0:
                processed["passed"] = False
                processed["summary"]["total_issues"] += 1

        return processed

    def generate_report(self, results: dict) -> str:
        """Generate markdown report"""
        report = f"""# Code Analysis Report

**Generated:** {results['timestamp']}
**Duration:** {results['elapsed_seconds']}s
**Status:** {'✅ PASSED' if results['passed'] else '❌ FAILED'}

## Summary
- Total Issues: {results['summary']['total_issues']}
- Critical: {results['summary']['critical']}
- High: {results['summary']['high']}
- Medium: {results['summary']['medium']}
- Low: {results['summary']['low']}

## Tool Results

"""
        for tool, data in results["tools"].items():
            status_emoji = "✅" if data["status"] == "passed" else "❌"
            report += f"### {status_emoji} {tool.upper()}\n"
            report += f"Status: {data['status']}\n\n"

            if data["errors"]:
                report += f"**Errors:**\n```\n{data['errors']}\n```\n\n"

        return report

    def save_results(self, results: dict, output_path: str = "analysis-results.json"):
        """Save results to JSON file"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_path}")


async def main():
    """Main entry point"""
    print("🚀 Starting parallel code analysis...")

    analyzer = ParallelCodeAnalyzer()
    results = await analyzer.run_all_async()

    # Generate and display report
    report = analyzer.generate_report(results)
    print(report)

    # Save results
    analyzer.save_results(results)

    # Exit with appropriate code
    sys.exit(0 if results["passed"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
