"""Unit tests for agents/orchestrator_agent.py"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def run(coro):
    return asyncio.run(coro)


def _make_orchestrator(config=None):
    from agents.orchestrator_agent import OrchestratorAgent

    cfg = config or {"github_token": "ghp_test", "openai_api_key": "sk-test"}
    with (
        patch("core.agent_base.GitHubClient"),
        patch("core.agent_base.LLMClient"),
        patch("core.agent_base.AuditLogger"),
        patch("core.agent_base.PolicyEngine"),
        patch("core.message_queue.MessageQueue._init_redis", return_value=False),
    ):
        agent = OrchestratorAgent(cfg)
        agent.policy.check_action = AsyncMock(return_value={"requires_approval": False})
        agent.audit.log_action = AsyncMock()
    return agent


def _make_sub_agent(execute_result=None, supported_actions=None):
    """Create a mock sub-agent."""
    from core.agent_base import BaseAgent

    _result = execute_result or {"status": "success", "output": "done"}
    _actions = supported_actions or ["test_action"]

    class SubAgent(BaseAgent):
        def get_supported_actions(self):
            return _actions

        async def _execute(self, task):
            return _result

    with (
        patch("core.agent_base.GitHubClient"),
        patch("core.agent_base.LLMClient"),
        patch("core.agent_base.AuditLogger"),
        patch("core.agent_base.PolicyEngine"),
    ):
        agent = SubAgent("sub-agent", {})
        agent.policy.check_action = AsyncMock(return_value={"requires_approval": False})
        agent.audit.log_action = AsyncMock()
    return agent


class TestOrchestratorInit:
    def test_orchestrator_name_is_orchestrator(self):
        orch = _make_orchestrator()
        assert orch.name == "orchestrator"

    def test_agent_registry_starts_empty(self):
        orch = _make_orchestrator()
        assert orch.agent_registry == {}

    def test_default_routing_strategy(self):
        orch = _make_orchestrator()
        assert orch.routing_strategy == "priority"

    def test_custom_routing_strategy_respected(self):
        orch = _make_orchestrator(
            config={"routing_strategy": "round-robin", "github_token": "x", "openai_api_key": "x"}
        )
        assert orch.routing_strategy == "round-robin"

    def test_supported_actions(self):
        orch = _make_orchestrator()
        actions = orch.get_supported_actions()
        assert "delegate_task" in actions
        assert "route_task" in actions
        assert "execute_parallel" in actions
        assert "execute_sequential" in actions


class TestRegisterAgent:
    def test_register_adds_agent_to_registry(self):
        orch = _make_orchestrator()
        sub = _make_sub_agent()
        orch.register_agent("my-agent", sub)
        assert "my-agent" in orch.agent_registry

    def test_registered_agent_retrievable(self):
        orch = _make_orchestrator()
        sub = _make_sub_agent()
        orch.register_agent("worker", sub)
        assert orch.agent_registry["worker"] is sub


class TestDetermineAgent:
    def test_pr_review_maps_to_pr_review_agent(self):
        orch = _make_orchestrator()
        assert orch._determine_agent("pr_review") == "pr_review_agent"

    def test_issue_triage_maps_to_issue_triager(self):
        orch = _make_orchestrator()
        assert orch._determine_agent("issue_triage") == "issue_triager"

    def test_unknown_task_type_returns_none(self):
        orch = _make_orchestrator()
        assert orch._determine_agent("unknown_task_type") is None


class TestDelegateTask:
    def test_delegate_to_registered_agent(self):
        orch = _make_orchestrator()
        sub = _make_sub_agent(execute_result={"status": "success", "data": "ok"})
        orch.register_agent("pr_review_agent", sub)
        result = run(orch._delegate_task({"task_type": "pr_review", "task_data": {"action": "test_action"}}))
        assert result is not None

    def test_delegate_unknown_task_type_returns_error(self):
        orch = _make_orchestrator()
        result = run(orch._delegate_task({"task_type": "nonexistent_task", "task_data": {}}))
        assert result["status"] == "error"
        assert "No agent" in result["error"]

    def test_delegate_unregistered_agent_returns_error(self):
        orch = _make_orchestrator()
        # "pr_review" maps to "pr_review_agent" but it's not registered
        result = run(orch._delegate_task({"task_type": "pr_review", "task_data": {}}))
        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_delegate_handles_exception_gracefully(self):
        orch = _make_orchestrator()

        class ErrorAgent:
            async def execute(self, task):
                raise RuntimeError("Broken!")

            def get_capabilities(self):
                return {}

        orch.register_agent("pr_review_agent", ErrorAgent())
        result = run(orch._delegate_task({"task_type": "pr_review", "task_data": {}}))
        assert result["status"] == "error"
        assert "Broken!" in result["error"]


class TestRouteTask:
    def test_route_known_task_returns_queued_status(self):
        orch = _make_orchestrator()
        result = run(orch._route_task({"task_type": "pr_review", "priority": 5}))
        assert result["status"] == "queued"
        assert result["agent"] == "pr_review_agent"
        assert result["priority"] == 5

    def test_route_unknown_task_returns_error(self):
        orch = _make_orchestrator()
        result = run(orch._route_task({"task_type": "unknown_task"}))
        assert result["status"] == "error"


class TestExecuteParallel:
    def test_empty_tasks_returns_error(self):
        orch = _make_orchestrator()
        result = run(orch._execute_parallel({"tasks": []}))
        assert result["status"] == "error"

    def test_parallel_execution_returns_results(self):
        orch = _make_orchestrator()
        sub = _make_sub_agent()
        orch.register_agent("pr_review_agent", sub)
        tasks = [
            {"type": "pr_review", "data": {"action": "test_action"}},
        ]
        result = run(orch._execute_parallel({"tasks": tasks}))
        assert result["status"] == "completed"
        assert result["total_tasks"] == 1
        assert len(result["results"]) == 1

    def test_parallel_batching_respects_max(self):
        orch = _make_orchestrator()
        orch.max_parallel_tasks = 2
        sub = _make_sub_agent()
        orch.register_agent("pr_review_agent", sub)
        tasks = [{"type": "pr_review", "data": {"action": "test_action"}} for _ in range(5)]
        result = run(orch._execute_parallel({"tasks": tasks}))
        assert result["total_tasks"] == 5


class TestExecuteSequential:
    def test_empty_tasks_returns_error(self):
        orch = _make_orchestrator()
        result = run(orch._execute_sequential({"tasks": []}))
        assert result["status"] == "error"

    def test_sequential_executes_all_tasks(self):
        orch = _make_orchestrator()
        sub = _make_sub_agent()
        orch.register_agent("pr_review_agent", sub)
        tasks = [
            {"type": "pr_review", "data": {"action": "test_action"}},
            {"type": "pr_review", "data": {"action": "test_action"}},
        ]
        result = run(orch._execute_sequential({"tasks": tasks}))
        assert result["total_tasks"] == 2
        assert result["completed"] == 2

    def test_stop_on_error_halts_execution(self):
        orch = _make_orchestrator()
        # No agent registered for "unknown_task" → error
        tasks = [
            {"type": "unknown_task", "data": {}},
            {"type": "pr_review", "data": {"action": "test_action"}},
        ]
        result = run(
            orch._execute_sequential({"tasks": tasks, "stop_on_error": True})
        )
        # Should stop after first error
        assert result["completed"] == 1


class TestGetAgentStatus:
    def test_no_agents_registered(self):
        orch = _make_orchestrator()
        result = run(orch._get_agent_status({}))
        assert result["status"] == "success"
        assert result["total_agents"] == 0
        assert result["agents"] == {}

    def test_registered_agent_shows_as_available(self):
        orch = _make_orchestrator()
        sub = _make_sub_agent(supported_actions=["test_action"])
        orch.register_agent("sub", sub)
        result = run(orch._get_agent_status({}))
        assert result["agents"]["sub"]["available"] is True

    def test_broken_agent_shows_as_unavailable(self):
        orch = _make_orchestrator()

        class BrokenCaps:
            def get_capabilities(self):
                raise RuntimeError("no caps")

        orch.register_agent("broken", BrokenCaps())
        result = run(orch._get_agent_status({}))
        assert result["agents"]["broken"]["available"] is False


class TestCreateApprovalIssue:
    def test_missing_repo_info_returns_error(self):
        orch = _make_orchestrator()
        result = run(orch._create_approval_issue({"action": "deploy", "agent": "deployer"}))
        assert result["status"] == "error"
        assert "Repository" in result["error"] or "repository" in result["error"].lower()

    def test_creates_issue_when_repo_info_provided(self):
        orch = _make_orchestrator()
        mock_issue = MagicMock()
        mock_issue.number = 99
        mock_issue.html_url = "https://github.com/owner/repo/issues/99"
        orch.github.create_issue = MagicMock(return_value=mock_issue)
        result = run(
            orch._create_approval_issue(
                {
                    "action": "deploy",
                    "agent": "deployer",
                    "task_data": {"repo_owner": "owner", "repo_name": "repo"},
                }
            )
        )
        assert result["status"] == "success"
        assert result["issue_number"] == 99

    def test_github_exception_returns_error(self):
        orch = _make_orchestrator()
        orch.github.create_issue = MagicMock(side_effect=Exception("GitHub down"))
        result = run(
            orch._create_approval_issue(
                {
                    "action": "deploy",
                    "agent": "deployer",
                    "task_data": {"repo_owner": "owner", "repo_name": "repo"},
                }
            )
        )
        assert result["status"] == "error"
