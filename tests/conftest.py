"""Enhanced pytest configuration with comprehensive fixtures."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock


# Async test support
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_github_repo():
    """Create a mock GitHub repository."""
    repo = MagicMock()
    repo.name = "test-repo"
    repo.full_name = "test-owner/test-repo"
    repo.description = "Test repository"
    repo.default_branch = "main"
    repo.private = False
    repo.archived = False
    return repo


@pytest.fixture
def mock_github_issue():
    """Create a mock GitHub issue."""
    issue = MagicMock()
    issue.number = 1
    issue.title = "Test Issue"
    issue.body = "This is a test issue"
    issue.state = "open"
    issue.labels = []
    issue.assignees = []
    issue.created_at = "2026-02-16T00:00:00Z"
    issue.updated_at = "2026-02-16T00:00:00Z"
    return issue


@pytest.fixture
def mock_github_pr():
    """Create a mock GitHub pull request."""
    pr = MagicMock()
    pr.number = 1
    pr.title = "Test PR"
    pr.body = "This is a test pull request"
    pr.state = "open"
    pr.head = MagicMock()
    pr.head.ref = "feature-branch"
    pr.base = MagicMock()
    pr.base.ref = "main"
    pr.mergeable = True
    pr.merged = False
    pr.draft = False
    pr.created_at = "2026-02-16T00:00:00Z"
    pr.updated_at = "2026-02-16T00:00:00Z"
    return pr


@pytest.fixture
def mock_github_commit():
    """Create a mock GitHub commit."""
    commit = MagicMock()
    commit.sha = "abc123def456"
    commit.message = "Test commit message"
    commit.author = MagicMock()
    commit.author.name = "Test Author"
    commit.author.email = "test@example.com"
    return commit


@pytest.fixture
def mock_github_user():
    """Create a mock GitHub user."""
    user = MagicMock()
    user.login = "test-user"
    user.name = "Test User"
    user.email = "test@example.com"
    user.type = "User"
    return user


@pytest.fixture
def sample_config_dict():
    """Sample configuration dictionary."""
    return {
        "github": {
            "token": "test_token_12345",
            "timeout": 30,
            "max_retries": 3
        },
        "llm": {
            "provider": "openai",
            "api_key": "test_llm_key",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "automation_level": "semi-auto",
        "logging": {
            "log_dir": "/tmp/test_logs",
            "retention_days": 30,
            "log_level": "INFO"
        },
        "policies": {
            "require_approval": [
                "delete_main_branch",
                "force_push_protected",
                "deploy_production"
            ],
            "auto_approve": [
                "update_dependencies",
                "fix_linting",
                "label_issue"
            ]
        }
    }


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    response = MagicMock()
    response.content = "This is a test LLM response"
    response.model = "gpt-4"
    response.tokens_used = 150
    response.finish_reason = "stop"
    return response


@pytest.fixture
def sample_pr_review_data():
    """Sample PR review data for testing."""
    return {
        "pr_number": 42,
        "repository": "owner/repo",
        "title": "Add new feature",
        "description": "This PR adds a new feature",
        "files_changed": [
            {
                "filename": "src/main.py",
                "additions": 50,
                "deletions": 10,
                "changes": 60,
                "patch": "@@ -1,5 +1,10 @@\n def main():\n+    print('new line')\n"
            }
        ],
        "comments": [],
        "commits": 3
    }


@pytest.fixture
def sample_issue_data():
    """Sample issue data for testing."""
    return {
        "number": 123,
        "title": "Bug: Application crashes on startup",
        "body": "Steps to reproduce:\n1. Start app\n2. Crash happens",
        "labels": ["bug", "high-priority"],
        "state": "open",
        "assignee": None
    }


@pytest.fixture
def mock_audit_log_entry():
    """Create a mock audit log entry."""
    return {
        "id": 12345,
        "timestamp": "2026-02-16T12:00:00Z",
        "agent_name": "TestAgent",
        "action": "create_pr",
        "repository": "owner/repo",
        "details": {
            "pr_number": 42,
            "title": "Test PR"
        },
        "rollback_instructions": {
            "type": "close_pr",
            "pr_number": 42
        },
        "status": "success"
    }


@pytest.fixture(autouse=True)
def reset_environment_variables(monkeypatch):
    """Reset environment variables for each test."""
    test_env = {
        "GITHUB_TOKEN": "test_token",
        "OPENAI_API_KEY": "test_openai_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key"
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_file_content():
    """Mock file content for testing."""
    return {
        "README.md": "# Test Repository\n\nThis is a test.",
        "src/main.py": "def main():\n    print('Hello, World!')\n",
        "requirements.txt": "requests==2.28.0\npytest==7.2.0\n",
        ".gitignore": "*.pyc\n__pycache__/\nvenv/\n"
    }


@pytest.fixture
def mock_github_search_results():
    """Mock GitHub search results."""
    results = MagicMock()
    results.total_count = 5
    results.items = [
        MagicMock(name=f"result_{i}", score=100-i*10) 
        for i in range(5)
    ]
    return results


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interactions"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take significant time to run"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests that require external API access"
    )
