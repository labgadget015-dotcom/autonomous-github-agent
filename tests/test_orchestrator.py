"""Comprehensive test suite for Orchestrator."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from autonomous_agent.core.orchestrator import Orchestrator


@pytest.fixture
def mock_dependencies():
    """Mock all orchestrator dependencies."""
    mocks = {
        "config": MagicMock(),
        "github_client": MagicMock(),
        "llm_client": MagicMock(),
        "audit_logger": MagicMock(),
    }

    mocks["config"].enabled_agents = ["health_monitor", "code_reviewer"]

    return mocks


@pytest.fixture
def orchestrator(mock_dependencies):
    """Create Orchestrator instance with mocked dependencies."""
    with patch(
        "autonomous_agent.core.orchestrator.get_config",
        return_value=mock_dependencies["config"],
    ):
        with patch(
            "autonomous_agent.core.orchestrator.GitHubClient",
            return_value=mock_dependencies["github_client"],
        ):
            with patch(
                "autonomous_agent.core.orchestrator.LLMClient",
                return_value=mock_dependencies["llm_client"],
            ):
                with patch(
                    "autonomous_agent.core.orchestrator.AuditLogger",
                    return_value=mock_dependencies["audit_logger"],
                ):
                    orch = Orchestrator()
    return orch


class TestOrchestrator:
    """Test suite for Orchestrator."""

    def test_initialization(self, orchestrator, mock_dependencies):
        """Test orchestrator initialization."""
        assert orchestrator.config == mock_dependencies["config"]
        assert orchestrator.github == mock_dependencies["github_client"]
        assert orchestrator.llm == mock_dependencies["llm_client"]
        assert orchestrator.audit == mock_dependencies["audit_logger"]
        assert hasattr(orchestrator, "agents")
        assert isinstance(orchestrator.agents, dict)

    def test_load_agents_called_on_init(self, mock_dependencies):
        """Test that _load_agents is called during initialization."""
        with patch(
            "autonomous_agent.core.orchestrator.get_config",
            return_value=mock_dependencies["config"],
        ):
            with patch("autonomous_agent.core.orchestrator.GitHubClient"):
                with patch("autonomous_agent.core.orchestrator.LLMClient"):
                    with patch("autonomous_agent.core.orchestrator.AuditLogger"):
                        with patch.object(Orchestrator, "_load_agents") as mock_load:
                            orch = Orchestrator()
                            mock_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_health_check_basic(self, orchestrator):
        """Test basic health check."""
        result = await orchestrator.run_health_check("owner/repo")

        assert result["status"] == "healthy"
        assert result["repository"] == "owner/repo"
        assert "checks" in result
        assert result["checks"]["github_connection"] == "ok"
        assert result["checks"]["llm_connection"] == "ok"

    @pytest.mark.asyncio
    async def test_run_health_check_multiple_repos(self, orchestrator):
        """Test health check for multiple repositories."""
        repos = ["owner/repo1", "owner/repo2", "owner/repo3"]
        results = []

        for repo in repos:
            result = await orchestrator.run_health_check(repo)
            results.append(result)

        assert len(results) == 3
        assert all(r["status"] == "healthy" for r in results)
        assert results[0]["repository"] == "owner/repo1"
        assert results[1]["repository"] == "owner/repo2"
        assert results[2]["repository"] == "owner/repo3"

    @pytest.mark.asyncio
    async def test_monitor_repository_basic(self, orchestrator):
        """Test repository monitoring starts correctly."""
        # Use asyncio.wait_for to prevent infinite loop
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                orchestrator.monitor_repository("owner/repo"), timeout=0.1
            )

    @pytest.mark.asyncio
    async def test_monitor_repository_sleep_interval(self, orchestrator):
        """Test monitoring sleep interval."""
        with patch("autonomous_agent.core.orchestrator.asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = asyncio.CancelledError()

            try:
                await orchestrator.monitor_repository("owner/repo")
            except asyncio.CancelledError:
                pass

            mock_sleep.assert_called_with(60)

    def test_close_cleans_up_resources(self, orchestrator, mock_dependencies):
        """Test that close() cleans up resources."""
        orchestrator.close()
        mock_dependencies["github_client"].close.assert_called_once()

    def test_agents_dictionary_accessible(self, orchestrator):
        """Test that agents dictionary is accessible."""
        assert hasattr(orchestrator, "agents")
        assert isinstance(orchestrator.agents, dict)
        # Initially empty as no agents loaded
        # Will be populated in future implementations

    def test_config_accessible(self, orchestrator, mock_dependencies):
        """Test that configuration is accessible."""
        assert orchestrator.config == mock_dependencies["config"]
        assert orchestrator.config.enabled_agents == ["health_monitor", "code_reviewer"]

    def test_github_client_accessible(self, orchestrator, mock_dependencies):
        """Test that GitHub client is accessible."""
        assert orchestrator.github == mock_dependencies["github_client"]

    def test_llm_client_accessible(self, orchestrator, mock_dependencies):
        """Test that LLM client is accessible."""
        assert orchestrator.llm == mock_dependencies["llm_client"]

    def test_audit_logger_accessible(self, orchestrator, mock_dependencies):
        """Test that audit logger is accessible."""
        assert orchestrator.audit == mock_dependencies["audit_logger"]

    @pytest.mark.asyncio
    async def test_health_check_response_structure(self, orchestrator):
        """Test health check response has correct structure."""
        result = await orchestrator.run_health_check("test/repo")

        # Verify all required keys are present
        assert "status" in result
        assert "repository" in result
        assert "checks" in result

        # Verify checks structure
        assert isinstance(result["checks"], dict)
        assert "github_connection" in result["checks"]
        assert "llm_connection" in result["checks"]

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, orchestrator):
        """Test running health checks concurrently."""
        repos = [f"owner/repo{i}" for i in range(5)]

        tasks = [orchestrator.run_health_check(repo) for repo in repos]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["repository"] == f"owner/repo{i}"
            assert result["status"] == "healthy"

    def test_load_agents_respects_enabled_config(self, mock_dependencies):
        """Test that _load_agents respects enabled_agents config."""
        mock_dependencies["config"].enabled_agents = ["agent1", "agent2"]

        with patch(
            "autonomous_agent.core.orchestrator.get_config",
            return_value=mock_dependencies["config"],
        ):
            with patch("autonomous_agent.core.orchestrator.GitHubClient"):
                with patch("autonomous_agent.core.orchestrator.LLMClient"):
                    with patch("autonomous_agent.core.orchestrator.AuditLogger"):
                        orch = Orchestrator()
                        # Current implementation doesn't populate agents yet
                        # This test documents expected behavior

    @pytest.mark.asyncio
    async def test_monitor_handles_cancellation(self, orchestrator):
        """Test that monitor_repository handles cancellation gracefully."""
        task = asyncio.create_task(orchestrator.monitor_repository("owner/repo"))
        await asyncio.sleep(0.01)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    def test_multiple_orchestrator_instances(self, mock_dependencies):
        """Test creating multiple orchestrator instances."""
        with patch(
            "autonomous_agent.core.orchestrator.get_config",
            return_value=mock_dependencies["config"],
        ):
            with patch("autonomous_agent.core.orchestrator.GitHubClient"):
                with patch("autonomous_agent.core.orchestrator.LLMClient"):
                    with patch("autonomous_agent.core.orchestrator.AuditLogger"):
                        orch1 = Orchestrator()
                        orch2 = Orchestrator()

        assert orch1 is not orch2
        assert orch1.agents is not orch2.agents
