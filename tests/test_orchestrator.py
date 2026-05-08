"""
Tests for Orchestrator Agent.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.orchestrator_agent import OrchestratorAgent
from core.agent_base import BaseAgent


@pytest.fixture
def orchestrator_config():
    """Configuration for orchestrator"""
    return {
        "github_token": "test_token",
        "openai_api_key": "test_key",
        "llm_provider": "openai",
        "routing_strategy": "priority",
        "max_parallel_tasks": 3,
        "default_repo_owner": "test_owner",
        "default_repo_name": "test_repo",
    }


@pytest.fixture
def mock_agent():
    """Mock agent for testing"""

    class MockAgent(BaseAgent):
        def get_supported_actions(self):
            return ["test_action"]

        async def _execute(self, task):
            return {"result": "success", "data": task.get("params", {})}

    return MockAgent


class TestOrchestratorAgent:
    """Test OrchestratorAgent class"""

    def test_initialization(self, orchestrator_config):
        """Test orchestrator initialization"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        assert orchestrator.name == "orchestrator"
        assert orchestrator.routing_strategy == "priority"
        assert orchestrator.max_parallel_tasks == 3
        assert len(orchestrator.agent_registry) == 0

    def test_register_agent(self, orchestrator_config, mock_agent):
        """Test agent registration"""
        orchestrator = OrchestratorAgent(orchestrator_config)
        agent = mock_agent("test_agent", orchestrator_config)

        orchestrator.register_agent("test_agent", agent)

        assert "test_agent" in orchestrator.agent_registry
        assert orchestrator.agent_registry["test_agent"] == agent

    def test_determine_agent(self, orchestrator_config):
        """Test agent determination for task types"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        # Test known task types
        assert orchestrator._determine_agent("pr_review") == "pr_review_agent"
        assert orchestrator._determine_agent("issue_triage") == "issue_triager"
        assert orchestrator._determine_agent("security_scan") == "security_scanner"

        # Test unknown task type
        assert orchestrator._determine_agent("unknown_task") is None

    @pytest.mark.asyncio
    async def test_delegate_task_success(self, orchestrator_config, mock_agent):
        """Test successful task delegation"""
        orchestrator = OrchestratorAgent(orchestrator_config)
        agent = mock_agent("test_agent", orchestrator_config)

        # Override _determine_agent to return our mock agent
        with patch.object(orchestrator, "_determine_agent", return_value="test_agent"):
            orchestrator.register_agent("test_agent", agent)

            result = await orchestrator._delegate_task(
                {
                    "task_type": "test_task",
                    "task_data": {"action": "test_action", "params": {"key": "value"}},
                }
            )

        assert result["status"] == "success"
        assert "result" in result

    @pytest.mark.asyncio
    async def test_delegate_task_no_agent(self, orchestrator_config):
        """Test delegation when no agent is available"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        result = await orchestrator._delegate_task(
            {"task_type": "unknown_task", "task_data": {}}
        )

        assert result["status"] == "error"
        assert "no agent" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_delegate_task_with_approval(self, orchestrator_config, mock_agent):
        """Test delegation requiring approval"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        # Create mock agent
        agent = mock_agent("test_agent", orchestrator_config)

        with patch.object(orchestrator, "_determine_agent", return_value="test_agent"):
            orchestrator.register_agent("test_agent", agent)

            # Mock policy to require approval
            with patch.object(
                agent.policy, "check_action", new_callable=AsyncMock
            ) as mock_policy:
                mock_policy.return_value = {
                    "requires_approval": True,
                    "reason": "Test approval required",
                }

                with patch.object(
                    orchestrator, "_create_approval_issue", new_callable=AsyncMock
                ) as mock_create:
                    mock_create.return_value = {"issue_number": 123}

                    result = await orchestrator._delegate_task(
                        {
                            "task_type": "approval_task",
                            "task_data": {"action": "test_action"},
                        }
                    )

        assert result["status"] == "pending_approval"
        assert "approval_issue" in result
        assert result["approval_issue"]["issue_number"] == 123

    @pytest.mark.asyncio
    async def test_route_task(self, orchestrator_config):
        """Test task routing"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        with patch.object(orchestrator, "_determine_agent", return_value="test_agent"):
            with patch.object(
                orchestrator.message_queue, "enqueue", new_callable=AsyncMock
            ) as mock_enqueue:
                result = await orchestrator._route_task(
                    {"task_type": "test_task", "priority": 5}
                )

        assert result["status"] == "queued"
        assert result["agent"] == "test_agent"
        assert result["priority"] == 5
        mock_enqueue.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parallel(self, orchestrator_config, mock_agent):
        """Test parallel task execution"""
        orchestrator = OrchestratorAgent(orchestrator_config)
        agent = mock_agent("test_agent", orchestrator_config)

        with patch.object(orchestrator, "_determine_agent", return_value="test_agent"):
            orchestrator.register_agent("test_agent", agent)

            tasks = [
                {
                    "type": "task1",
                    "data": {"action": "test_action", "params": {"id": 1}},
                },
                {
                    "type": "task2",
                    "data": {"action": "test_action", "params": {"id": 2}},
                },
                {
                    "type": "task3",
                    "data": {"action": "test_action", "params": {"id": 3}},
                },
            ]

            result = await orchestrator._execute_parallel({"tasks": tasks})

        assert result["status"] == "completed"
        assert result["total_tasks"] == 3
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_execute_sequential(self, orchestrator_config, mock_agent):
        """Test sequential task execution"""
        orchestrator = OrchestratorAgent(orchestrator_config)
        agent = mock_agent("test_agent", orchestrator_config)

        with patch.object(orchestrator, "_determine_agent", return_value="test_agent"):
            orchestrator.register_agent("test_agent", agent)

            tasks = [
                {"type": "task1", "data": {"action": "test_action"}},
                {"type": "task2", "data": {"action": "test_action"}},
            ]

            result = await orchestrator._execute_sequential({"tasks": tasks})

        assert result["status"] == "completed"
        assert result["total_tasks"] == 2
        assert result["completed"] == 2

    @pytest.mark.asyncio
    async def test_execute_sequential_stop_on_error(self, orchestrator_config):
        """Test sequential execution with stop on error"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        # Create agent that fails on second task
        class FailingAgent(BaseAgent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.call_count = 0

            def get_supported_actions(self):
                return ["test_action"]

            async def _execute(self, task):
                self.call_count += 1
                if self.call_count == 2:
                    raise Exception("Simulated failure")
                return {"result": "success"}

        agent = FailingAgent("failing_agent", orchestrator_config)

        with patch.object(
            orchestrator, "_determine_agent", return_value="failing_agent"
        ):
            orchestrator.register_agent("failing_agent", agent)

            tasks = [
                {"type": "task1", "data": {"action": "test_action"}},
                {"type": "task2", "data": {"action": "test_action"}},
                {"type": "task3", "data": {"action": "test_action"}},
            ]

            result = await orchestrator._execute_sequential(
                {"tasks": tasks, "stop_on_error": True}
            )

        # Should stop after error in task 2
        assert result["completed"] == 2

    @pytest.mark.asyncio
    async def test_create_approval_issue(self, orchestrator_config):
        """Test approval issue creation"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.html_url = "https://github.com/test/test/issues/123"

        with patch.object(orchestrator.github, "create_issue", return_value=mock_issue):
            result = await orchestrator._create_approval_issue(
                {
                    "action": "test_action",
                    "agent": "test_agent",
                    "reason": "Test approval",
                    "task_data": {"repo_owner": "test_owner", "repo_name": "test_repo"},
                }
            )

        assert result["status"] == "success"
        assert result["issue_number"] == 123
        assert "issue_url" in result

    @pytest.mark.asyncio
    async def test_get_agent_status(self, orchestrator_config, mock_agent):
        """Test getting agent status"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        agent1 = mock_agent("agent1", orchestrator_config)
        agent2 = mock_agent("agent2", orchestrator_config)

        orchestrator.register_agent("agent1", agent1)
        orchestrator.register_agent("agent2", agent2)

        result = await orchestrator._get_agent_status({})

        assert result["status"] == "success"
        assert result["total_agents"] == 2
        assert "agent1" in result["agents"]
        assert "agent2" in result["agents"]
        assert result["agents"]["agent1"]["available"] is True
        assert result["agents"]["agent2"]["available"] is True

    def test_get_supported_actions(self, orchestrator_config):
        """Test getting supported actions"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        actions = orchestrator.get_supported_actions()

        assert "delegate_task" in actions
        assert "route_task" in actions
        assert "execute_parallel" in actions
        assert "execute_sequential" in actions
        assert "create_approval_issue" in actions
        assert "get_agent_status" in actions

    @pytest.mark.asyncio
    async def test_execute_main_actions(self, orchestrator_config, mock_agent):
        """Test main execute method with different actions"""
        orchestrator = OrchestratorAgent(orchestrator_config)
        agent = mock_agent("test_agent", orchestrator_config)

        with patch.object(orchestrator, "_determine_agent", return_value="test_agent"):
            orchestrator.register_agent("test_agent", agent)

            # Test delegate_task
            task1 = {
                "action": "delegate_task",
                "params": {
                    "task_type": "test_task",
                    "task_data": {"action": "test_action"},
                },
            }
            result1 = await orchestrator._execute(task1)
            assert "status" in result1

            # Test get_agent_status
            task2 = {"action": "get_agent_status", "params": {}}
            result2 = await orchestrator._execute(task2)
            assert result2["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, orchestrator_config):
        """Test execution with unknown action"""
        orchestrator = OrchestratorAgent(orchestrator_config)

        task = {"action": "unknown_action", "params": {}}

        with pytest.raises(ValueError, match="Unknown action"):
            await orchestrator._execute(task)

    @pytest.mark.asyncio
    async def test_parallel_execution_batching(self, orchestrator_config, mock_agent):
        """Test parallel execution respects batch size"""
        orchestrator = OrchestratorAgent(orchestrator_config)
        agent = mock_agent("test_agent", orchestrator_config)

        # Set max_parallel_tasks to 2
        orchestrator.max_parallel_tasks = 2

        with patch.object(orchestrator, "_determine_agent", return_value="test_agent"):
            orchestrator.register_agent("test_agent", agent)

            # Create 5 tasks (should execute in batches of 2)
            tasks = [
                {"type": f"task{i}", "data": {"action": "test_action"}}
                for i in range(5)
            ]

            result = await orchestrator._execute_parallel({"tasks": tasks})

        assert result["total_tasks"] == 5
        assert len(result["results"]) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
