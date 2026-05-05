"""Performance Monitoring and Benchmarking System

This module provides comprehensive performance tracking and benchmarking
capabilities for the GitHub Autopilot AI optimization system.
"""

import json
import logging
import statistics
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Track and analyze performance metrics for AI optimization."""

    def __init__(self, config=None, history_size: int = 1000):
        """Initialize performance monitor.

        Args:
            config: Optional configuration dict
            history_size: Maximum number of historical records to keep
        """
        self.config = config or {}
        self.metrics: dict[str, Any] = {
            # Speed metrics
            "execution_time": deque(maxlen=history_size),
            "api_response_time": deque(maxlen=history_size),
            "cache_hit_rate": deque(maxlen=history_size),
            # Efficiency metrics
            "api_calls_per_run": deque(maxlen=history_size),
            "memory_usage": deque(maxlen=history_size),
            "cpu_utilization": deque(maxlen=history_size),
            # Accuracy metrics
            "priority_precision": deque(maxlen=history_size),
            "relevance_f1_score": deque(maxlen=history_size),
            "summary_quality_score": deque(maxlen=history_size),
            # Resource metrics
            "rate_limit_efficiency": deque(maxlen=history_size),
            "cost_per_execution": deque(maxlen=history_size),
        }

        self.benchmarks: dict[str, Any] = {}
        self.baseline = None
        self.process = psutil.Process()

    def record_metric(self, metric_name: str, value: float):
        """Record a single metric value.

        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        if metric_name in self.metrics:
            self.metrics[metric_name].append({"timestamp": time.time(), "value": value})
            logger.debug(f"Recorded {metric_name}: {value}")
        else:
            # Allow arbitrary metric names by creating a new deque
            self.metrics[metric_name] = deque(maxlen=1000)
            self.metrics[metric_name].append({"timestamp": time.time(), "value": value})
            logger.debug(f"Recorded new metric {metric_name}: {value}")

    def record(self, metric_name: str, value: float):
        """Alias for record_metric."""
        self.record_metric(metric_name, value)

    def get_metrics(self) -> dict[str, Any]:
        """Return current metrics summary."""
        return self.get_summary()

    def benchmark(
        self,
        func: Callable,
        name: str | None = None,
        track_memory: bool = True,
        track_cpu: bool = True,
    ) -> Any:
        """Benchmark a function execution.

        Args:
            func: Function to benchmark
            name: Name for this benchmark
            track_memory: Whether to track memory usage
            track_cpu: Whether to track CPU usage

        Returns:
            Function result
        """
        name = name or func.__name__

        # Record initial state
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = self.process.cpu_percent(interval=0.1)

        # Execute function
        try:
            result = func()
            success = True
            error = None
        except Exception as e:
            logger.error(f"Benchmark error in {name}: {e}")
            result = None
            success = False
            error = str(e)

        # Record final state
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = self.process.cpu_percent(interval=0.1)

        # Calculate metrics
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        cpu_used = (start_cpu + end_cpu) / 2  # Average

        # Store benchmark
        benchmark_data = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "success": success,
            "error": error,
        }

        if track_memory:
            benchmark_data["memory_used_mb"] = memory_used
            benchmark_data["memory_peak_mb"] = end_memory

        if track_cpu:
            benchmark_data["cpu_percent"] = cpu_used

        if name not in self.benchmarks:
            self.benchmarks[name] = []
        self.benchmarks[name].append(benchmark_data)

        # Record to metrics
        self.record_metric("execution_time", execution_time)
        if track_memory:
            self.record_metric("memory_usage", memory_used)
        if track_cpu:
            self.record_metric("cpu_utilization", cpu_used)

        logger.info(f"Benchmark {name}: {execution_time:.3f}s")

        return result

    def get_metric_stats(self, metric_name: str) -> dict[str, float] | None:
        """Get statistics for a specific metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Dictionary with statistics or None if no data
        """
        if metric_name not in self.metrics:
            return None

        data = self.metrics[metric_name]
        if not data:
            return None

        values = [d["value"] for d in data]

        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else None,
        }

    def get_benchmark_stats(self, name: str) -> dict[str, Any] | None:
        """Get statistics for a specific benchmark.

        Args:
            name: Benchmark name

        Returns:
            Dictionary with benchmark statistics or None
        """
        if name not in self.benchmarks:
            return None

        benchmarks = self.benchmarks[name]
        if not benchmarks:
            return None

        times = [b["execution_time"] for b in benchmarks if b["success"]]
        success_rate = sum(1 for b in benchmarks if b["success"]) / len(benchmarks)

        stats = {
            "total_runs": len(benchmarks),
            "success_rate": success_rate,
            "avg_time": statistics.mean(times) if times else 0,
            "median_time": statistics.median(times) if times else 0,
            "min_time": min(times) if times else 0,
            "max_time": max(times) if times else 0,
            "latest_run": benchmarks[-1],
        }

        # Add memory stats if available
        memory_data = [
            b.get("memory_used_mb", 0) for b in benchmarks if "memory_used_mb" in b
        ]
        if memory_data:
            stats["avg_memory_mb"] = statistics.mean(memory_data)
            stats["peak_memory_mb"] = max(
                b.get("memory_peak_mb", 0) for b in benchmarks
            )

        return stats

    def set_baseline(self):
        """Set current state as baseline for comparisons."""
        self.baseline = {
            metric: self.get_metric_stats(metric) for metric in self.metrics.keys()
        }
        logger.info("Baseline metrics established")

    def compare_to_baseline(self) -> dict[str, dict[str, float]]:
        """Compare current metrics to baseline.

        Returns:
            Dictionary with comparison results
        """
        if not self.baseline:
            logger.warning("No baseline set")
            return {}

        comparison = {}

        for metric_name in self.metrics.keys():
            current = self.get_metric_stats(metric_name)
            baseline = self.baseline.get(metric_name)

            if current and baseline and baseline.get("mean"):
                improvement = (
                    (baseline["mean"] - current["mean"]) / baseline["mean"] * 100
                )

                comparison[metric_name] = {
                    "baseline_mean": baseline["mean"],
                    "current_mean": current["mean"],
                    "improvement_percent": improvement,
                    "status": "improved" if improvement > 0 else "degraded",
                }

        return comparison

    def get_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary.

        Returns:
            Dictionary with all performance data
        """
        summary: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "benchmarks": {},
            "system": {
                "cpu_count": psutil.cpu_count(),
                "total_memory_gb": psutil.virtual_memory().total / 1024**3,
                "available_memory_gb": psutil.virtual_memory().available / 1024**3,
            },
        }

        # Add metric statistics
        for metric_name in self.metrics.keys():
            stats = self.get_metric_stats(metric_name)
            if stats:
                summary["metrics"][metric_name] = stats

        # Add benchmark statistics
        for bench_name in self.benchmarks.keys():
            stats = self.get_benchmark_stats(bench_name)
            if stats:
                summary["benchmarks"][bench_name] = stats

        # Add baseline comparison if available
        if self.baseline:
            summary["baseline_comparison"] = self.compare_to_baseline()

        return summary

    def save_report(self, filepath: str):
        """Save performance report to file.

        Args:
            filepath: Path to save report
        """
        summary = self.get_summary()

        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Performance report saved to {filepath}")

    def print_summary(self):
        """Log performance summary."""
        summary = self.get_summary()

        logger.info("=" * 70)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("=" * 70)

        logger.info("Key Metrics:")
        for metric_name, stats in summary["metrics"].items():
            if stats and stats.get("count", 0) > 0:
                logger.info("  %s:", metric_name)
                logger.info("    Mean: %.3f", stats["mean"])
                logger.info("    Latest: %.3f", stats["latest"])
                if stats.get("stdev", 0) > 0:
                    logger.info("    StdDev: %.3f", stats["stdev"])

        logger.info("Benchmarks:")
        for bench_name, stats in summary["benchmarks"].items():
            logger.info("  %s:", bench_name)
            logger.info("    Runs: %s", stats["total_runs"])
            logger.info("    Success Rate: %.1f%%", stats["success_rate"] * 100)
            logger.info("    Avg Time: %.3fs", stats["avg_time"])
            if "avg_memory_mb" in stats:
                logger.info("    Avg Memory: %.1f MB", stats["avg_memory_mb"])

        if "baseline_comparison" in summary:
            logger.info("Improvements vs Baseline:")
            for metric, comp in summary["baseline_comparison"].items():
                if abs(comp["improvement_percent"]) > 1:  # Show if >1% change
                    symbol = "✓" if comp["status"] == "improved" else "✗"
                    logger.info("  %s %s: %+.1f%%", symbol, metric, comp["improvement_percent"])

        logger.info("=" * 70)

    def check_performance_targets(self, targets: dict[str, float]) -> dict[str, bool]:
        """Check if performance meets target thresholds.

        Args:
            targets: Dictionary of metric_name: target_value pairs

        Returns:
            Dictionary of metric_name: meets_target boolean
        """
        results = {}

        for metric_name, target_value in targets.items():
            stats = self.get_metric_stats(metric_name)
            if stats:
                current_value = stats["mean"]
                # Assume lower is better for most metrics
                meets_target = current_value <= target_value
                results[metric_name] = meets_target

                status = "✓ PASS" if meets_target else "✗ FAIL"
                logger.info(
                    f"{status}: {metric_name} - "
                    f"Current: {current_value:.2f}, "
                    f"Target: {target_value:.2f}"
                )
            else:
                results[metric_name] = False
                logger.warning(f"No data for metric: {metric_name}")

        return results


# Global monitor instance
_global_monitor: PerformanceMonitor | None = None
_global_monitor_lock = threading.Lock()


def get_monitor() -> PerformanceMonitor:
    """Get global monitor instance (thread-safe)."""
    global _global_monitor
    if _global_monitor is None:
        with _global_monitor_lock:
            if _global_monitor is None:
                _global_monitor = PerformanceMonitor()
    return _global_monitor


if __name__ == "__main__":
    # Example usage
    monitor = PerformanceMonitor()

    # Example benchmark
    def example_task():
        """Simulate some work."""
        total = 0
        for i in range(1000000):
            total += i
        return total

    # Run benchmarks
    print("Running performance benchmarks...")

    for _ in range(5):
        result = monitor.benchmark(example_task, name="example_task")

    # Record some metrics
    monitor.record_metric("cache_hit_rate", 0.85)
    monitor.record_metric("cache_hit_rate", 0.90)
    monitor.record_metric("cache_hit_rate", 0.88)

    monitor.record_metric("api_calls_per_run", 25)
    monitor.record_metric("api_calls_per_run", 5)  # After optimization

    # Set baseline
    monitor.set_baseline()

    # Simulate improvement
    for _ in range(3):
        monitor.record_metric("cache_hit_rate", 0.92)
        monitor.record_metric("api_calls_per_run", 3)

    # Print summary
    monitor.print_summary()

    # Check targets
    targets = {
        "execution_time": 0.1,  # 100ms target
        "cache_hit_rate": 0.90,  # 90% target
        "api_calls_per_run": 10,  # Max 10 calls
    }

    results = monitor.check_performance_targets(targets)
    print("\nTarget Achievement:")
    for metric, passed in results.items():
        print(f"  {metric}: {'PASS ✓' if passed else 'FAIL ✗'}")
