#!/usr/bin/env python3
"""
Prometheus Metrics Exporter for CI/CD Workflows
Exports workflow metrics for monitoring with Prometheus and Grafana
"""

import json

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    push_to_gateway,
    write_to_textfile,
)


class WorkflowMetricsExporter:
    """Export workflow metrics to Prometheus"""

    def __init__(self, pushgateway_url: str = None):
        self.registry = CollectorRegistry()
        self.pushgateway_url = pushgateway_url or "localhost:9091"
        self._setup_metrics()

    def _setup_metrics(self):
        """Setup Prometheus metrics"""
        # Gauges for current state
        self.health_score = Gauge(
            "repo_health_score",
            "Overall repository health score (0-100)",
            registry=self.registry,
        )

        self.test_coverage = Gauge(
            "test_coverage_percentage",
            "Test coverage percentage",
            registry=self.registry,
        )

        self.code_quality_score = Gauge(
            "code_quality_score",
            "Code quality score from analysis tools",
            ["tool"],
            registry=self.registry,
        )

        self.complexity_avg = Gauge(
            "code_complexity_average",
            "Average cyclomatic complexity",
            registry=self.registry,
        )

        self.maintainability_avg = Gauge(
            "code_maintainability_average",
            "Average maintainability index",
            registry=self.registry,
        )

        # Counters for events
        self.workflow_runs = Counter(
            "workflow_runs_total",
            "Total workflow runs",
            ["workflow", "status"],
            registry=self.registry,
        )

        self.security_issues = Counter(
            "security_issues_total",
            "Total security issues found",
            ["severity"],
            registry=self.registry,
        )

        self.quality_violations = Counter(
            "quality_violations_total",
            "Total code quality violations",
            ["type", "severity"],
            registry=self.registry,
        )

        # Histograms for distributions
        self.workflow_duration = Histogram(
            "workflow_duration_seconds",
            "Workflow execution duration in seconds",
            ["workflow"],
            registry=self.registry,
            buckets=[30, 60, 120, 300, 600, 1800, 3600],
        )

        self.test_duration = Histogram(
            "test_duration_seconds",
            "Test execution duration in seconds",
            registry=self.registry,
            buckets=[1, 5, 10, 30, 60, 120, 300],
        )

    def collect_metrics(self):
        """Collect metrics from various sources"""
        # Health score
        health_data = self._load_json("analysis-results.json")
        if health_data:
            score = self._calculate_health_score(health_data)
            self.health_score.set(score)

        # Test coverage
        coverage_data = self._load_json("coverage.json")
        if coverage_data:
            coverage_pct = coverage_data.get("totals", {}).get("percent_covered", 0)
            self.test_coverage.set(coverage_pct)

        # Code quality scores
        if health_data:
            for tool, data in health_data.get("tools", {}).items():
                score = 100 if data["status"] == "passed" else 0
                self.code_quality_score.labels(tool=tool).set(score)

        # Complexity metrics
        complexity_data = self._load_json("complexity.json")
        if complexity_data:
            avg_complexity = self._calculate_avg_complexity(complexity_data)
            self.complexity_avg.set(avg_complexity)

        # Maintainability
        mi_data = self._load_json("maintainability.json")
        if mi_data:
            avg_mi = self._calculate_avg_maintainability(mi_data)
            self.maintainability_avg.set(avg_mi)

        # Security issues
        security_data = self._load_json("bandit-report.json")
        if security_data:
            for issue in security_data.get("results", []):
                severity = issue.get("issue_severity", "UNKNOWN").lower()
                self.security_issues.labels(severity=severity).inc()

        # Quality violations
        violations_data = self._load_json("threshold-violations.json")
        if violations_data:
            for v in violations_data.get("violations", []):
                self.quality_violations.labels(
                    type=v.get("type", "unknown"), severity=v.get("severity", "unknown")
                ).inc()

        # Workflow metrics
        if health_data:
            duration = health_data.get("elapsed_seconds", 0)
            self.workflow_duration.labels(workflow="code_analysis").observe(duration)

            status = "success" if health_data.get("passed") else "failure"
            self.workflow_runs.labels(workflow="code_analysis", status=status).inc()

    def _load_json(self, filename: str) -> dict:
        """Load JSON file"""
        try:
            with open(filename) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _calculate_health_score(self, data: dict) -> int:
        """Calculate health score from analysis data"""
        # Simple calculation - can be enhanced
        return 100 if data.get("passed") else 70

    def _calculate_avg_complexity(self, data: dict) -> float:
        """Calculate average complexity"""
        total = 0
        count = 0

        for functions in data.values():
            for func in functions:
                total += func.get("complexity", 0)
                count += 1

        return total / count if count > 0 else 0

    def _calculate_avg_maintainability(self, data: dict) -> float:
        """Calculate average maintainability index"""
        scores = []

        for value in data.values():
            if isinstance(value, dict):
                scores.append(value.get("mi", 100))
            else:
                scores.append(value)

        return sum(scores) / len(scores) if scores else 100

    def export_to_file(self, filename: str = "metrics.prom"):
        """Export metrics to file for Prometheus to scrape"""
        write_to_textfile(filename, self.registry)
        print(f"✅ Metrics exported to {filename}")

    def push_to_gateway(self, job: str = "github_actions"):
        """Push metrics to Prometheus Pushgateway"""
        try:
            push_to_gateway(self.pushgateway_url, job=job, registry=self.registry)
            print(f"✅ Metrics pushed to {self.pushgateway_url}")
        except Exception as e:
            print(f"⚠️  Failed to push metrics: {e}")

    def generate_summary(self) -> str:
        """Generate human-readable metrics summary"""
        summary = "# 📊 Workflow Metrics Summary\n\n"

        # Get current metric values
        coverage_data = self._load_json("coverage.json")
        health_data = self._load_json("analysis-results.json")

        if coverage_data:
            coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
            summary += f"**Test Coverage:** {coverage:.1f}%\n"

        if health_data:
            summary += f"**Analysis Status:** {'✅ Passed' if health_data.get('passed') else '❌ Failed'}\n"
            summary += f"**Duration:** {health_data.get('elapsed_seconds', 0):.2f}s\n"

        return summary


def main():
    """Main entry point"""
    print("📊 Exporting workflow metrics...")

    exporter = WorkflowMetricsExporter()

    # Collect all metrics
    exporter.collect_metrics()

    # Export to file
    exporter.export_to_file("metrics.prom")

    # Try to push to gateway (optional)
    # exporter.push_to_gateway()

    # Generate summary
    summary = exporter.generate_summary()
    print(summary)

    print("✅ Metrics export complete")


if __name__ == "__main__":
    main()
