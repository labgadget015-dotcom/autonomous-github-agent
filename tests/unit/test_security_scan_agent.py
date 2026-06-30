"""Unit tests for agents/security_scan_agent.py"""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch


def run(coro):
    return asyncio.run(coro)


def _make_agent(config=None):
    from agents.security_scan_agent import SecurityScanAgent

    with (
        patch("core.agent_base.GitHubClient"),
        patch("core.agent_base.LLMClient"),
        patch("core.agent_base.AuditLogger"),
        patch("core.agent_base.PolicyEngine"),
    ):
        agent = SecurityScanAgent(config or {"github_token": "x"})
        agent.policy.check_action = AsyncMock(return_value={"requires_approval": False})
        agent.audit.log_action = AsyncMock()
    return agent


class TestSecurityScanAgentInit:
    def test_name(self):
        assert _make_agent().name == "security_scan_agent"

    def test_supported_actions(self):
        assert _make_agent().get_supported_actions() == ["scan_repo"]


class TestRunBandit:
    def setup_method(self):
        self.agent = _make_agent()

    def test_returns_empty_dict_when_file_missing(self):
        with patch("subprocess.run"), patch("builtins.open", side_effect=FileNotFoundError):
            result = self.agent._run_bandit()
        assert result == {}

    def test_returns_empty_dict_on_bad_json(self, tmp_path):
        bandit_out = tmp_path / "bandit.json"
        bandit_out.write_text("not-json")
        with patch("subprocess.run"), patch("builtins.open", mock_open(read_data="not-json")):
            result = self.agent._run_bandit()
        assert result == {}

    def test_returns_parsed_json(self):
        bandit_data = {"results": [], "metrics": {}}
        with (
            patch("subprocess.run"),
            patch("builtins.open", mock_open(read_data=json.dumps(bandit_data))),
        ):
            result = self.agent._run_bandit()
        assert result == bandit_data


class TestRunPipAudit:
    def setup_method(self):
        self.agent = _make_agent()

    def test_returns_empty_on_missing_file(self):
        with patch("subprocess.run"), patch("builtins.open", side_effect=FileNotFoundError):
            result = self.agent._run_pip_audit()
        assert result == []

    def test_returns_list_result(self):
        data = [{"name": "flask", "version": "1.0", "vulns": []}]
        with (
            patch("subprocess.run"),
            patch("builtins.open", mock_open(read_data=json.dumps(data))),
        ):
            result = self.agent._run_pip_audit()
        assert result == data

    def test_returns_dependencies_key_if_dict(self):
        deps = [{"name": "x", "version": "1", "vulns": []}]
        payload = {"dependencies": deps}
        with (
            patch("subprocess.run"),
            patch("builtins.open", mock_open(read_data=json.dumps(payload))),
        ):
            result = self.agent._run_pip_audit()
        assert result == deps

    def test_returns_empty_on_bad_json(self):
        with (
            patch("subprocess.run"),
            patch("builtins.open", mock_open(read_data="bad")),
        ):
            result = self.agent._run_pip_audit()
        assert result == []


class TestFormatSummary:
    def setup_method(self):
        self.agent = _make_agent()

    def test_empty_inputs_shows_zero_counts(self):
        report = self.agent._format_summary({}, [])
        assert "Security Scan Report" in report
        assert "0 issue(s)" in report
        assert "0 vulnerable package(s)" in report

    def test_bandit_results_included(self):
        bandit_data = {
            "results": [
                {
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "Use of assert",
                    "filename": "core/x.py",
                    "line_number": 10,
                }
            ],
            "metrics": {},
        }
        report = self.agent._format_summary(bandit_data, [])
        assert "HIGH" in report
        assert "core/x.py" in report
        assert "Use of assert" in report

    def test_bandit_metrics_used_for_count(self):
        bandit_data = {
            "results": [],
            "metrics": {"_totals": {"SEVERITY.HIGH": 2, "SEVERITY.MEDIUM": 1, "SEVERITY.LOW": 0}},
        }
        report = self.agent._format_summary(bandit_data, [])
        assert "3 issue(s)" in report

    def test_pip_audit_vulns_included(self):
        pip_data = [
            {
                "name": "flask",
                "version": "0.12",
                "vulns": [{"id": "CVE-2021-99", "fix_versions": ["2.0"]}],
            }
        ]
        report = self.agent._format_summary({}, pip_data)
        assert "flask==0.12" in report
        assert "CVE-2021-99" in report
        assert "2.0" in report

    def test_vuln_with_no_fix_shows_none(self):
        pip_data = [
            {"name": "bad", "version": "1.0", "vulns": [{"id": "CVE-x", "fix_versions": []}]}
        ]
        report = self.agent._format_summary({}, pip_data)
        assert "none" in report

    def test_non_vulnerable_pkg_not_in_report(self):
        pip_data = [{"name": "safe", "version": "1.0", "vulns": []}]
        report = self.agent._format_summary({}, pip_data)
        assert "safe==" not in report

    def test_bandit_truncates_at_20_results(self):
        results = [
            {
                "issue_severity": "LOW",
                "issue_confidence": "LOW",
                "issue_text": f"issue {i}",
                "filename": "f.py",
                "line_number": i,
            }
            for i in range(25)
        ]
        report = self.agent._format_summary({"results": results, "metrics": {}}, [])
        assert "issue 19" in report
        assert "issue 20" not in report


class TestScanRepo:
    def setup_method(self):
        self.agent = _make_agent()

    def test_creates_issue_when_no_issue_number(self):
        mock_issue = MagicMock()
        mock_issue.number = 55
        mock_repo = MagicMock()
        mock_repo.create_issue.return_value = mock_issue
        self.agent.github.client.get_repo.return_value = mock_repo

        with (
            patch.object(self.agent, "_run_bandit", return_value={}),
            patch.object(self.agent, "_run_pip_audit", return_value=[]),
        ):
            result = run(self.agent._scan_repo({"repo": "o/r", "issue_number": 0}))
        assert result["created_issue"] == 55

    def test_comments_on_existing_issue(self):
        mock_issue = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        self.agent.github.client.get_repo.return_value = mock_repo

        with (
            patch.object(self.agent, "_run_bandit", return_value={}),
            patch.object(self.agent, "_run_pip_audit", return_value=[]),
        ):
            result = run(self.agent._scan_repo({"repo": "o/r", "issue_number": 7}))
        mock_issue.create_comment.assert_called_once()
        assert result["posted_to_issue"] == 7


class TestExecuteDispatch:
    def setup_method(self):
        self.agent = _make_agent()

    def test_unsupported_action_raises(self):
        import pytest

        with pytest.raises(ValueError, match="Unsupported action"):
            run(self.agent._execute({"action": "hack"}))

    def test_scan_repo_dispatches(self):
        self.agent._scan_repo = AsyncMock(return_value={"created_issue": 1})
        result = run(self.agent._execute({"action": "scan_repo", "params": {"repo": "o/r"}}))
        self.agent._scan_repo.assert_called_once()
        assert result["created_issue"] == 1
