"""Unit tests for .github/scripts/issue_auto_creator.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)


def _make_creator(monkeypatch):
    """Create IssueAutoCreator with required env vars mocked."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    from issue_auto_creator import IssueAutoCreator

    return IssueAutoCreator()


class TestIssueAutoCreatorInit:
    def test_creates_with_env_vars(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        assert creator.github_token == "fake-token"
        assert creator.repo == "owner/repo"

    def test_default_quality_threshold(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        assert creator.quality_threshold == 7.0

    def test_custom_quality_threshold(self, monkeypatch):
        monkeypatch.setenv("QUALITY_THRESHOLD", "8.0")
        creator = _make_creator(monkeypatch)
        assert creator.quality_threshold == 8.0

    def test_default_coverage_threshold(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        assert creator.coverage_threshold == 80.0

    def test_default_complexity_threshold(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        assert creator.complexity_threshold == 10


class TestCheckQualityMetrics:
    def test_missing_file_returns_empty_list(self, monkeypatch, tmp_path):
        creator = _make_creator(monkeypatch)
        result = creator.check_quality_metrics(tmp_path / "nonexistent.json")
        assert result == []

    def test_low_quality_score_creates_issue(self, monkeypatch, tmp_path):
        creator = _make_creator(monkeypatch)
        summary = tmp_path / "summary.json"
        summary.write_text(
            json.dumps(
                {"quality_score": 5.0, "security": {}, "high_complexity_functions": []}
            )
        )
        issues = creator.check_quality_metrics(summary)
        assert any(
            "quality" in i["title"].lower() or "Quality" in i["title"] for i in issues
        )

    def test_high_security_vulnerabilities_creates_issue(self, monkeypatch, tmp_path):
        creator = _make_creator(monkeypatch)
        summary = tmp_path / "summary.json"
        summary.write_text(
            json.dumps(
                {
                    "quality_score": 9.0,
                    "security": {"high": 3, "medium": 0, "low": 0},
                    "high_complexity_functions": [],
                }
            )
        )
        issues = creator.check_quality_metrics(summary)
        assert any("security" in i["labels"] for i in issues)

    def test_high_complexity_functions_creates_issue(self, monkeypatch, tmp_path):
        creator = _make_creator(monkeypatch)
        summary = tmp_path / "summary.json"
        funcs = [{"name": f"func_{i}", "complexity": 15} for i in range(7)]
        summary.write_text(
            json.dumps(
                {
                    "quality_score": 9.0,
                    "security": {},
                    "high_complexity_functions": funcs,
                }
            )
        )
        issues = creator.check_quality_metrics(summary)
        assert any(
            "complexity" in i["labels"] or "Complexity" in i["title"] for i in issues
        )

    def test_good_metrics_no_issues(self, monkeypatch, tmp_path):
        creator = _make_creator(monkeypatch)
        summary = tmp_path / "summary.json"
        summary.write_text(
            json.dumps(
                {
                    "quality_score": 9.0,
                    "security": {"high": 0},
                    "high_complexity_functions": [],
                }
            )
        )
        issues = creator.check_quality_metrics(summary)
        assert issues == []


class TestGenerateQualityIssueBody:
    def test_body_contains_quality_score(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        body = creator._generate_quality_issue_body({"quality_score": 5.5}, 5.5)
        assert "5.5" in body

    def test_body_contains_workflow_url(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        body = creator._generate_quality_issue_body({}, 6.0)
        assert "workflow" in body.lower() or "actions" in body.lower()

    def test_body_with_pylint_issues(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        body = creator._generate_quality_issue_body({"pylint_issues": 42}, 5.0)
        assert "42" in body or "Pylint" in body


class TestGenerateSecurityIssueBody:
    def test_body_contains_severity_table(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        body = creator._generate_security_issue_body({"high": 3, "medium": 1, "low": 5})
        assert "HIGH" in body
        assert "3" in body

    def test_body_is_markdown(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        body = creator._generate_security_issue_body({})
        assert "##" in body


class TestGenerateComplexityIssueBody:
    def test_body_contains_function_names(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        funcs = [{"name": "complex_func", "complexity": 25}]
        body = creator._generate_complexity_issue_body(funcs)
        assert "complex_func" in body

    def test_body_limits_to_10_functions(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        funcs = [{"name": f"func_{i}", "complexity": 20 + i} for i in range(20)]
        body = creator._generate_complexity_issue_body(funcs)
        # Only first 10 should appear
        assert "func_9" in body
        assert "func_15" not in body


class TestMakeRequest:
    def test_successful_request(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 123, "number": 42}
        mock_response.raise_for_status.return_value = None
        with patch("requests.post", return_value=mock_response):
            result = creator._make_request("issues", {"title": "test"})
        assert result is not None
        assert result["id"] == 123

    def test_failed_request_returns_none(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        import requests

        with patch(
            "requests.post",
            side_effect=requests.exceptions.RequestException("Connection error"),
        ):
            result = creator._make_request("issues", {"title": "test"})
        assert result is None


class TestCreateIssuesDedup:
    def test_updates_existing_issue_instead_of_creating(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        mock_get = MagicMock()
        mock_get.json.return_value = [{"number": 7, "title": "old"}]
        mock_get.raise_for_status.return_value = None
        mock_patch = MagicMock()
        mock_patch.json.return_value = {"number": 7}
        mock_patch.raise_for_status.return_value = None

        with (
            patch("requests.get", return_value=mock_get) as get,
            patch("requests.patch", return_value=mock_patch) as patch_call,
            patch("requests.post") as post_call,
        ):
            issue_data = {
                "title": "⚠️ Code Quality Below Threshold",
                "body": "x",
                "labels": ["code-quality", "automated", "urgent"],
            }
            creator.create_issues([issue_data])

        get.assert_called_once()
        patch_call.assert_called_once()
        post_call.assert_not_called()

    def test_creates_new_issue_when_none_exists(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        mock_get = MagicMock()
        mock_get.json.return_value = []
        mock_get.raise_for_status.return_value = None
        mock_post = MagicMock()
        mock_post.json.return_value = {"number": 9}
        mock_post.raise_for_status.return_value = None

        with (
            patch("requests.get", return_value=mock_get),
            patch("requests.post", return_value=mock_post) as post_call,
            patch("requests.patch") as patch_call,
        ):
            issue_data = {
                "title": "🔴 1 High-Severity Security Vulnerabilities Detected",
                "body": "x",
                "labels": ["security", "automated", "critical"],
            }
            creator.create_issues([issue_data])

        post_call.assert_called_once()
        patch_call.assert_not_called()

    def test_find_open_issue_skips_pull_requests(self, monkeypatch):
        creator = _make_creator(monkeypatch)
        mock_get = MagicMock()
        mock_get.json.return_value = [{"number": 1, "pull_request": {}}, {"number": 2}]
        mock_get.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_get):
            result = creator._find_open_issue(["automated"])

        assert result["number"] == 2
