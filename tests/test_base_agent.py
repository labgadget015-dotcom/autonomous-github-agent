"""Comprehensive test suite for BaseAgent class."""

from unittest.mock import Mock, patch

import pytest

from autonomous_agent.core.audit_logger import AuditLogger
from autonomous_agent.core.base_agent import BaseAgent
from autonomous_agent.core.github_client import GitHubClient
from autonomous_agent.core.llm_client import LLMClient


class TestAgentImplementation(BaseAgent):
    """Concrete implementation for testing abstract BaseAgent."""

    async def execute(self, repository: str, **kwargs):
        """Test implementation of execute method."""
        return {"status": "success", "repository": repository, "kwargs": kwargs}


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client."""
    return Mock(spec=GitHubClient)


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    return Mock(spec=LLMClient)


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger."""
    mock = Mock(spec=AuditLogger)
    mock.log_action.return_value = 12345  # Mock log ID
    return mock


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock()
    config.requires_approval = Mock(return_value=False)
    return config


@pytest.fixture
def test_agent(mock_github_client, mock_llm_client, mock_audit_logger, mock_config):
    """Create a test agent instance."""
    with patch("autonomous_agent.core.base_agent.get_config", return_value=mock_config):
        agent = TestAgentImplementation(
            github_client=mock_github_client,
            llm_client=mock_llm_client,
            audit_logger=mock_audit_logger,
        )
    return agent


class TestBaseAgent:
    """Test suite for BaseAgent class."""

    def test_initialization(
        self, test_agent, mock_github_client, mock_llm_client, mock_audit_logger
    ):
        """Test agent initialization."""
        assert test_agent.github == mock_github_client
        assert test_agent.llm == mock_llm_client
        assert test_agent.audit == mock_audit_logger
        assert test_agent.name == "TestAgentImplementation"

    @pytest.mark.asyncio
    async def test_execute_basic(self, test_agent):
        """Test basic execute method."""
        result = await test_agent.execute("owner/repo")
        assert result["status"] == "success"
        assert result["repository"] == "owner/repo"

    @pytest.mark.asyncio
    async def test_execute_with_kwargs(self, test_agent):
        """Test execute with additional keyword arguments."""
        result = await test_agent.execute(
            "owner/repo", action="test_action", priority="high"
        )
        assert result["kwargs"]["action"] == "test_action"
        assert result["kwargs"]["priority"] == "high"

    def test_log_action_basic(self, test_agent, mock_audit_logger):
        """Test logging an action."""
        log_id = test_agent.log_action(action="test_action", repository="owner/repo")

        assert log_id == 12345
        mock_audit_logger.log_action.assert_called_once_with(
            agent_name="TestAgentImplementation",
            action="test_action",
            repository="owner/repo",
            details=None,
            rollback_instructions=None,
        )

    def test_log_action_with_details(self, test_agent, mock_audit_logger):
        """Test logging action with details and rollback."""
        details = {"key": "value", "count": 42}
        rollback = {"undo": "command"}

        test_agent.log_action(
            action="deploy", repository="owner/repo", details=details, rollback=rollback
        )

        mock_audit_logger.log_action.assert_called_once_with(
            agent_name="TestAgentImplementation",
            action="deploy",
            repository="owner/repo",
            details=details,
            rollback_instructions=rollback,
        )

    def test_requires_approval_true(self, test_agent, mock_config):
        """Test requires_approval when approval is needed."""
        mock_config.requires_approval.return_value = True
        result = test_agent.requires_approval("delete_branch")
        assert result is True
        mock_config.requires_approval.assert_called_once_with("delete_branch")

    def test_requires_approval_false(self, test_agent, mock_config):
        """Test requires_approval when no approval needed."""
        mock_config.requires_approval.return_value = False
        result = test_agent.requires_approval("create_pr")
        assert result is False

    def test_requires_approval_no_method(self, test_agent):
        """Test requires_approval when config has no method."""
        test_agent.config = Mock(spec=[])  # Config without requires_approval method
        result = test_agent.requires_approval("any_action")
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_multiple_calls(self, test_agent):
        """Test multiple sequential execute calls."""
        results = []
        for i in range(3):
            result = await test_agent.execute(f"owner/repo{i}", iteration=i)
            results.append(result)

        assert len(results) == 3
        assert results[0]["repository"] == "owner/repo0"
        assert results[1]["repository"] == "owner/repo1"
        assert results[2]["repository"] == "owner/repo2"

    def test_agent_name_property(self, test_agent):
        """Test agent name property is set correctly."""
        assert hasattr(test_agent, "name")
        assert isinstance(test_agent.name, str)
        assert test_agent.name == test_agent.__class__.__name__
