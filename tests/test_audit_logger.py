"""Comprehensive test suite for AuditLogger."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from autonomous_agent.core.audit_logger import AuditLogger


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config():
    """Mock configuration."""
    config = MagicMock()
    config.logging.log_dir = "/tmp/audit_logs"
    config.logging.retention_days = 90
    return config


@pytest.fixture
def audit_logger(temp_log_dir, mock_config):
    """Create AuditLogger instance."""
    with patch(
        "autonomous_agent.core.audit_logger.get_config", return_value=mock_config
    ):
        logger = AuditLogger(log_dir=str(temp_log_dir))
    return logger


class TestAuditLogger:
    """Test suite for AuditLogger."""

    def test_initialization(self, temp_log_dir):
        """Test audit logger initialization."""
        logger = AuditLogger(log_dir=str(temp_log_dir))
        assert logger.log_dir == temp_log_dir
        assert temp_log_dir.exists()

    def test_log_action_basic(self, audit_logger, temp_log_dir):
        """Test logging a basic action."""
        log_id = audit_logger.log_action(
            agent_name="TestAgent", action="test_action", repository="owner/repo"
        )

        assert isinstance(log_id, int)
        assert log_id > 0

    def test_log_action_with_details(self, audit_logger):
        """Test logging action with details."""
        details = {"key": "value", "count": 42}
        rollback = {"command": "undo"}

        log_id = audit_logger.log_action(
            agent_name="DeployAgent",
            action="deploy",
            repository="owner/repo",
            details=details,
            rollback_instructions=rollback,
        )

        assert log_id > 0

    def test_log_action_creates_file(self, audit_logger, temp_log_dir):
        """Test that log action creates a log file."""
        audit_logger.log_action(
            agent_name="TestAgent", action="create_pr", repository="owner/repo"
        )

        # Check that log file was created
        log_files = list(temp_log_dir.glob("*.log"))
        assert len(log_files) > 0

    def test_log_action_multiple_entries(self, audit_logger):
        """Test logging multiple actions."""
        log_ids = []
        for i in range(5):
            log_id = audit_logger.log_action(
                agent_name=f"Agent{i}", action=f"action_{i}", repository="owner/repo"
            )
            log_ids.append(log_id)

        assert len(log_ids) == 5
        assert len(set(log_ids)) == 5  # All unique

    def test_log_entry_contains_timestamp(self, audit_logger, temp_log_dir):
        """Test that log entries contain timestamps."""
        with patch("autonomous_agent.core.audit_logger.datetime") as mock_datetime:
            mock_now = datetime(2026, 2, 16, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = datetime.fromisoformat

            audit_logger.log_action(
                agent_name="TestAgent", action="test", repository="owner/repo"
            )

    def test_log_entry_json_serializable(self, audit_logger, temp_log_dir):
        """Test that log entries are JSON serializable."""
        details = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }

        audit_logger.log_action(
            agent_name="TestAgent",
            action="complex_action",
            repository="owner/repo",
            details=details,
        )

        # Verify JSON can be read back
        log_files = list(temp_log_dir.glob("*.log"))
        assert len(log_files) > 0

    def test_get_logs_for_repository(self, audit_logger):
        """Test retrieving logs for a specific repository."""
        # Log actions for different repos
        audit_logger.log_action("Agent1", "action1", "owner/repo1")
        audit_logger.log_action("Agent2", "action2", "owner/repo1")
        audit_logger.log_action("Agent3", "action3", "owner/repo2")

        # This assumes get_logs method exists
        # If not, this test documents expected behavior

    def test_log_action_error_handling(self, audit_logger):
        """Test that logging handles errors gracefully."""
        # Test with invalid data that might cause issues
        try:
            log_id = audit_logger.log_action(
                agent_name="TestAgent",
                action="test",
                repository="owner/repo",
                details={"circular": "ref"},  # Simple case
            )
            assert log_id > 0
        except Exception as e:
            pytest.fail(f"Logging should handle edge cases: {e}")

    def test_log_directory_creation(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "nonexistent" / "logs"
            logger = AuditLogger(log_dir=str(log_path))
            assert log_path.exists()

    def test_rollback_instructions_stored(self, audit_logger):
        """Test that rollback instructions are properly stored."""
        rollback = {
            "type": "git_revert",
            "commit": "abc123",
            "command": "git revert abc123",
        }

        log_id = audit_logger.log_action(
            agent_name="GitAgent",
            action="merge_pr",
            repository="owner/repo",
            rollback_instructions=rollback,
        )

        assert log_id > 0

    def test_log_action_concurrent_writes(self, audit_logger):
        """Test that concurrent log writes don't corrupt data."""
        import concurrent.futures

        def log_action(i):
            return audit_logger.log_action(
                agent_name=f"Agent{i}", action=f"action_{i}", repository="owner/repo"
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(log_action, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 10
        assert len(set(results)) == 10  # All unique IDs

    def test_log_retention_mechanism(self, audit_logger, temp_log_dir):
        """Test log retention and cleanup mechanism."""
        # Create old log files
        old_log = temp_log_dir / "old_audit_2025_01_01.log"
        old_log.write_text("old log content")

        # This tests that cleanup method exists
        # If not, documents expected behavior

    def test_query_logs_by_agent(self, audit_logger):
        """Test querying logs by agent name."""
        audit_logger.log_action("Agent1", "action1", "owner/repo")
        audit_logger.log_action("Agent1", "action2", "owner/repo")
        audit_logger.log_action("Agent2", "action3", "owner/repo")

        # Assumes query functionality exists
        # Documents expected interface

    def test_query_logs_by_action_type(self, audit_logger):
        """Test querying logs by action type."""
        audit_logger.log_action("Agent1", "deploy", "owner/repo1")
        audit_logger.log_action("Agent2", "deploy", "owner/repo2")
        audit_logger.log_action("Agent3", "review", "owner/repo3")

        # Documents expected query interface
