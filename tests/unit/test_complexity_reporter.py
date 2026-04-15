"""Unit tests for .github/scripts/complexity_reporter.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from complexity_reporter import ComplexityReporter


def _make_reporter(tmp_path, complexity_data=None, maintainability_data=None):
    """Create a reporter with pre-populated data."""
    reporter = ComplexityReporter.__new__(ComplexityReporter)
    reporter.complexity_data = complexity_data or {}
    reporter.maintainability_data = maintainability_data or {}
    reporter.thresholds = {"complexity": 10, "maintainability": 65}
    return reporter


class TestLoadJson:
    def test_load_valid_json_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        data = {"key": "value"}
        (tmp_path / "test.json").write_text(json.dumps(data))
        reporter = ComplexityReporter.__new__(ComplexityReporter)
        result = reporter._load_json("test.json")
        assert result == data

    def test_returns_empty_dict_for_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        reporter = ComplexityReporter.__new__(ComplexityReporter)
        result = reporter._load_json("nonexistent.json")
        assert result == {}

    def test_returns_empty_dict_for_invalid_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "bad.json").write_text("{invalid}")
        reporter = ComplexityReporter.__new__(ComplexityReporter)
        result = reporter._load_json("bad.json")
        assert result == {}


class TestAnalyzeComplexity:
    def test_empty_data_returns_zeros(self):
        reporter = _make_reporter(None)
        issues = reporter.analyze_complexity()
        assert issues["total_functions"] == 0
        assert issues["avg_complexity"] == 0
        assert issues["high_complexity"] == []
        assert issues["low_maintainability"] == []

    def test_high_complexity_function_flagged(self):
        reporter = _make_reporter(
            None,
            complexity_data={
                "src/module.py": [
                    {"name": "complex_func", "complexity": 15, "lineno": 10},
                ]
            }
        )
        issues = reporter.analyze_complexity()
        assert len(issues["high_complexity"]) == 1
        assert issues["high_complexity"][0]["function"] == "complex_func"

    def test_low_complexity_not_flagged(self):
        reporter = _make_reporter(
            None,
            complexity_data={
                "src/module.py": [
                    {"name": "simple_func", "complexity": 3, "lineno": 1},
                ]
            }
        )
        issues = reporter.analyze_complexity()
        assert len(issues["high_complexity"]) == 0

    def test_average_complexity_calculated(self):
        reporter = _make_reporter(
            None,
            complexity_data={
                "src/module.py": [
                    {"name": "func_a", "complexity": 4, "lineno": 1},
                    {"name": "func_b", "complexity": 6, "lineno": 20},
                ]
            }
        )
        issues = reporter.analyze_complexity()
        assert issues["avg_complexity"] == 5.0
        assert issues["total_functions"] == 2

    def test_low_maintainability_flagged(self):
        reporter = _make_reporter(
            None,
            maintainability_data={"src/module.py": 40.0}
        )
        issues = reporter.analyze_complexity()
        assert len(issues["low_maintainability"]) == 1

    def test_high_maintainability_not_flagged(self):
        reporter = _make_reporter(
            None,
            maintainability_data={"src/module.py": 80.0}
        )
        issues = reporter.analyze_complexity()
        assert len(issues["low_maintainability"]) == 0

    def test_maintainability_as_dict_with_mi_key(self):
        reporter = _make_reporter(
            None,
            maintainability_data={"src/module.py": {"mi": 50.0}}
        )
        issues = reporter.analyze_complexity()
        assert len(issues["low_maintainability"]) == 1


class TestGenerateMarkdownReport:
    def test_report_is_string(self):
        reporter = _make_reporter(None)
        issues = reporter.analyze_complexity()
        report = reporter.generate_markdown_report(issues)
        assert isinstance(report, str)

    def test_report_contains_summary(self):
        reporter = _make_reporter(None)
        issues = reporter.analyze_complexity()
        report = reporter.generate_markdown_report(issues)
        assert "Total Functions" in report or "Summary" in report

    def test_report_contains_high_complexity_section(self):
        reporter = _make_reporter(
            None,
            complexity_data={
                "src/app.py": [{"name": "huge_func", "complexity": 25, "lineno": 1}]
            }
        )
        issues = reporter.analyze_complexity()
        report = reporter.generate_markdown_report(issues)
        assert "High Complexity" in report
        assert "huge_func" in report

    def test_report_contains_low_maintainability_section(self):
        reporter = _make_reporter(
            None,
            maintainability_data={"src/module.py": 30.0}
        )
        issues = reporter.analyze_complexity()
        report = reporter.generate_markdown_report(issues)
        assert "Maintainability" in report
        assert "module.py" in report


class TestGenerateRefactoringRecommendations:
    def test_returns_list(self):
        reporter = _make_reporter(None)
        issues = {"high_complexity": [], "low_maintainability": []}
        recs = reporter.generate_refactoring_recommendations(issues)
        assert isinstance(recs, list)

    def test_includes_high_complexity_recs(self):
        reporter = _make_reporter(None)
        issues = {
            "high_complexity": [
                {"function": "big_func", "file": "mod.py", "complexity": 25}
            ],
            "low_maintainability": [],
        }
        recs = reporter.generate_refactoring_recommendations(issues)
        assert len(recs) >= 1
        assert "big_func" in recs[0]

    def test_includes_low_maintainability_recs(self):
        reporter = _make_reporter(None)
        issues = {
            "high_complexity": [],
            "low_maintainability": [{"file": "legacy.py", "score": 30.0}],
        }
        recs = reporter.generate_refactoring_recommendations(issues)
        assert len(recs) >= 1
        assert "legacy.py" in recs[0]


class TestShouldBlockMerge:
    def test_blocks_when_very_high_complexity(self):
        reporter = _make_reporter(None)
        issues = {
            "high_complexity": [
                {"function": "huge", "file": "mod.py", "complexity": 25}
            ],
            "low_maintainability": [],
        }
        assert reporter.should_block_merge(issues) is True

    def test_no_block_with_moderate_complexity(self):
        reporter = _make_reporter(None)
        issues = {
            "high_complexity": [
                {"function": "moderate", "file": "mod.py", "complexity": 15}
            ],
            "low_maintainability": [],
        }
        assert reporter.should_block_merge(issues) is False

    def test_blocks_when_very_low_maintainability(self):
        reporter = _make_reporter(None)
        issues = {
            "high_complexity": [],
            "low_maintainability": [{"file": "mod.py", "score": 30.0}],
        }
        assert reporter.should_block_merge(issues) is True

    def test_no_block_with_no_issues(self):
        reporter = _make_reporter(None)
        issues = {"high_complexity": [], "low_maintainability": []}
        assert reporter.should_block_merge(issues) is False
