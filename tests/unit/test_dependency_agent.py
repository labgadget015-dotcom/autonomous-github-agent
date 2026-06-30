"""Unit tests for agents/dependency_agent.py"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


def run(coro):
    return asyncio.run(coro)


def _make_agent(config=None):
    from agents.dependency_agent import DependencyAgent

    with (
        patch("core.agent_base.GitHubClient"),
        patch("core.agent_base.LLMClient"),
        patch("core.agent_base.AuditLogger"),
        patch("core.agent_base.PolicyEngine"),
    ):
        agent = DependencyAgent(config or {"github_token": "x"})
        agent.policy.check_action = AsyncMock(return_value={"requires_approval": False})
        agent.audit.log_action = AsyncMock()
    return agent


class TestDependencyAgentInit:
    def test_name(self):
        assert _make_agent().name == "dependency_agent"

    def test_supported_actions(self):
        assert _make_agent().get_supported_actions() == ["check_dependencies"]


class TestCheckUnpinned:
    def setup_method(self):
        self.agent = _make_agent()

    def test_returns_empty_for_missing_file(self, tmp_path):
        result = self.agent._check_unpinned(tmp_path / "nonexistent.txt")
        assert result == []

    def test_exact_pin_not_flagged(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests==2.28.0\n")
        assert self.agent._check_unpinned(req) == []

    def test_lower_bound_only_flagged(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests>=2.0\n")
        result = self.agent._check_unpinned(req)
        assert "requests>=2.0" in result

    def test_tilde_pin_not_flagged(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests~=2.28\n")
        assert self.agent._check_unpinned(req) == []

    def test_bare_package_flagged(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests\n")
        result = self.agent._check_unpinned(req)
        assert "requests" in result

    def test_comment_lines_skipped(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("# this is a comment\nrequests==2.28.0\n")
        assert self.agent._check_unpinned(req) == []

    def test_blank_lines_skipped(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("\n\nrequests==2.28.0\n\n")
        assert self.agent._check_unpinned(req) == []

    def test_upper_bound_with_lower_not_flagged(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests>=2.0,<3.0\n")
        assert self.agent._check_unpinned(req) == []


class TestBuildReport:
    def setup_method(self):
        self.agent = _make_agent()

    def test_report_with_no_issues(self):
        report = self.agent._build_report([], [])
        assert "Dependency Audit Report" in report
        assert "0 package(s) affected" in report
        assert "0 found" in report

    def test_report_with_vulnerability(self):
        audit_data = [{"name": "flask", "version": "1.0", "vulns": [
            {"id": "CVE-2021-1234", "aliases": ["GHSA-abc"], "fix_versions": ["2.0"]}
        ]}]
        report = self.agent._build_report(audit_data, [])
        assert "flask" in report
        assert "CVE-2021-1234" in report
        assert "2.0" in report

    def test_report_with_unpinned(self):
        report = self.agent._build_report([], ["requests", "flask>=1.0"])
        assert "requests" in report
        assert "flask>=1.0" in report

    def test_vuln_with_no_fix(self):
        audit_data = [{"name": "pkg", "version": "0.1", "vulns": [
            {"id": "CVE-x", "aliases": [], "fix_versions": []}
        ]}]
        report = self.agent._build_report(audit_data, [])
        assert "none" in report

    def test_non_vulnerable_pkg_not_in_table(self):
        audit_data = [{"name": "safe-pkg", "version": "1.0", "vulns": []}]
        report = self.agent._build_report(audit_data, [])
        assert "safe-pkg" not in report


class TestRunPipAudit:
    def setup_method(self):
        self.agent = _make_agent()

    def test_returns_empty_on_bad_json(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="not-json")
            result = self.agent._run_pip_audit()
        assert result == []

    def test_returns_list_result(self):
        data = [{"name": "flask", "version": "1.0", "vulns": []}]
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=json.dumps(data))
            result = self.agent._run_pip_audit()
        assert result == data

    def test_returns_dependencies_key_if_dict(self):
        deps = [{"name": "x", "version": "1", "vulns": []}]
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=json.dumps({"dependencies": deps}))
            result = self.agent._run_pip_audit()
        assert result == deps


class TestCheckDependencies:
    def setup_method(self):
        self.agent = _make_agent()

    def test_creates_issue_when_none_exists(self, tmp_path, monkeypatch):
        import agents.dependency_agent as mod
        monkeypatch.setattr(mod, "project_root", tmp_path)
        (tmp_path / "requirements.txt").write_text("requests==2.28.0\n")

        mock_issue = MagicMock()
        mock_issue.number = 42
        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = []
        mock_repo.create_issue.return_value = mock_issue
        self.agent.github.client.get_repo.return_value = mock_repo

        with patch.object(self.agent, "_run_pip_audit", return_value=[]):
            result = run(self.agent._check_dependencies({"repo": "o/r"}))
        assert result["created_issue"] == 42

    def test_updates_existing_issue(self, tmp_path, monkeypatch):
        import agents.dependency_agent as mod
        monkeypatch.setattr(mod, "project_root", tmp_path)
        (tmp_path / "requirements.txt").write_text("requests==2.28.0\n")

        existing = MagicMock()
        existing.number = 10
        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = [existing]
        self.agent.github.client.get_repo.return_value = mock_repo

        with patch.object(self.agent, "_run_pip_audit", return_value=[]):
            result = run(self.agent._check_dependencies({"repo": "o/r"}))
        assert result["updated_issue"] == 10
        existing.create_comment.assert_called_once()


class TestExecuteDispatch:
    def setup_method(self):
        self.agent = _make_agent()

    def test_unsupported_action_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Unsupported action"):
            run(self.agent._execute({"action": "fly"}))

    def test_check_dependencies_dispatches(self):
        self.agent._check_dependencies = AsyncMock(return_value={"created_issue": 1})
        result = run(self.agent._execute({"action": "check_dependencies", "params": {"repo": "o/r"}}))
        self.agent._check_dependencies.assert_called_once()
        assert result["created_issue"] == 1
