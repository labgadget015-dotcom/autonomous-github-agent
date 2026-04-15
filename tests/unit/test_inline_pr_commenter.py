"""Unit tests for .github/scripts/inline_pr_commenter.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)


def _make_bot(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("PR_NUMBER", "42")
    monkeypatch.setenv("COMMIT_SHA", "abc123")
    from inline_pr_commenter import InlinePRCommentBot
    return InlinePRCommentBot()


class TestInlinePRCommentBotInit:
    def test_sets_pr_number(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        assert bot.pr_number == "42"

    def test_sets_repo(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        assert bot.repo == "owner/repo"

    def test_headers_have_auth(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        assert "Authorization" in bot.headers
        assert "fake-token" in bot.headers["Authorization"]


class TestLoadAnalysisResults:
    def test_returns_empty_when_no_files(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        bot = _make_bot(monkeypatch)
        result = bot.load_analysis_results()
        assert isinstance(result, list)

    def test_loads_pylint_results(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        pylint_data = [
            {"path": "module.py", "line": 10, "type": "error", "symbol": "undefined-variable", "message": "Undefined", "message-id": "E0602"}
        ]
        (tmp_path / "pylint-report.json").write_text(json.dumps(pylint_data))
        bot = _make_bot(monkeypatch)
        result = bot.load_analysis_results()
        assert len(result) >= 1
        assert any("module.py" in r["path"] for r in result)

    def test_loads_bandit_results(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        bandit_data = {
            "results": [
                {"filename": "module.py", "line_number": 5, "issue_severity": "HIGH", "issue_text": "SQL injection", "issue_confidence": "HIGH"}
            ]
        }
        (tmp_path / "bandit-report.json").write_text(json.dumps(bandit_data))
        bot = _make_bot(monkeypatch)
        result = bot.load_analysis_results()
        assert any("module.py" in r["path"] for r in result)

    def test_loads_complexity_results(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        complexity_data = {
            "module.py": [
                {"name": "complex_func", "lineno": 20, "complexity": 15}
            ]
        }
        (tmp_path / "complexity.json").write_text(json.dumps(complexity_data))
        bot = _make_bot(monkeypatch)
        result = bot.load_analysis_results()
        assert any("module.py" in r["path"] for r in result)


class TestFormatPylintComment:
    def test_format_creates_markdown(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        issue = {
            "symbol": "missing-docstring",
            "message": "Missing module docstring",
            "type": "convention",
            "message-id": "C0114"
        }
        comment = bot._format_pylint_comment(issue)
        assert "Pylint" in comment
        assert "missing-docstring" in comment

    def test_format_includes_fix_suggestion(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        issue = {"symbol": "missing-docstring", "message": "Missing", "type": "convention", "message-id": "C0114"}
        comment = bot._format_pylint_comment(issue)
        assert "docstring" in comment.lower()


class TestFormatBanditComment:
    def test_format_creates_markdown(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        issue = {
            "issue_severity": "HIGH",
            "issue_confidence": "HIGH",
            "issue_text": "SQL injection",
            "issue_cwe": {"id": "89"},
            "code": "cursor.execute(query)",
            "test_id": "B601"
        }
        comment = bot._format_bandit_comment(issue)
        assert "HIGH" in comment
        assert "SQL injection" in comment

    def test_high_severity_has_alert_emoji(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        issue = {"issue_severity": "HIGH", "issue_confidence": "HIGH", "issue_text": "Issue", "issue_cwe": {}, "code": ""}
        comment = bot._format_bandit_comment(issue)
        assert "🚨" in comment

    def test_medium_severity_has_warning_emoji(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        issue = {"issue_severity": "MEDIUM", "issue_confidence": "MEDIUM", "issue_text": "Issue", "issue_cwe": {}, "code": ""}
        comment = bot._format_bandit_comment(issue)
        assert "⚠️" in comment


class TestFormatComplexityComment:
    def test_format_includes_function_name(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        func = {"name": "my_complex_func", "complexity": 15}
        comment = bot._format_complexity_comment(func)
        assert "my_complex_func" in comment
        assert "15" in comment


class TestMapPylintSeverity:
    def test_error_maps_to_high(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        assert bot._map_pylint_severity("error") == "high"

    def test_warning_maps_to_medium(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        assert bot._map_pylint_severity("warning") == "medium"

    def test_convention_maps_to_low(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        assert bot._map_pylint_severity("convention") == "low"

    def test_unknown_maps_to_low(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        assert bot._map_pylint_severity("unknown_type") == "low"


class TestDeduplicateComments:
    def test_removes_same_file_line_duplicates(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        comments = [
            {"path": "module.py", "line": 10, "body": "Issue 1", "severity": "high"},
            {"path": "module.py", "line": 10, "body": "Issue 2", "severity": "medium"},
            {"path": "module.py", "line": 20, "body": "Issue 3", "severity": "low"},
        ]
        result = bot._deduplicate_comments(comments)
        assert len(result) == 2

    def test_different_files_not_deduplicated(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        comments = [
            {"path": "a.py", "line": 10, "body": "Issue 1", "severity": "high"},
            {"path": "b.py", "line": 10, "body": "Issue 2", "severity": "high"},
        ]
        result = bot._deduplicate_comments(comments)
        assert len(result) == 2


class TestGetPylintFixSuggestion:
    def test_known_symbol_returns_suggestion(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        suggestion = bot._get_pylint_fix_suggestion("line-too-long")
        assert len(suggestion) > 0
        assert "line" in suggestion.lower() or "break" in suggestion.lower()

    def test_unknown_symbol_returns_generic(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        suggestion = bot._get_pylint_fix_suggestion("unknown-symbol")
        assert len(suggestion) > 0


class TestGetSecurityRecommendation:
    def test_known_test_id_returns_recommendation(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        rec = bot._get_security_recommendation({"test_id": "B101"})
        assert "assert" in rec.lower()

    def test_unknown_test_id_returns_generic(self, monkeypatch):
        bot = _make_bot(monkeypatch)
        rec = bot._get_security_recommendation({"test_id": "B999"})
        assert len(rec) > 0
