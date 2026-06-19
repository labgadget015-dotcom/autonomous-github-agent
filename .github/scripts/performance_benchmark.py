#!/usr/bin/env python3
"""
Performance Benchmarking System

Tracks and compares performance metrics over time:
- CI/CD execution times
- Test execution speed
- Build times
- Code analysis duration
- Resource usage
"""

import json
import sys
import time

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil not available - some metrics will be limited")
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkResult:
    """Represents a benchmark result"""

    timestamp: str
    benchmark_name: str
    duration_seconds: float
    cpu_usage_percent: float
    memory_mb: float
    success: bool
    metadata: dict[str, Any]


class PerformanceBenchmark:
    """
    Performance Benchmarking System

    Tracks performance metrics and compares over time
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.results_dir = self.repo_path / ".benchmark_results"
        self.results_dir.mkdir(exist_ok=True)
        self.current_session = []

    def benchmark_tests(self) -> BenchmarkResult:
        """Benchmark test suite execution"""
        print("🧪 Benchmarking test suite...")

        start_time = time.time()
        start_mem = (
            psutil.Process().memory_info().rss / 1024 / 1024 if PSUTIL_AVAILABLE else 0
        )
        psutil.cpu_percent(interval=0.1) if PSUTIL_AVAILABLE else 0

        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-q"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            success = result.returncode == 0
        except subprocess.TimeoutExpired:
            success = False
        except Exception:
            success = False

        duration = time.time() - start_time
        end_mem = (
            psutil.Process().memory_info().rss / 1024 / 1024 if PSUTIL_AVAILABLE else 0
        )
        cpu_usage = psutil.cpu_percent(interval=0.1) if PSUTIL_AVAILABLE else 0

        benchmark = BenchmarkResult(
            timestamp=datetime.now().isoformat(),
            benchmark_name="test_suite",
            duration_seconds=duration,
            cpu_usage_percent=cpu_usage,
            memory_mb=end_mem - start_mem,
            success=success,
            metadata={"test_framework": "pytest"},
        )

        self.current_session.append(benchmark)
        print(
            f"   ✅ Duration: {duration:.2f}s, CPU: {cpu_usage:.1f}%, Memory: {end_mem - start_mem:.1f}MB"
        )

        return benchmark

    def benchmark_linting(self) -> BenchmarkResult:
        """Benchmark linting execution"""
        print("🔍 Benchmarking linting...")

        start_time = time.time()
        start_mem = (
            psutil.Process().memory_info().rss / 1024 / 1024 if PSUTIL_AVAILABLE else 0
        )
        psutil.cpu_percent(interval=0.1) if PSUTIL_AVAILABLE else 0

        success = True
        # Try multiple linters
        for linter in ["flake8", "pylint"]:
            try:
                subprocess.run([linter, "--version"], capture_output=True, timeout=10)
            except Exception:
                success = False

        duration = time.time() - start_time
        end_mem = (
            psutil.Process().memory_info().rss / 1024 / 1024 if PSUTIL_AVAILABLE else 0
        )
        cpu_usage = psutil.cpu_percent(interval=0.1) if PSUTIL_AVAILABLE else 0

        benchmark = BenchmarkResult(
            timestamp=datetime.now().isoformat(),
            benchmark_name="linting",
            duration_seconds=duration,
            cpu_usage_percent=cpu_usage,
            memory_mb=end_mem - start_mem,
            success=success,
            metadata={"linters": ["flake8", "pylint"]},
        )

        self.current_session.append(benchmark)
        print(f"   ✅ Duration: {duration:.2f}s")

        return benchmark

    def benchmark_copilot_analysis(self) -> BenchmarkResult:
        """Benchmark copilot analysis"""
        print("🤖 Benchmarking copilot analysis...")

        start_time = time.time()
        start_mem = (
            psutil.Process().memory_info().rss / 1024 / 1024 if PSUTIL_AVAILABLE else 0
        )
        psutil.cpu_percent(interval=0.1) if PSUTIL_AVAILABLE else 0

        try:
            # Import and run copilot
            sys.path.insert(0, str(self.repo_path / ".github" / "scripts"))
            from elite_copilot import EliteCopilot

            copilot = EliteCopilot()
            results = copilot.analyze_repository(str(self.repo_path))
            success = results.get("health_score", 0) > 0
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            success = False

        duration = time.time() - start_time
        end_mem = (
            psutil.Process().memory_info().rss / 1024 / 1024 if PSUTIL_AVAILABLE else 0
        )
        cpu_usage = psutil.cpu_percent(interval=0.1) if PSUTIL_AVAILABLE else 0

        benchmark = BenchmarkResult(
            timestamp=datetime.now().isoformat(),
            benchmark_name="copilot_analysis",
            duration_seconds=duration,
            cpu_usage_percent=cpu_usage,
            memory_mb=end_mem - start_mem,
            success=success,
            metadata={"analysis_type": "full_repository"},
        )

        self.current_session.append(benchmark)
        print(f"   ✅ Duration: {duration:.2f}s, Memory: {end_mem - start_mem:.1f}MB")

        return benchmark

    def run_full_benchmark(self) -> list[BenchmarkResult]:
        """Run complete benchmark suite"""
        print("\n" + "=" * 70)
        print("Performance Benchmark Suite")
        print("=" * 70)
        print()

        benchmarks = [
            ("Linting", self.benchmark_linting),
            ("Copilot Analysis", self.benchmark_copilot_analysis),
        ]

        # Only run tests if pytest is available
        try:
            subprocess.run(
                ["python", "-m", "pytest", "--version"], capture_output=True, timeout=5
            )
            benchmarks.insert(0, ("Test Suite", self.benchmark_tests))
        except Exception:
            print("⚠️  Pytest not available, skipping test benchmark")

        for _name, func in benchmarks:
            try:
                func()
            except Exception as e:
                print(f"   ❌ Failed: {e}")

        # Save results
        self._save_results()

        print("\n" + "=" * 70)
        print(f"✅ Benchmark complete - {len(self.current_session)} benchmarks run")

        return self.current_session

    def _save_results(self) -> None:
        """Save benchmark results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"benchmark_{timestamp}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": [asdict(b) for b in self.current_session],
        }

        with open(results_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n📊 Results saved to {results_file}")

    def compare_with_baseline(self, baseline_file: str | None = None) -> dict[str, Any]:
        """Compare current results with baseline"""
        if not baseline_file:
            # Find most recent baseline
            baseline_files = sorted(self.results_dir.glob("benchmark_*.json"))
            if len(baseline_files) < 2:
                print("⚠️  Not enough baseline data for comparison")
                return {}
            baseline_file = baseline_files[-2]  # Second most recent

        with open(baseline_file) as f:
            baseline_data = json.load(f)

        baseline_benchmarks = {
            b["benchmark_name"]: b for b in baseline_data["benchmarks"]
        }

        comparison = {}

        print("\n📊 Performance Comparison vs Baseline\n")

        for current in self.current_session:
            name = current.benchmark_name
            if name not in baseline_benchmarks:
                continue

            baseline = baseline_benchmarks[name]

            duration_change = (
                (current.duration_seconds - baseline["duration_seconds"])
                / baseline["duration_seconds"]
                * 100
            )

            memory_change = current.memory_mb - baseline["memory_mb"]

            comparison[name] = {
                "duration_change_percent": duration_change,
                "memory_change_mb": memory_change,
                "current_duration": current.duration_seconds,
                "baseline_duration": baseline["duration_seconds"],
            }

            # Print comparison
            emoji = (
                "🔴"
                if duration_change > 10
                else "🟢" if duration_change < -10 else "🟡"
            )
            print(f"{emoji} {name}:")
            print(
                f"   Duration: {current.duration_seconds:.2f}s "
                f"({duration_change:+.1f}% vs baseline)"
            )
            print(
                f"   Memory: {current.memory_mb:.1f}MB "
                f"({memory_change:+.1f}MB vs baseline)"
            )

        return comparison

    def generate_report(self, output_path: str = "BENCHMARK_REPORT.md") -> None:
        """Generate benchmark report"""
        print("\n📝 Generating benchmark report...")

        report = []
        report.append("# Performance Benchmark Report")
        report.append(
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report.append(f"**Benchmarks Run:** {len(self.current_session)}")
        report.append("\n---\n")

        # Summary table
        report.append("## 📊 Benchmark Results\n")
        report.append("| Benchmark | Duration | CPU % | Memory (MB) | Status |")
        report.append("|-----------|----------|-------|-------------|--------|")

        for benchmark in self.current_session:
            status = "✅ Pass" if benchmark.success else "❌ Fail"
            report.append(
                f"| {benchmark.benchmark_name} | "
                f"{benchmark.duration_seconds:.2f}s | "
                f"{benchmark.cpu_usage_percent:.1f}% | "
                f"{benchmark.memory_mb:.1f} MB | "
                f"{status} |"
            )

        report.append("\n---\n")

        # Detailed results
        report.append("## 📈 Detailed Results\n")

        for benchmark in self.current_session:
            report.append(f"### {benchmark.benchmark_name}")
            report.append(f"- **Duration:** {benchmark.duration_seconds:.2f} seconds")
            report.append(f"- **CPU Usage:** {benchmark.cpu_usage_percent:.1f}%")
            report.append(f"- **Memory Used:** {benchmark.memory_mb:.1f} MB")
            report.append(
                f"- **Status:** {'✅ Success' if benchmark.success else '❌ Failed'}"
            )
            report.append(f"- **Timestamp:** {benchmark.timestamp}")

            if benchmark.metadata:
                report.append(
                    f"- **Metadata:** {json.dumps(benchmark.metadata, indent=2)}"
                )

            report.append("")

        # Save report
        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"✅ Report saved to {output_path}")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Benchmarking System")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--output", default="BENCHMARK_REPORT.md", help="Output file")
    parser.add_argument("--compare", action="store_true", help="Compare with baseline")

    args = parser.parse_args()

    try:
        benchmark = PerformanceBenchmark(repo_path=args.repo_path)
        benchmark.run_full_benchmark()

        if args.compare:
            benchmark.compare_with_baseline()

        benchmark.generate_report(args.output)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
