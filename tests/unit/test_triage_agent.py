"""Unit tests for agents/triage_agent.py"""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


def run(coro):
    return asyncio.run(coro)


def _make_agent(config=None):
    from agents.triage_agent import TriageAgent

    with (
        patch("core.agent_base.GitHubClient"),
        patch("core.agent_base.LLMClient"),
        patch("core.agent_base.AuditLogger"),
        patch("core.agent_base.PolicyEngine"),
    ):
        agent = TriageAgent(config or {"github_token": "x"})
        agent.policy.check_action = AsyncMock(return_value={"requires_approval": False})
        agent.audit.log_action = AsyncMock()
    return agent


class TestTriageAgentInit:
    def test_name(self):
        agent = _make_agent()
        assert agent.name == "triage_agent"

    def test_supported_actions(self):
        agent = _make_agent()
        assert set(agent.get_supported_actions()) == {"triage_issue", "cost_report"}


class TestKeywordPriority:
    def setup_method(self):
        self.agent = _make_agent()

    def test_p0_critical(self):
        assert self.agent._keyword_priority("critical bug") == "P0"

    def test_p0_crash(self):
        assert self.agent._keyword_priority("app crash on startup") == "P0"

    def test_p0_data_loss(self):
        assert self.agent._keyword_priority("data loss possible") == "P0"

    def test_p0_security(self):
        assert self.agent._keyword_priority("security vulnerability") == "P0"

    def test_p0_outage(self):
        assert self.agent._keyword_priority("service outage") == "P0"

    def test_p0_urgent(self):
        assert self.agent._keyword_priority("urgent fix needed") == "P0"

    def test_p0_blocker(self):
        assert self.agent._keyword_priority("this is a blocker") == "P0"

    def test_p1_regression(self):
        assert self.agent._keyword_priority("regression in payment flow") == "P1"

    def test_p1_broken(self):
        assert self.agent._keyword_priority("button is broken") == "P1"

    def test_p1_failing(self):
        assert self.agent._keyword_priority("CI is failing") == "P1"

    def test_p1_high_priority(self):
        assert self.agent._keyword_priority("high priority request") == "P1"

    def test_no_match_returns_none(self):
        assert self.agent._keyword_priority("add dark mode support") is None

    def test_case_insensitive(self):
        assert self.agent._keyword_priority("CRITICAL failure") == "P0"


class TestLoadCosts:
    def setup_method(self):
        self.agent = _make_agent()

    def test_returns_empty_when_file_missing(self, tmp_path, monkeypatch):
        import agents.triage_agent as mod
        monkeypatch.setattr(mod, "project_root", tmp_path)
        result = self.agent._load_costs(30)
        assert result == []

    def test_returns_records_within_window(self, tmp_path, monkeypatch):
        import agents.triage_agent as mod
        from datetime import datetime, timedelta

        monkeypatch.setattr(mod, "project_root", tmp_path)
        costs_path = tmp_path / ".llm_costs.jsonl"
        recent = (datetime.now() - timedelta(days=1)).isoformat()
        old = (datetime.now() - timedelta(days=60)).isoformat()
        costs_path.write_text(
            json.dumps({"timestamp": recent, "cost_usd": 0.5, "model": "claude"}) + "\n"
            + json.dumps({"timestamp": old, "cost_usd": 1.0, "model": "gpt4"}) + "\n"
        )
        result = self.agent._load_costs(30)
        assert len(result) == 1
        assert result[0]["cost_usd"] == 0.5

    def test_skips_blank_lines(self, tmp_path, monkeypatch):
        import agents.triage_agent as mod

        monkeypatch.setattr(mod, "project_root", tmp_path)
        (tmp_path / ".llm_costs.jsonl").write_text("\n\n\n")
        assert self.agent._load_costs(30) == []

    def test_skips_invalid_json(self, tmp_path, monkeypatch):
        import agents.triage_agent as mod

        monkeypatch.setattr(mod, "project_root", tmp_path)
        (tmp_path / ".llm_costs.jsonl").write_text("not-json\n")
        assert self.agent._load_costs(30) == []

    def test_skips_missing_timestamp_key(self, tmp_path, monkeypatch):
        import agents.triage_agent as mod

        monkeypatch.setattr(mod, "project_root", tmp_path)
        (tmp_path / ".llm_costs.jsonl").write_text(json.dumps({"cost_usd": 0.1}) + "\n")
        assert self.agent._load_costs(30) == []


class TestCostReport:
    def setup_method(self):
        self.agent = _make_agent()

    def test_no_slack_url_prints_and_returns(self, tmp_path, monkeypatch, capsys):
        import agents.triage_agent as mod
        from datetime import datetime, timedelta

        monkeypatch.setattr(mod, "project_root", tmp_path)
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

        recent = (datetime.now() - timedelta(days=1)).isoformat()
        (tmp_path / ".llm_costs.jsonl").write_text(
            json.dumps({"timestamp": recent, "cost_usd": 0.25, "input_tokens": 100,
                        "output_tokens": 50, "model": "claude"}) + "\n"
        )
        result = run(self.agent._cost_report({}))
        assert result["total_cost_usd"] == 0.25
        assert result["records"] == 1
        assert result["slack_status"] == 0
        captured = capsys.readouterr()
        assert "LLM Cost Report" in captured.out

    def test_empty_costs_returns_zero(self, tmp_path, monkeypatch):
        import agents.triage_agent as mod

        monkeypatch.setattr(mod, "project_root", tmp_path)
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
        result = run(self.agent._cost_report({}))
        assert result["total_cost_usd"] == 0.0
        assert result["records"] == 0

    def test_multiple_models_aggregated(self, tmp_path, monkeypatch):
        import agents.triage_agent as mod
        from datetime import datetime, timedelta

        monkeypatch.setattr(mod, "project_root", tmp_path)
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

        recent = (datetime.now() - timedelta(hours=1)).isoformat()
        lines = "\n".join([
            json.dumps({"timestamp": recent, "cost_usd": 0.10, "input_tokens": 10,
                        "output_tokens": 5, "model": "claude"}),
            json.dumps({"timestamp": recent, "cost_usd": 0.20, "input_tokens": 20,
                        "output_tokens": 10, "model": "gpt4"}),
        ])
        (tmp_path / ".llm_costs.jsonl").write_text(lines)
        result = run(self.agent._cost_report({}))
        assert abs(result["total_cost_usd"] - 0.30) < 0.001
        assert result["records"] == 2


class TestExecuteDispatch:
    def setup_method(self):
        self.agent = _make_agent()

    def test_unsupported_action_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Unsupported action"):
            run(self.agent._execute({"action": "unknown"}))

    def test_triage_issue_dispatches(self):
        self.agent._triage_issue = AsyncMock(return_value={"issue": 1})
        result = run(self.agent._execute({"action": "triage_issue", "params": {"repo": "o/r", "issue_number": 1}}))
        self.agent._triage_issue.assert_called_once()
        assert result == {"issue": 1}

    def test_cost_report_dispatches(self):
        self.agent._cost_report = AsyncMock(return_value={"records": 0})
        result = run(self.agent._execute({"action": "cost_report", "params": {}}))
        self.agent._cost_report.assert_called_once()
        assert result == {"records": 0}
