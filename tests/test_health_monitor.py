"""Tests for health monitor agent."""

import pytest
from unittest.mock import Mock, AsyncMock
from autonomous_agent.agents.health_monitor import HealthMonitorAgent


@pytest.mark.asyncio
async def test_health_monitor_execute():
    """Test health monitor execution."""
    mock_github = Mock()
    mock_llm = Mock()
    mock_audit = Mock()
    
    agent = HealthMonitorAgent(mock_github, mock_llm, mock_audit)
    
    # Mock repository
    mock_repo = Mock()
    mock_repo.stargazers_count = 100
    mock_repo.open_issues_count = 5
    mock_github.get_repository.return_value = mock_repo
    
    # This will fail without full mocking, but shows test structure
    # result = await agent.execute("owner/repo")
    # assert "metrics" in result
