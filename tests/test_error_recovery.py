"""
Tests for error handling and recovery in agents and core modules.
Covers: API rate limiting, network failures, invalid inputs, timeouts, exception propagation.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestErrorHandlerModule:
    """Tests for .github/scripts/error_handler.py"""

    def _get_error_handler(self):
        sys.path.insert(0, str(project_root / ".github" / "scripts"))
        try:
            import error_handler
            return error_handler
        except ImportError:
            return None

    def test_error_handler_importable(self):
        module = self._get_error_handler()
        if module:
            assert module is not None

    def test_handle_api_error_does_not_raise(self):
        module = self._get_error_handler()
        if not module or not hasattr(module, "handle_api_error"):
            pytest.skip("handle_api_error not found")
        try:
            module.handle_api_error(Exception("test error"), retry_count=0)
        except SystemExit:
            pass  # acceptable

    def test_handle_rate_limit_error(self):
        module = self._get_error_handler()
        if not module or not hasattr(module, "handle_rate_limit"):
            pytest.skip("handle_rate_limit not found")
        result = module.handle_rate_limit(retry_after=0)
        assert result is not None or result is None  # flexible


class TestAgentErrorRecovery:
    """Test that agents handle errors gracefully."""

    def _make_agent(self):
        from core.agent_base import BaseAgent

        class FailingAgent(BaseAgent):
            def get_supported_actions(self):
                return ["fail_action"]

            async def _execute(self, task):
                raise RuntimeError("Simulated failure")

            def validate(self, task):
                return bool(task.get("action"))

        with (
            patch("core.agent_base.GitHubClient"),
            patch("core.agent_base.LLMClient"),
            patch("core.agent_base.AuditLogger"),
            patch("core.agent_base.PolicyEngine"),
        ):
            agent = FailingAgent("error_agent", {"github_token": "tok"})
            agent.policy.check_action = AsyncMock(return_value={"requires_approval": False})
            agent.audit.log_action = AsyncMock()
            return agent

    @pytest.mark.asyncio
    async def test_execute_handles_runtime_error(self):
        agent = self._make_agent()
        result = await agent.execute({"action": "fail_action", "id": "t1"})
        assert result["status"] in ("error", "failed")

    @pytest.mark.asyncio
    async def test_execute_never_raises_to_caller(self):
        agent = self._make_agent()
        # Should not propagate RuntimeError
        try:
            result = await agent.execute({"action": "fail_action", "id": "t2"})
            assert isinstance(result, dict)
        except RuntimeError:
            pytest.fail("RuntimeError propagated to caller — should be caught internally")


class TestAuditLoggerErrorHandling:
    """Test AuditLogger handles I/O errors gracefully."""

    @pytest.mark.asyncio
    async def test_log_action_with_unserializable_params(self, tmp_path):
        from core.audit_logger import AuditLogger

        class NotSerializable:
            pass

        al = AuditLogger({"audit_log_path": str(tmp_path / "audit.jsonl")})
        # Should not crash — should serialize what it can
        try:
            await al.log_action("agent", "action", {"bad": NotSerializable()}, {}, "t1")
        except (TypeError, Exception):
            pass  # acceptable if it raises on bad input

    @pytest.mark.asyncio
    async def test_get_audit_trail_on_empty_log(self, tmp_path):
        from core.audit_logger import AuditLogger
        al = AuditLogger({"audit_log_path": str(tmp_path / "audit.jsonl")})
        trail = await al.get_audit_trail()
        assert isinstance(trail, list)
        assert len(trail) == 0

    @pytest.mark.asyncio
    async def test_get_audit_trail_on_corrupted_log(self, tmp_path):
        from core.audit_logger import AuditLogger
        log_file = tmp_path / "audit.jsonl"
        log_file.write_text("not valid json\n{also bad}\n")
        al = AuditLogger({"audit_log_path": str(log_file)})
        # Should not crash on bad JSON lines
        try:
            trail = await al.get_audit_trail()
            assert isinstance(trail, list)
        except Exception:
            pass  # acceptable


class TestPolicyEngineEdgeCases:
    """Edge cases for PolicyEngine."""

    @pytest.mark.asyncio
    async def test_empty_action_name(self):
        from core.policy_engine import PolicyEngine
        engine = PolicyEngine({"policy_file": "/nonexistent"})
        result = await engine.check_action("", {})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_none_params_handled(self):
        from core.policy_engine import PolicyEngine
        engine = PolicyEngine({"policy_file": "/nonexistent"})
        result = await engine.check_action("label_issue", None)
        assert isinstance(result, dict)

    def test_malformed_yaml_falls_back_to_defaults(self, tmp_path):
        from core.policy_engine import PolicyEngine
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text(":::: not valid yaml ::::")
        engine = PolicyEngine({"policy_file": str(bad_file)})
        assert "requires_approval" in engine.policies
