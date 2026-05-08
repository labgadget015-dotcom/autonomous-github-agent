"""Unit tests for .github/scripts/workflow_monitor.py"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from workflow_monitor import GitHubActionsMonitor


def _make_monitor(token="fake-token"):
    return GitHubActionsMonitor("owner/repo", token=token)


class TestGitHubActionsMonitorInit:
    def test_creates_with_repo(self):
        m = _make_monitor()
        assert m.repo == "owner/repo"

    def test_token_set_in_headers(self):
        m = _make_monitor(token="mytoken")
        assert "Authorization" in m.headers
        assert "mytoken" in m.headers["Authorization"]

    def test_no_auth_header_without_token(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        m = GitHubActionsMonitor("owner/repo", token=None)
        assert "Authorization" not in m.headers

    def test_base_url_contains_repo(self):
        m = _make_monitor()
        assert "owner/repo" in m.base_url


class TestFormatDuration:
    def _m(self):
        return _make_monitor()

    def test_seconds_only(self):
        m = self._m()
        assert m.format_duration(45) == "45s"

    def test_minutes_and_seconds(self):
        m = self._m()
        assert m.format_duration(90) == "1m 30s"

    def test_hours_and_minutes(self):
        m = self._m()
        result = m.format_duration(3661)
        assert "1h" in result
        assert "1m" in result

    def test_exact_minute(self):
        m = self._m()
        result = m.format_duration(60)
        assert "1m" in result
        assert "0s" in result

    def test_zero_seconds(self):
        m = self._m()
        assert m.format_duration(0) == "0s"


class TestGetStatusEmoji:
    def _m(self):
        return _make_monitor()

    def test_completed_success(self):
        m = self._m()
        assert m.get_status_emoji("completed", "success") == "✅"

    def test_completed_failure(self):
        m = self._m()
        assert m.get_status_emoji("completed", "failure") == "❌"

    def test_completed_cancelled(self):
        m = self._m()
        assert m.get_status_emoji("completed", "cancelled") == "🚫"

    def test_completed_skipped(self):
        m = self._m()
        assert m.get_status_emoji("completed", "skipped") == "⏭️"

    def test_completed_unknown_conclusion(self):
        m = self._m()
        assert m.get_status_emoji("completed", "timed_out") == "❓"

    def test_in_progress(self):
        m = self._m()
        assert m.get_status_emoji("in_progress") == "🔄"

    def test_queued(self):
        m = self._m()
        assert m.get_status_emoji("queued") == "⏳"

    def test_unknown_status(self):
        m = self._m()
        assert m.get_status_emoji("unknown_state") == "❓"


class TestGetWorkflowRuns:
    def test_returns_empty_on_request_error(self):
        m = _make_monitor()
        import requests

        with patch("requests.get", side_effect=requests.RequestException("Error")):
            result = m.get_workflow_runs()
        assert result == []

    def test_returns_runs_on_success(self):
        m = _make_monitor()
        mock_response = MagicMock()
        mock_response.json.return_value = {"workflow_runs": [{"id": 1, "name": "CI"}]}
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response):
            result = m.get_workflow_runs()
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_uses_limit_parameter(self):
        m = _make_monitor()
        mock_response = MagicMock()
        mock_response.json.return_value = {"workflow_runs": []}
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response) as mock_get:
            m.get_workflow_runs(limit=5)
        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["params"]["per_page"] == 5


class TestGetRunDetails:
    def test_returns_none_on_error(self):
        m = _make_monitor()
        import requests

        with patch("requests.get", side_effect=requests.RequestException("Error")):
            result = m.get_run_details(12345)
        assert result is None

    def test_returns_run_data_on_success(self):
        m = _make_monitor()
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "status": "completed"}
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response):
            result = m.get_run_details(12345)
        assert result["id"] == 12345


class TestGetRunJobs:
    def test_returns_empty_on_error(self):
        m = _make_monitor()
        import requests

        with patch("requests.get", side_effect=requests.RequestException("Error")):
            result = m.get_run_jobs(12345)
        assert result == []

    def test_returns_jobs_on_success(self):
        m = _make_monitor()
        mock_response = MagicMock()
        mock_response.json.return_value = {"jobs": [{"id": 1, "name": "build"}]}
        mock_response.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_response):
            result = m.get_run_jobs(12345)
        assert len(result) == 1
        assert result[0]["name"] == "build"


class TestDisplayRecentRuns:
    def test_displays_when_no_runs(self, capsys):
        m = _make_monitor()
        with patch.object(m, "get_workflow_runs", return_value=[]):
            m.display_recent_runs()
        out = capsys.readouterr().out
        assert "No runs" in out or "no" in out.lower()
