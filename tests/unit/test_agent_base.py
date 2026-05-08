"""Unit tests for core/agent_base.py"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch


def run(coro):
    return asyncio.run(coro)


def _make_agent(config=None, supported_actions=None, execute_result=None):
    """Create a concrete BaseAgent subclass for testing."""
    from core.agent_base import BaseAgent

    _supported = supported_actions or ["do_work", "noop"]
    _result = execute_result or {"output": "done"}

    class TestAgent(BaseAgent):
        def get_supported_actions(self):
            return _supported

        async def _execute(self, task):
            return _result

    with (
        patch("core.agent_base.GitHubClient"),
        patch("core.agent_base.LLMClient"),
        patch("core.agent_base.AuditLogger"),
        patch("core.agent_base.PolicyEngine"),
    ):
        agent = TestAgent("test-agent", config or {"github_token": "x"})
        agent.policy.check_action = AsyncMock(return_value={"requires_approval": False})
        agent.audit.log_action = AsyncMock()
    return agent


class TestAgentInit:
    def test_agent_name_stored(self):
        agent = _make_agent()
        assert agent.name == "test-agent"

    def test_initialized_flag_set(self):
        agent = _make_agent()
        assert agent._initialized is True

    def test_get_capabilities(self):
        agent = _make_agent(supported_actions=["alpha", "beta"])
        caps = agent.get_capabilities()
        assert caps["name"] == "test-agent"
        assert caps["actions"] == ["alpha", "beta"]
        assert caps["version"] == "1.0.0"


class TestValidate:
    def test_valid_task_returns_true(self):
        agent = _make_agent()
        assert agent.validate({"action": "do_work"}) is True

    def test_missing_action_returns_false(self):
        agent = _make_agent()
        assert agent.validate({"params": {}}) is False

    def test_empty_string_action_returns_false(self):
        agent = _make_agent()
        assert agent.validate({"action": ""}) is False

    def test_whitespace_action_returns_false(self):
        agent = _make_agent()
        assert agent.validate({"action": "   "}) is False

    def test_unsupported_action_returns_false(self):
        agent = _make_agent(supported_actions=["do_work"])
        assert agent.validate({"action": "unknown_action"}) is False

    def test_supported_action_returns_true(self):
        agent = _make_agent(supported_actions=["do_work"])
        assert agent.validate({"action": "do_work"}) is True

    def test_non_string_action_returns_false(self):
        agent = _make_agent()
        assert agent.validate({"action": 42}) is False

    def test_empty_supported_actions_allows_any(self):
        """When get_supported_actions() returns empty list, any action is valid."""
        from core.agent_base import BaseAgent

        class EmptyActionsAgent(BaseAgent):
            def get_supported_actions(self):
                return []  # empty → no restriction

            async def _execute(self, task):
                return {}

        with (
            patch("core.agent_base.GitHubClient"),
            patch("core.agent_base.LLMClient"),
            patch("core.agent_base.AuditLogger"),
            patch("core.agent_base.PolicyEngine"),
        ):
            agent = EmptyActionsAgent("empty", {})
        assert agent.validate({"action": "anything"}) is True


class TestExecuteLifecycle:
    def test_successful_execution_returns_success_status(self):
        agent = _make_agent()
        result = run(agent.execute({"action": "do_work", "params": {}}))
        assert result["status"] == "success"
        assert result["agent"] == "test-agent"
        assert "task_id" in result

    def test_successful_execution_calls_audit_log(self):
        agent = _make_agent()
        run(agent.execute({"action": "do_work", "params": {}}))
        agent.audit.log_action.assert_called_once()

    def test_task_id_used_from_task_dict(self):
        agent = _make_agent()
        result = run(
            agent.execute({"action": "do_work", "id": "my-task-123", "params": {}})
        )
        assert result["task_id"] == "my-task-123"

    def test_validation_failure_returns_error(self):
        agent = _make_agent()
        result = run(agent.execute({"params": {}}))  # no 'action'
        assert result["status"] == "error"
        assert "validation" in result["error"].lower()

    def test_policy_approval_required_returns_pending(self):
        agent = _make_agent()
        agent.policy.check_action = AsyncMock(
            return_value={
                "requires_approval": True,
                "reason": "Dangerous action",
            }
        )
        result = run(agent.execute({"action": "do_work", "params": {}}))
        assert result["status"] == "pending_approval"
        assert "approval_reason" in result

    def test_exception_in_execute_returns_error(self):
        from core.agent_base import BaseAgent

        class BrokenAgent(BaseAgent):
            def get_supported_actions(self):
                return ["do_work"]

            async def _execute(self, task):
                raise RuntimeError("Something went wrong")

        with (
            patch("core.agent_base.GitHubClient"),
            patch("core.agent_base.LLMClient"),
            patch("core.agent_base.AuditLogger"),
            patch("core.agent_base.PolicyEngine"),
        ):
            agent = BrokenAgent("broken", {})
            agent.policy.check_action = AsyncMock(
                return_value={"requires_approval": False}
            )
            agent.audit.log_action = AsyncMock()

        result = run(agent.execute({"action": "do_work"}))
        assert result["status"] == "error"
        assert "Something went wrong" in result["error"]

    def test_exception_in_execute_logs_error(self):
        from core.agent_base import BaseAgent

        class BrokenAgent(BaseAgent):
            def get_supported_actions(self):
                return ["do_work"]

            async def _execute(self, task):
                raise ValueError("bad input")

        with (
            patch("core.agent_base.GitHubClient"),
            patch("core.agent_base.LLMClient"),
            patch("core.agent_base.AuditLogger"),
            patch("core.agent_base.PolicyEngine"),
        ):
            agent = BrokenAgent("broken2", {})
            agent.policy.check_action = AsyncMock(
                return_value={"requires_approval": False}
            )
            agent.audit.log_action = AsyncMock()

        run(agent.execute({"action": "do_work"}))
        # Audit should still be called on error
        agent.audit.log_action.assert_called_once()

    def test_result_contains_execute_output(self):
        agent = _make_agent(execute_result={"computed": 42})
        result = run(agent.execute({"action": "do_work"}))
        assert result["result"]["computed"] == 42
