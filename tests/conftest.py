"""Pytest configuration and fixtures for test suite."""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ---------------------------------------------------------------------------
# Generic fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_directory(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def temp_file(tmp_path):
    """Provide a temporary file path for tests."""
    p = tmp_path / "test_file.txt"
    p.write_text("")
    return str(p)


@pytest.fixture
def sample_config():
    """Minimal working configuration for core components."""
    return {
        "github_token": "ghp_test_token",
        "openai_api_key": "sk-test-key",
        "llm_provider": "openai",
        "model": "gpt-4",
        "max_retries": 3,
        "timeout": 30,
        "debug": True,
    }


# ---------------------------------------------------------------------------
# Mock GitHub fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_github_api():
    """Provide a mock GitHub API client (PyGithub style)."""
    mock_api = MagicMock()
    mock_repo = MagicMock()
    mock_issue = MagicMock()
    mock_issue.number = 1
    mock_issue.state = "open"
    mock_repo.create_issue.return_value = mock_issue
    mock_repo.get_issue.return_value = mock_issue
    mock_api.get_repo.return_value = mock_repo
    return mock_api


@pytest.fixture
def mock_github_client(sample_config):
    """Provide a GitHubClient with mocked PyGithub."""
    from core.github_client import GitHubClient

    with patch("core.github_client.Github") as mock_gh:
        mock_repo = MagicMock()
        mock_gh.return_value.get_repo.return_value = mock_repo
        client = GitHubClient(sample_config)
        client._mock_repo = mock_repo
        yield client


# ---------------------------------------------------------------------------
# Core component fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def audit_logger(tmp_path, sample_config):
    """Provide a real AuditLogger writing to a temp file."""
    from core.audit_logger import AuditLogger

    cfg = dict(sample_config)
    cfg["audit_log_path"] = str(tmp_path / "audit.jsonl")
    return AuditLogger(cfg)


@pytest.fixture
def policy_engine():
    """Provide a PolicyEngine using default (no file) policies."""
    from core.policy_engine import PolicyEngine

    return PolicyEngine({"policy_file": "/nonexistent/policies.yaml"})


@pytest.fixture
def message_queue(sample_config):
    """Provide a MessageQueue in in-memory mode (no Redis)."""
    from core.message_queue import MessageQueue

    with patch("core.message_queue.MessageQueue._init_redis", return_value=False):
        return MessageQueue(sample_config)


# ---------------------------------------------------------------------------
# Agent fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def base_agent_class():
    """Return a concrete BaseAgent subclass for testing."""
    from core.agent_base import BaseAgent

    class ConcreteAgent(BaseAgent):
        def get_supported_actions(self):
            return ["test_action", "noop"]

        async def _execute(self, task):
            return {"status": "success", "output": f"executed {task.get('action')}"}

        def validate(self, task):
            return "action" in task

    return ConcreteAgent


@pytest.fixture
def base_agent(base_agent_class, sample_config):
    """Provide a fully patched BaseAgent instance."""
    with (
        patch("core.agent_base.GitHubClient"),
        patch("core.agent_base.LLMClient"),
        patch("core.agent_base.AuditLogger"),
        patch("core.agent_base.PolicyEngine"),
    ):
        agent = base_agent_class("test_agent", sample_config)
        agent.policy.check_action = AsyncMock(return_value={"requires_approval": False})
        agent.audit.log_action = AsyncMock()
        return agent


@pytest.fixture
def orchestrator(sample_config):
    """Provide a fully patched OrchestratorAgent instance."""
    from agents.orchestrator_agent import OrchestratorAgent

    with (
        patch("core.agent_base.GitHubClient"),
        patch("core.agent_base.LLMClient"),
        patch("core.agent_base.AuditLogger"),
        patch("core.agent_base.PolicyEngine"),
        patch("core.message_queue.MessageQueue._init_redis", return_value=False),
    ):
        return OrchestratorAgent(sample_config)


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_task():
    """A valid task dict."""
    return {"id": "task-001", "action": "test_action", "params": {"repo": "owner/repo"}}


@pytest.fixture
def sample_json_file(tmp_path):
    """Create a sample JSON file for testing."""
    file_path = tmp_path / "test_config.json"
    test_data = {"key": "value", "number": 42, "nested": {"a": 1}}
    file_path.write_text(json.dumps(test_data))
    return str(file_path)


@pytest.fixture
def sample_policy_file(tmp_path):
    """Create a minimal policy YAML for testing."""
    content = (
        "requires_approval:\n"
        "  - delete_repository\n"
        "  - force_push_protected\n"
        "auto_approved:\n"
        "  - label_issue\n"
        "  - add_comment\n"
    )
    p = tmp_path / "policies.yaml"
    p.write_text(content)
    return str(p)
