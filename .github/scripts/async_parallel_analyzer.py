#!/usr/bin/env python3
"""
Async Parallel Code Analyzer
Runs multiple code analysis tools in parallel using asyncio and concurrent.futures
for maximum CI/CD efficiency.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AnalysisResult:
    """Result from a single analysis tool."""

    tool: str
    success: bool
    duration: float
    output: str
    error: str = ""
    issues_count: int = 0


class AsyncParallelAnalyzer:
    """Orchestrates parallel execution of code analysis tools."""

    def __init__(self, target_path: str = ".github/scripts"):
        self.target_path = target_path
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.max_workers = min(8, (os.cpu_count() or 4))

    async def run_tool(self, tool_name: str, command: list[str]) -> AnalysisResult:
        """Run a single analysis tool asynchronously."""
        start_time = time.time()

        try:
            print(f"🔍 Starting {tool_name}...")

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout per tool
                ),
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # Count issues in output
            issues = self._count_issues(tool_name, result.stdout)

            print(
                f"{'✅' if success else '⚠️ '} {tool_name} completed in {duration:.2f}s ({issues} issues)"
            )

            return AnalysisResult(
                tool=tool_name,
                success=success,
                duration=duration,
                output=result.stdout,
                error=result.stderr,
                issues_count=issues,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"⏱️  {tool_name} timeout after {duration:.2f}s")
            return AnalysisResult(
                tool=tool_name,
                success=False,
                duration=duration,
                output="",
                error="Timeout exceeded",
            )
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {tool_name} failed: {e}")
            return AnalysisResult(
                tool=tool_name,
                success=False,
                duration=duration,
                output="",
                error=str(e),
            )

    def _count_issues(self, tool: str, output: str) -> int:
        """Estimate issue count from tool output."""
        if not output:
            return 0

        if tool == "pylint":
            # Count lines that look like issues
            return sum(
                1
                for line in output.split("\\n")
                if line.strip() and not line.startswith("*")
            )
        elif tool == "flake8":
            return len([line for line in output.split("\\n") if ":" in line])
        elif tool == "bandit":
            return output.count(">> Issue:")
        elif tool == "mypy":
            return output.count("error:")
        else:
            return 0

    async def run_all_parallel(self) -> list[AnalysisResult]:
        """Run all analysis tools in parallel."""

        tools = {
            "pylint": [
                "pylint",
                self.target_path,
                "--output-format=json",
                f"--output={self.reports_dir}/pylint-report.json",
                "--exit-zero",
            ],
            "flake8": [
                "flake8",
                self.target_path,
                "--format=json",
                f"--output-file={self.reports_dir}/flake8-report.json",
                "--exit-zero",
            ],
            "mypy": [
                "mypy",
                self.target_path,
                "--json-report",
                str(self.reports_dir / "mypy"),
                "--ignore-missing-imports",
                "--no-error-summary",
            ],
            "bandit": [
                "bandit",
                "-r",
                self.target_path,
                "-f",
                "json",
                "-o",
                str(self.reports_dir / "bandit-report.json"),
                "--exit-zero",
            ],
            "radon_cc": [
                "radon",
                "cc",
                self.target_path,
                "-a",
                "-j",
                "-O",
                str(self.reports_dir / "radon-cc.json"),
            ],
            "radon_mi": [
                "radon",
                "mi",
                self.target_path,
                "-j",
                "-O",
                str(self.reports_dir / "radon-mi.json"),
            ],
        }

        print(f"\\n🚀 Running {len(tools)} analysis tools in parallel...")
        print(f"   Workers: {self.max_workers}")
        print(f"   Target: {self.target_path}\\n")

        # Run all tools in parallel
        tasks = [self.run_tool(name, cmd) for name, cmd in tools.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and convert to results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tool_name = list(tools.keys())[i]
                print(f"❌ {tool_name} raised exception: {result}")
                valid_results.append(
                    AnalysisResult(
                        tool=tool_name,
                        success=False,
                        duration=0.0,
                        output="",
                        error=str(result),
                    )
                )
            else:
                valid_results.append(result)

        return valid_results

    def generate_summary(self, results: list[AnalysisResult]) -> dict[str, Any]:
        """Generate comprehensive summary of all analysis results."""

        total_duration = sum(r.duration for r in results)
        total_issues = sum(r.issues_count for r in results)
        successful = sum(1 for r in results if r.success)

        summary = {
            "total_tools": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "total_duration": round(total_duration, 2),
            "total_issues": total_issues,
            "results": [],
        }

        for result in results:
            summary["results"].append(
                {
                    "tool": result.tool,
                    "success": result.success,
                    "duration": round(result.duration, 2),
                    "issues": result.issues_count,
                    "error": result.error if not result.success else None,
                }
            )

        return summary

    def save_summary(self, summary: dict[str, Any]) -> None:
        """Save summary to JSON file."""
        summary_path = self.reports_dir / "analysis-summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\\n💾 Summary saved to {summary_path}")

    def print_summary(self, summary: dict[str, Any]) -> None:
        """Print formatted summary to console."""
        print("\\n" + "=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Tools Ran: {summary['total_tools']}")
        print(f"Successful: {summary['successful']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Total Duration: {summary['total_duration']}s")
        print(f"Total Issues: {summary['total_issues']}")
        print("\\nIndividual Results:")
        print("-" * 60)

        for result in summary["results"]:
            status = "✅" if result["success"] else "❌"
            print(
                f"{status} {result['tool']:15} {result['duration']:6.2f}s  {result['issues']:4d} issues"
            )
            if result["error"]:
                print(f"   Error: {result['error']}")

        print("=" * 60 + "\\n")


async def main():
    """Main entry point."""
    target = os.getenv("ANALYSIS_TARGET", ".github/scripts")

    analyzer = AsyncParallelAnalyzer(target)

    # Run all tools in parallel
    results = await analyzer.run_all_parallel()

    # Generate and save summary
    summary = analyzer.generate_summary(results)
    analyzer.save_summary(summary)
    analyzer.print_summary(summary)

    # Exit with error if any critical issues found
    if summary["total_issues"] > 50:
        print(f"⚠️  WARNING: {summary['total_issues']} issues found (threshold: 50)")
        sys.exit(1)

    if summary["failed"] > 0:
        print(f"⚠️  WARNING: {summary['failed']} tools failed")
        sys.exit(1)

    print("✅ Analysis completed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
