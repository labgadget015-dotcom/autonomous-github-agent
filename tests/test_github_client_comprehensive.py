"""Comprehensive test suite for GitHubClient."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from github import GithubException
from autonomous_agent.core.github_client import GitHubClient


@pytest.fixture
def mock_github_api():
    """Mock the Github API."""
    with patch('autonomous_agent.core.github_client.Github') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Mock user
        mock_user = MagicMock()
        mock_user.login = "test_user"
        mock_instance.get_user.return_value = mock_user
        
        # Mock rate limit
        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4500
        mock_rate_limit.core.limit = 5000
        mock_rate_limit.core.reset = 1234567890
        mock_instance.get_rate_limit.return_value = mock_rate_limit
        
        yield mock_instance


@pytest.fixture
def mock_config():
    """Mock configuration."""
    config = MagicMock()
    config.github.token = "test_token"
    config.github.timeout = 30
    return config


@pytest.fixture
def github_client(mock_github_api, mock_config):
    """Create GitHubClient instance with mocked dependencies."""
    with patch('autonomous_agent.core.github_client.get_config', return_value=mock_config):
        client = GitHubClient(token="test_token_override")
    return client


class TestGitHubClient:
    """Test suite for GitHubClient."""
    
    def test_initialization_with_token(self, mock_config):
        """Test client initialization with explicit token."""
        with patch('autonomous_agent.core.github_client.get_config', return_value=mock_config):
            with patch('autonomous_agent.core.github_client.Github') as mock_github:
                mock_user = MagicMock()
                mock_github.return_value.get_user.return_value = mock_user
                
                client = GitHubClient(token="explicit_token")
                
                assert client.token == "explicit_token"
                mock_github.assert_called_once_with("explicit_token", timeout=30)
    
    def test_initialization_default_token(self, mock_config):
        """Test client initialization with config token."""
        with patch('autonomous_agent.core.github_client.get_config', return_value=mock_config):
            with patch('autonomous_agent.core.github_client.Github') as mock_github:
                mock_user = MagicMock()
                mock_github.return_value.get_user.return_value = mock_user
                
                client = GitHubClient()
                
                assert client.token == "test_token"
    
    def test_get_repository_success(self, github_client, mock_github_api):
        """Test successful repository retrieval."""
        mock_repo = MagicMock()
        mock_repo.name = "test-repo"
        mock_repo.full_name = "owner/test-repo"
        mock_github_api.get_repo.return_value = mock_repo
        
        repo = github_client.get_repository("owner/test-repo")
        
        assert repo.name == "test-repo"
        assert repo.full_name == "owner/test-repo"
        mock_github_api.get_repo.assert_called_once_with("owner/test-repo")
    
    def test_get_repository_retry_on_failure(self, github_client, mock_github_api):
        """Test retry mechanism on repository fetch failure."""
        mock_github_api.get_repo.side_effect = [
            GithubException(500, "Server error"),
            GithubException(500, "Server error"),
            MagicMock(name="test-repo")  # Success on third attempt
        ]
        
        repo = github_client.get_repository("owner/test-repo")
        
        assert repo.name == "test-repo"
        assert mock_github_api.get_repo.call_count == 3
    
    def test_get_pull_requests_open(self, github_client):
        """Test getting open pull requests."""
        mock_repo = MagicMock()
        mock_pr1 = MagicMock()
        mock_pr1.number = 1
        mock_pr1.state = "open"
        mock_pr2 = MagicMock()
        mock_pr2.number = 2
        mock_pr2.state = "open"
        mock_repo.get_pulls.return_value = [mock_pr1, mock_pr2]
        
        prs = github_client.get_pull_requests(mock_repo, state="open")
        
        assert len(prs) == 2
        assert prs[0].number == 1
        assert prs[1].number == 2
        mock_repo.get_pulls.assert_called_once_with(state="open")
    
    def test_get_pull_requests_all_states(self, github_client):
        """Test getting PRs with all state."""
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = [MagicMock(), MagicMock(), MagicMock()]
        
        prs = github_client.get_pull_requests(mock_repo, state="all")
        
        assert len(prs) == 3
        mock_repo.get_pulls.assert_called_once_with(state="all")
    
    def test_get_issues_open(self, github_client):
        """Test getting open issues."""
        mock_repo = MagicMock()
        mock_issue1 = MagicMock()
        mock_issue1.number = 10
        mock_issue2 = MagicMock()
        mock_issue2.number = 20
        mock_repo.get_issues.return_value = [mock_issue1, mock_issue2]
        
        issues = github_client.get_issues(mock_repo, state="open")
        
        assert len(issues) == 2
        assert issues[0].number == 10
        assert issues[1].number == 20
    
    def test_get_issues_closed(self, github_client):
        """Test getting closed issues."""
        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = [MagicMock(number=30, state="closed")]
        
        issues = github_client.get_issues(mock_repo, state="closed")
        
        assert len(issues) == 1
        assert issues[0].number == 30
        mock_repo.get_issues.assert_called_once_with(state="closed")
    
    def test_create_issue_comment(self, github_client):
        """Test creating a comment on an issue."""
        mock_issue = MagicMock()
        comment_text = "This is a test comment"
        
        github_client.create_issue_comment(mock_issue, comment_text)
        
        mock_issue.create_comment.assert_called_once_with(comment_text)
    
    def test_create_pr_review_comment(self, github_client):
        """Test creating an inline PR review comment."""
        mock_pr = MagicMock()
        
        github_client.create_pr_review_comment(
            pr=mock_pr,
            body="Fix this line",
            commit_id="abc123",
            path="src/main.py",
            line=42
        )
        
        mock_pr.create_review_comment.assert_called_once_with(
            body="Fix this line",
            commit_id="abc123",
            path="src/main.py",
            line=42
        )
    
    def test_get_rate_limit(self, github_client, mock_github_api):
        """Test getting rate limit information."""
        rate_limit = github_client.get_rate_limit()
        
        assert rate_limit["core"]["remaining"] == 4500
        assert rate_limit["core"]["limit"] == 5000
        assert rate_limit["core"]["reset"] == 1234567890
    
    def test_close_connection(self, github_client, mock_github_api):
        """Test closing GitHub client connection."""
        github_client.close()
        mock_github_api.close.assert_called_once()
    
    def test_user_property(self, github_client):
        """Test user property is set on initialization."""
        assert hasattr(github_client, 'user')
        assert github_client.user.login == "test_user"
    
    def test_retry_exhaustion_raises_exception(self, github_client, mock_github_api):
        """Test that retry exhaustion raises exception."""
        mock_github_api.get_repo.side_effect = GithubException(500, "Persistent error")
        
        with pytest.raises(GithubException):
            github_client.get_repository("owner/repo")
        
        # Should attempt 3 times (initial + 2 retries)
        assert mock_github_api.get_repo.call_count == 3
    
    def test_get_pull_requests_empty_list(self, github_client):
        """Test getting PRs when none exist."""
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = []
        
        prs = github_client.get_pull_requests(mock_repo)
        
        assert prs == []
        assert isinstance(prs, list)
    
    def test_get_issues_empty_list(self, github_client):
        """Test getting issues when none exist."""
        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = []
        
        issues = github_client.get_issues(mock_repo)
        
        assert issues == []
        assert isinstance(issues, list)
