"""Unit tests for .github/scripts/notification_manager.py"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from notification_manager import NotificationManager


def _make_manager(monkeypatch=None, slack_url=None, discord_url=None):
    if monkeypatch:
        if slack_url:
            monkeypatch.setenv("SLACK_WEBHOOK_URL", slack_url)
        else:
            monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
        if discord_url:
            monkeypatch.setenv("DISCORD_WEBHOOK_URL", discord_url)
        else:
            monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    return NotificationManager()


class TestNotificationManagerInit:
    def test_no_channels_when_no_env_vars(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        assert manager.enabled_channels == []

    def test_slack_enabled_when_env_set(self, monkeypatch):
        manager = _make_manager(monkeypatch, slack_url="https://hooks.slack.com/test")
        assert "slack" in manager.enabled_channels

    def test_discord_enabled_when_env_set(self, monkeypatch):
        manager = _make_manager(
            monkeypatch, discord_url="https://discord.com/api/webhooks/test"
        )
        assert "discord" in manager.enabled_channels

    def test_both_channels_enabled(self, monkeypatch):
        manager = _make_manager(
            monkeypatch,
            slack_url="https://hooks.slack.com/test",
            discord_url="https://discord.com/api/webhooks/test",
        )
        assert len(manager.enabled_channels) == 2


class TestSendSlackNotification:
    def test_returns_false_when_no_webhook(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        result = manager.send_slack_notification("test message")
        assert result is False

    def test_returns_true_on_success(self, monkeypatch):
        manager = _make_manager(monkeypatch, slack_url="https://hooks.slack.com/test")
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("requests.post", return_value=mock_response):
            result = manager.send_slack_notification("test message", "success")
        assert result is True

    def test_returns_false_on_request_exception(self, monkeypatch):
        manager = _make_manager(monkeypatch, slack_url="https://hooks.slack.com/test")
        with patch("requests.post", side_effect=Exception("Connection error")):
            result = manager.send_slack_notification("test message")
        assert result is False


class TestSendDiscordNotification:
    def test_returns_false_when_no_webhook(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        result = manager.send_discord_notification("test message")
        assert result is False

    def test_returns_true_on_204(self, monkeypatch):
        manager = _make_manager(monkeypatch, discord_url="https://discord.com/api/test")
        mock_response = MagicMock()
        mock_response.status_code = 204
        with patch("requests.post", return_value=mock_response):
            result = manager.send_discord_notification("test")
        assert result is True

    def test_returns_false_on_exception(self, monkeypatch):
        manager = _make_manager(monkeypatch, discord_url="https://discord.com/api/test")
        with patch("requests.post", side_effect=Exception("Network error")):
            result = manager.send_discord_notification("test")
        assert result is False


class TestNotifyWorkflowStatus:
    def test_success_notification_sent(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        with patch.object(manager, "send_all_channels") as mock_send:
            manager.notify_workflow_status("ci.yml", "success", 120)
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "✅" in args[0] or "completed successfully" in args[0]
        assert args[1] == "success"

    def test_failure_notification_sent(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        with patch.object(manager, "send_all_channels") as mock_send:
            manager.notify_workflow_status("ci.yml", "failure", 60)
        args = mock_send.call_args[0]
        assert "❌" in args[0] or "failed" in args[0]
        assert args[1] == "error"


class TestNotifySecurityIssue:
    def test_security_message_contains_severity(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        with patch.object(manager, "send_all_channels") as mock_send:
            manager.notify_security_issue(
                {"severity": "HIGH", "file": "app.py", "line": 42}
            )
        args = mock_send.call_args[0]
        assert "HIGH" in args[0]
        assert "app.py" in args[0]


class TestNotifyCoverageDrop:
    def test_coverage_drop_notification(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        with patch.object(manager, "send_all_channels") as mock_send:
            manager.notify_coverage_drop(80.0, 65.0)
        args = mock_send.call_args[0]
        assert "15.0%" in args[0]
        assert args[1] == "warning"


class TestNotifyQualityGateFailure:
    def test_quality_gate_message_contains_failures(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        with patch.object(manager, "send_all_channels") as mock_send:
            manager.notify_quality_gate_failure(
                ["Coverage below 80%", "Security issues found"]
            )
        args = mock_send.call_args[0]
        assert "Coverage below 80%" in args[0]
        assert "Security issues found" in args[0]


class TestSendAllChannels:
    def test_no_channels_returns_empty_dict(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        result = manager.send_all_channels("test")
        assert result == {}

    def test_sends_to_slack_when_enabled(self, monkeypatch):
        manager = _make_manager(monkeypatch, slack_url="https://hooks.slack.com/test")
        with patch.object(
            manager, "send_slack_notification", return_value=True
        ) as mock_slack:
            result = manager.send_all_channels("test msg")
        mock_slack.assert_called_once()
        assert "slack" in result

    def test_sends_to_discord_when_enabled(self, monkeypatch):
        manager = _make_manager(monkeypatch, discord_url="https://discord.com/api/test")
        with patch.object(
            manager, "send_discord_notification", return_value=True
        ) as mock_discord:
            result = manager.send_all_channels("test msg")
        mock_discord.assert_called_once()
        assert "discord" in result


class TestSendDailySummary:
    def test_sends_daily_summary(self, monkeypatch):
        manager = _make_manager(monkeypatch)
        with patch.object(manager, "send_all_channels") as mock_send:
            manager.send_daily_summary(
                {
                    "total_runs": 50,
                    "success_rate": 0.95,
                    "avg_duration": 120.5,
                    "coverage": 85.0,
                    "security_issues": 2,
                }
            )
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert "50" in msg  # total_runs
        assert "85.0" in msg  # coverage
