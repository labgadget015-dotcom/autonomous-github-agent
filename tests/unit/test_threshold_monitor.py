"""Unit tests for .github/scripts/threshold_monitor.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest
import yaml

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from threshold_monitor import ThresholdMonitor


def _make_monitor(tmp_path=None):
    return ThresholdMonitor(
        config_path=(
            str(tmp_path / "nonexistent.yaml") if tmp_path else "/nonexistent/path.yaml"
        )
    )


class TestThresholdMonitorInit:
    def test_init_with_nonexistent_config_uses_defaults(self):
        monitor = _make_monitor()
        assert "thresholds" in monitor.config

    def test_default_coverage_threshold(self):
        monitor = _make_monitor()
        assert monitor.config["thresholds"]["coverage"] == 80

    def test_default_complexity_threshold(self):
        monitor = _make_monitor()
        assert monitor.config["thresholds"]["complexity"] == 10

    def test_load_custom_config(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            yaml.dump({"thresholds": {"coverage": 90, "complexity": 5}})
        )
        monitor = ThresholdMonitor(str(config_file))
        assert monitor.config["thresholds"]["coverage"] == 90


class TestCheckAnalysisResults:
    def test_returns_empty_when_file_missing(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        result = monitor.check_analysis_results(str(tmp_path / "missing.json"))
        assert result == []

    def test_detects_tool_failure(self, tmp_path):
        results_file = tmp_path / "results.json"
        results_file.write_text(
            json.dumps(
                {
                    "tools": {
                        "pylint": {"status": "failed", "errors": "E0001: syntax error"},
                    }
                }
            )
        )
        monitor = _make_monitor(tmp_path)
        violations = monitor.check_analysis_results(str(results_file))
        assert len(violations) == 1
        assert violations[0]["type"] == "tool_failure"
        assert violations[0]["tool"] == "pylint"

    def test_no_violations_when_all_pass(self, tmp_path):
        results_file = tmp_path / "results.json"
        results_file.write_text(
            json.dumps(
                {
                    "tools": {
                        "pylint": {"status": "passed"},
                        "flake8": {"status": "passed"},
                    }
                }
            )
        )
        monitor = _make_monitor(tmp_path)
        violations = monitor.check_analysis_results(str(results_file))
        assert violations == []


class TestCheckCoverage:
    def test_returns_none_when_file_missing(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        result = monitor.check_coverage(str(tmp_path / "missing.json"))
        assert result is None

    def test_returns_violation_when_below_threshold(self, tmp_path):
        cov_file = tmp_path / "coverage.json"
        cov_file.write_text(json.dumps({"totals": {"percent_covered": 60.0}}))
        monitor = _make_monitor(tmp_path)
        result = monitor.check_coverage(str(cov_file))
        assert result is not None
        assert result["type"] == "coverage"
        assert result["current"] == 60.0

    def test_returns_none_when_above_threshold(self, tmp_path):
        cov_file = tmp_path / "coverage.json"
        cov_file.write_text(json.dumps({"totals": {"percent_covered": 95.0}}))
        monitor = _make_monitor(tmp_path)
        result = monitor.check_coverage(str(cov_file))
        assert result is None

    def test_severity_high_when_far_below_threshold(self, tmp_path):
        cov_file = tmp_path / "coverage.json"
        cov_file.write_text(json.dumps({"totals": {"percent_covered": 50.0}}))
        monitor = _make_monitor(tmp_path)
        result = monitor.check_coverage(str(cov_file))
        assert result["severity"] == "high"

    def test_severity_medium_when_slightly_below(self, tmp_path):
        cov_file = tmp_path / "coverage.json"
        cov_file.write_text(json.dumps({"totals": {"percent_covered": 76.0}}))
        monitor = _make_monitor(tmp_path)
        result = monitor.check_coverage(str(cov_file))
        assert result["severity"] == "medium"


class TestCheckComplexity:
    def test_returns_empty_list_when_file_missing(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        result = monitor.check_complexity(str(tmp_path / "missing.json"))
        assert result == []

    def test_detects_high_complexity_function(self, tmp_path):
        complexity_file = tmp_path / "complexity.json"
        complexity_file.write_text(
            json.dumps(
                {
                    "src/module.py": [
                        {"name": "my_func", "complexity": 15, "lineno": 10},
                    ]
                }
            )
        )
        monitor = _make_monitor(tmp_path)
        violations = monitor.check_complexity(str(complexity_file))
        assert len(violations) == 1
        assert violations[0]["type"] == "complexity"
        assert violations[0]["function"] == "my_func"

    def test_ignores_low_complexity(self, tmp_path):
        complexity_file = tmp_path / "complexity.json"
        complexity_file.write_text(
            json.dumps(
                {
                    "src/module.py": [
                        {"name": "simple_func", "complexity": 3, "lineno": 5},
                    ]
                }
            )
        )
        monitor = _make_monitor(tmp_path)
        violations = monitor.check_complexity(str(complexity_file))
        assert violations == []


class TestCheckSecurity:
    def test_returns_empty_list_when_file_missing(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        result = monitor.check_security(str(tmp_path / "missing.json"))
        assert result == []

    def test_detects_security_issue(self, tmp_path):
        bandit_file = tmp_path / "bandit.json"
        bandit_file.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "issue_text": "Use of unsafe function",
                            "issue_severity": "HIGH",
                            "filename": "src/app.py",
                            "line_number": 42,
                            "issue_confidence": "HIGH",
                            "issue_cwe": {"id": "CWE-78"},
                        }
                    ]
                }
            )
        )
        monitor = _make_monitor(tmp_path)
        violations = monitor.check_security(str(bandit_file))
        assert len(violations) == 1
        assert violations[0]["type"] == "security"
        assert violations[0]["severity"] == "critical"  # HIGH maps to critical

    def test_medium_severity_maps_to_high(self, tmp_path):
        bandit_file = tmp_path / "bandit.json"
        bandit_file.write_text(
            json.dumps(
                {"results": [{"issue_severity": "MEDIUM", "issue_text": "issue"}]}
            )
        )
        monitor = _make_monitor(tmp_path)
        violations = monitor.check_security(str(bandit_file))
        assert violations[0]["severity"] == "high"

    def test_low_severity_maps_to_medium(self, tmp_path):
        bandit_file = tmp_path / "bandit.json"
        bandit_file.write_text(
            json.dumps({"results": [{"issue_severity": "LOW", "issue_text": "issue"}]})
        )
        monitor = _make_monitor(tmp_path)
        violations = monitor.check_security(str(bandit_file))
        assert violations[0]["severity"] == "medium"


class TestCreateGithubIssue:
    def _monitor(self):
        return _make_monitor()

    def test_security_violation_creates_issue_with_security_label(self):
        monitor = self._monitor()
        violation = {
            "type": "security",
            "severity": "critical",
            "message": "SQL injection detected",
            "file": "app.py",
            "line": 10,
            "confidence": "HIGH",
            "cwe": "CWE-89",
        }
        issue = monitor.create_github_issue(violation)
        assert "security" in issue["labels"]
        assert "Security" in issue["title"]

    def test_coverage_violation_creates_issue_with_testing_label(self):
        monitor = self._monitor()
        violation = {
            "type": "coverage",
            "severity": "high",
            "message": "Coverage below threshold",
            "current": 60.0,
            "threshold": 80,
        }
        issue = monitor.create_github_issue(violation)
        assert "testing" in issue["labels"]
        assert "Coverage" in issue["title"]

    def test_complexity_violation_creates_issue_with_refactoring_label(self):
        monitor = self._monitor()
        violation = {
            "type": "complexity",
            "severity": "medium",
            "message": "High complexity",
            "file": "module.py",
            "function": "big_func",
            "complexity": 20,
            "threshold": 10,
            "line": 5,
        }
        issue = monitor.create_github_issue(violation)
        assert "refactoring" in issue["labels"]
        assert "Complexity" in issue["title"]

    def test_issue_contains_body(self):
        monitor = self._monitor()
        violation = {
            "type": "tool_failure",
            "severity": "high",
            "message": "pylint failed",
            "tool": "pylint",
        }
        issue = monitor.create_github_issue(violation)
        assert isinstance(issue["body"], str)
        assert len(issue["body"]) > 0


class TestGenerateSummaryReport:
    def test_no_violations_returns_success_message(self):
        monitor = _make_monitor()
        report = monitor.generate_summary_report([])
        assert "No threshold violations" in report

    def test_violations_appear_in_report(self):
        monitor = _make_monitor()
        violations = [
            {"type": "security", "severity": "critical", "message": "SQL injection"},
            {"type": "coverage", "severity": "high", "message": "Low coverage"},
        ]
        report = monitor.generate_summary_report(violations)
        assert "2" in report  # total violations
        assert "CRITICAL" in report or "HIGH" in report


class TestSaveViolations:
    def test_saves_violations_to_file(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        violations = [{"type": "coverage", "severity": "high", "message": "low cov"}]
        output_file = str(tmp_path / "violations.json")
        monitor.save_violations(violations, output_file)
        data = json.loads(Path(output_file).read_text())
        assert data["total_violations"] == 1
        assert len(data["violations"]) == 1
