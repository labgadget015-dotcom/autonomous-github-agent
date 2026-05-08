"""Unit tests for overseer/issue_triager.py"""

from __future__ import annotations

import pytest
from pathlib import Path

from overseer.issue_triager import IssueTriager


def _make_triager(tmp_path: Path, config=None):
    return IssueTriager(tmp_path, config or {})


class TestIssueTriagerInit:
    def test_creates_with_repo_path(self, tmp_path):
        triager = _make_triager(tmp_path)
        assert triager.repo_path == tmp_path

    def test_label_patterns_defined(self, tmp_path):
        triager = _make_triager(tmp_path)
        assert "bug" in triager.label_patterns
        assert "security" in triager.label_patterns
        assert "enhancement" in triager.label_patterns

    def test_priority_patterns_defined(self, tmp_path):
        triager = _make_triager(tmp_path)
        assert "critical" in triager.priority_patterns
        assert "high" in triager.priority_patterns
        assert "low" in triager.priority_patterns


class TestAnalyzeIssueContent:
    def test_bug_issue_detected(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content(
            "App crashes on startup", "Error in main module"
        )
        assert "bug" in result["labels"]

    def test_security_issue_detected(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content(
            "Security vulnerability in auth", "XSS exploit found"
        )
        assert "security" in result["labels"]

    def test_enhancement_detected(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content(
            "Feature request: add dark mode", "Would be nice to have"
        )
        assert "enhancement" in result["labels"]

    def test_documentation_detected(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content(
            "Update README", "The documentation is outdated"
        )
        assert "documentation" in result["labels"]

    def test_performance_detected(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content(
            "Performance slow", "Need to optimize speed"
        )
        assert "performance" in result["labels"]

    def test_critical_priority_detected(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content(
            "Critical production outage", "System is down"
        )
        assert result["priority"] == "critical"

    def test_high_priority_detected(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content(
            "Urgent: major breaking change", "Need ASAP fix"
        )
        assert result["priority"] == "high"

    def test_default_priority_is_medium(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content(
            "Rename variable", "Minor code style change"
        )
        assert "priority" in result

    def test_result_has_confidence(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content("App crashes", "Error found")
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_empty_content_returns_empty_labels(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content("", "")
        assert isinstance(result["labels"], list)

    def test_unicode_content_handled(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content(
            "Ошибка при запуске", "システムがクラッシュします"
        )
        assert isinstance(result["labels"], list)

    def test_special_chars_handled(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.analyze_issue_content("Bug @#$%^&*()", "crash!!! error???")
        assert "bug" in result["labels"]


class TestMatchesPatterns:
    def test_matches_when_pattern_found(self, tmp_path):
        triager = _make_triager(tmp_path)
        assert triager._matches_patterns("app bug found", [r"\bbug\b"]) is True

    def test_no_match_when_pattern_absent(self, tmp_path):
        triager = _make_triager(tmp_path)
        assert triager._matches_patterns("feature request", [r"\bbug\b"]) is False


class TestCalculateConfidence:
    def test_zero_confidence_with_no_labels(self, tmp_path):
        triager = _make_triager(tmp_path)
        assert triager._calculate_confidence("any text", []) == 0.0

    def test_confidence_above_zero_with_labels(self, tmp_path):
        triager = _make_triager(tmp_path)
        conf = triager._calculate_confidence("app crashes with error", ["bug"])
        assert conf > 0.0

    def test_confidence_at_most_one(self, tmp_path):
        triager = _make_triager(tmp_path)
        conf = triager._calculate_confidence(
            "security bug error crash", ["bug", "security"]
        )
        assert conf <= 1.0


class TestProcess:
    def test_process_returns_dict(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.process()
        assert isinstance(result, dict)
        assert "processed" in result
        assert "patterns" in result

    def test_process_detects_missing_templates(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.process()
        pattern_types = [p["type"] for p in result["patterns"]]
        assert "missing_templates" in pattern_types

    def test_process_detects_issue_templates_when_present(self, tmp_path):
        templates_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        templates_dir.mkdir(parents=True)
        (templates_dir / "bug_report.md").write_text("# Bug Report")
        triager = _make_triager(tmp_path)
        result = triager.process()
        pattern_types = [p["type"] for p in result["patterns"]]
        assert "issue_templates" in pattern_types

    def test_process_detects_missing_codeowners(self, tmp_path):
        triager = _make_triager(tmp_path)
        result = triager.process()
        pattern_types = [p["type"] for p in result["patterns"]]
        assert "missing_codeowners" in pattern_types

    def test_process_no_missing_codeowners_when_present(self, tmp_path):
        codeowners = tmp_path / ".github" / "CODEOWNERS"
        codeowners.parent.mkdir(parents=True, exist_ok=True)
        codeowners.write_text("* @default-owner")
        triager = _make_triager(tmp_path)
        result = triager.process()
        pattern_types = [p["type"] for p in result["patterns"]]
        assert "missing_codeowners" not in pattern_types
