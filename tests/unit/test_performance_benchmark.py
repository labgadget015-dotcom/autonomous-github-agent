"""Unit tests for .github/scripts/performance_benchmark.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest
from dataclasses import asdict
from datetime import datetime

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from performance_benchmark import PerformanceBenchmark, BenchmarkResult


def _make_benchmark(tmp_path: Path):
    return PerformanceBenchmark(repo_path=str(tmp_path))


def _make_result(name="test", success=True, duration=1.0, cpu=10.0, memory=50.0):
    return BenchmarkResult(
        timestamp=datetime.now().isoformat(),
        benchmark_name=name,
        duration_seconds=duration,
        cpu_usage_percent=cpu,
        memory_mb=memory,
        success=success,
        metadata={"framework": "pytest"},
    )


class TestBenchmarkResultDataclass:
    def test_creates_with_required_fields(self):
        result = _make_result()
        assert result.benchmark_name == "test"
        assert result.success is True

    def test_asdict_conversion(self):
        result = _make_result()
        data = asdict(result)
        assert isinstance(data, dict)
        assert "benchmark_name" in data
        assert "duration_seconds" in data


class TestPerformanceBenchmarkInit:
    def test_creates_with_repo_path(self, tmp_path):
        b = _make_benchmark(tmp_path)
        assert b.repo_path == tmp_path

    def test_creates_results_dir(self, tmp_path):
        b = _make_benchmark(tmp_path)
        assert (tmp_path / ".benchmark_results").exists()

    def test_initial_session_is_empty(self, tmp_path):
        b = _make_benchmark(tmp_path)
        assert b.current_session == []


class TestSaveResults:
    def test_saves_results_to_file(self, tmp_path):
        b = _make_benchmark(tmp_path)
        b.current_session = [_make_result()]
        b._save_results()
        files = list((tmp_path / ".benchmark_results").glob("benchmark_*.json"))
        assert len(files) == 1
        data = json.loads(files[0].read_text())
        assert len(data["benchmarks"]) == 1

    def test_saved_file_has_timestamp(self, tmp_path):
        b = _make_benchmark(tmp_path)
        b.current_session = [_make_result()]
        b._save_results()
        files = list((tmp_path / ".benchmark_results").glob("benchmark_*.json"))
        data = json.loads(files[0].read_text())
        assert "timestamp" in data


class TestCompareWithBaseline:
    def test_returns_empty_when_no_files(self, tmp_path):
        b = _make_benchmark(tmp_path)
        result = b.compare_with_baseline()
        assert result == {}

    def test_returns_empty_with_single_file(self, tmp_path):
        b = _make_benchmark(tmp_path)
        b.current_session = [_make_result()]
        b._save_results()
        result = b.compare_with_baseline()
        assert result == {}

    def test_compares_with_existing_baseline(self, tmp_path):
        b = _make_benchmark(tmp_path)
        # Create a baseline file
        baseline_data = {
            "timestamp": "2024-01-01T00:00:00",
            "benchmarks": [asdict(_make_result("test_suite", duration=5.0))],
        }
        baseline_file = (
            tmp_path / ".benchmark_results" / "benchmark_20240101_000000.json"
        )
        baseline_file.write_text(json.dumps(baseline_data))

        # Current session has faster results
        b.current_session = [_make_result("test_suite", duration=3.0)]
        comparison = b.compare_with_baseline(str(baseline_file))
        assert "test_suite" in comparison
        assert comparison["test_suite"]["current_duration"] == 3.0


class TestGenerateReport:
    def test_generates_report_file(self, tmp_path):
        b = _make_benchmark(tmp_path)
        output = str(tmp_path / "report.md")
        b.generate_report(output)
        assert Path(output).exists()

    def test_empty_session_report(self, tmp_path):
        b = _make_benchmark(tmp_path)
        output = str(tmp_path / "report.md")
        b.generate_report(output)
        content = Path(output).read_text()
        assert "Benchmark Report" in content

    def test_report_with_results(self, tmp_path):
        b = _make_benchmark(tmp_path)
        b.current_session = [_make_result("lint", success=True, duration=2.5)]
        output = str(tmp_path / "report.md")
        b.generate_report(output)
        content = Path(output).read_text()
        assert "lint" in content
        assert "2.50" in content
