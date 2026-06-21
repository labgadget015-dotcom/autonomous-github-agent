"""Tests for GitHub client."""

from unittest.mock import patch

from autonomous_agent.core.github_client import GitHubClient


@patch("autonomous_agent.core.github_client.Github")
def test_github_client_initialization(mock_github):
    """Test GitHub client initialization."""
    with patch("autonomous_agent.core.config.get_config") as mock_config:
        mock_config.return_value.github.token = "test_token"
        mock_config.return_value.github.timeout = 30

        client = GitHubClient()
        assert client.token == "test_token"
