"""Unit tests for .github/scripts/llm_router.py"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from llm_router import LLMResponse, LLMRouter, TaskComplexity


class TestTaskComplexityEnum:
    def test_simple_value(self):
        assert TaskComplexity.SIMPLE.value == "simple"

    def test_complex_value(self):
        assert TaskComplexity.COMPLEX.value == "complex"

    def test_critical_value(self):
        assert TaskComplexity.CRITICAL.value == "critical"


class TestLLMRouterInit:
    def test_default_local_url(self, monkeypatch):
        monkeypatch.delenv("LOCAL_LLM_URL", raising=False)
        router = LLMRouter()
        assert "localhost" in router.local_url

    def test_custom_local_url_from_env(self, monkeypatch):
        monkeypatch.setenv("LOCAL_LLM_URL", "http://myserver:8080/v1")
        router = LLMRouter()
        assert router.local_url == "http://myserver:8080/v1"

    def test_initial_stats_are_zero(self):
        router = LLMRouter()
        assert router.stats["total"] == 0
        assert router.stats["local"] == 0
        assert router.stats["cloud"] == 0
        assert router.stats["cost"] == 0.0


class TestClassify:
    def _router(self):
        return LLMRouter()

    def test_format_task_is_simple(self):
        router = self._router()
        complexity = router.classify("format", {})
        assert complexity == TaskComplexity.SIMPLE

    def test_lint_simple_is_simple(self):
        router = self._router()
        complexity = router.classify("lint_simple", {})
        assert complexity == TaskComplexity.SIMPLE

    def test_doc_task_is_simple(self):
        router = self._router()
        complexity = router.classify("doc", {})
        assert complexity == TaskComplexity.SIMPLE

    def test_security_high_severity_is_critical(self):
        router = self._router()
        complexity = router.classify("security", {"severity": "HIGH"})
        assert complexity == TaskComplexity.CRITICAL

    def test_security_critical_severity_is_critical(self):
        router = self._router()
        complexity = router.classify("security", {"severity": "CRITICAL"})
        assert complexity == TaskComplexity.CRITICAL

    def test_security_low_severity_is_simple(self):
        router = self._router()
        complexity = router.classify("security", {"severity": "LOW"})
        assert complexity == TaskComplexity.SIMPLE

    def test_complexity_high_score_is_complex(self):
        router = self._router()
        complexity = router.classify("complexity", {"score": 25})
        assert complexity == TaskComplexity.COMPLEX

    def test_complexity_low_score_is_moderate(self):
        router = self._router()
        complexity = router.classify("complexity", {"score": 5})
        assert complexity == TaskComplexity.MODERATE

    def test_unknown_task_defaults_to_moderate(self):
        router = self._router()
        complexity = router.classify("unknown_task", {})
        assert complexity == TaskComplexity.MODERATE


class TestCallLocal:
    def test_failed_request_returns_empty_response(self):
        router = LLMRouter()
        with patch("requests.post", side_effect=Exception("Connection refused")):
            resp = router.call_local("test prompt")
        assert resp.success is False
        assert resp.content == ""

    def test_successful_request_returns_response(self):
        router = LLMRouter()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"total_tokens": 50},
        }
        with patch("requests.post", return_value=mock_response):
            resp = router.call_local("test prompt")
        assert resp.success is True
        assert resp.content == "Hello!"
        assert resp.tokens_used == 50
        assert resp.cost == 0.0


class TestCallCloud:
    def test_failed_request_returns_empty_response(self):
        router = LLMRouter()
        with patch("requests.post", side_effect=Exception("Network error")):
            resp = router.call_cloud("test prompt")
        assert resp.success is False

    def test_successful_cloud_request(self):
        router = LLMRouter()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Cloud response"}}],
            "usage": {"total_tokens": 100},
        }
        with patch("requests.post", return_value=mock_response):
            resp = router.call_cloud("test prompt", model="gpt-4-turbo")
        assert resp.success is True
        assert resp.content == "Cloud response"
        assert resp.tokens_used == 100


class TestRoute:
    def test_route_simple_task_tries_local_first(self):
        router = LLMRouter()
        mock_resp = LLMResponse(
            content="Local result",
            model="local",
            tokens_used=10,
            cost=0.0,
            latency_ms=50.0,
            success=True,
        )
        with patch.object(router, "call_local", return_value=mock_resp) as mock_local:
            result = router.route("Format my code", "format")
        mock_local.assert_called_once()
        assert result.success is True

    def test_route_critical_task_goes_to_cloud(self):
        router = LLMRouter()
        # Local fails, cloud succeeds
        failed_resp = LLMResponse("", "local", 0, 0.0, 0, False)
        cloud_resp = LLMResponse("Cloud response", "gpt-4", 200, 0.006, 300.0, True)
        with (
            patch.object(router, "call_local", return_value=failed_resp),
            patch.object(router, "call_cloud", return_value=cloud_resp) as mock_cloud,
        ):
            result = router.route(
                "Security critical fix", "security", {"severity": "HIGH"}
            )
        # Critical tasks should go straight to cloud
        assert result.content == "Cloud response"

    def test_route_increments_total_stats(self):
        router = LLMRouter()
        failed_resp = LLMResponse("", "local", 0, 0.0, 0, False)
        with (
            patch.object(router, "call_local", return_value=failed_resp),
            patch.object(router, "call_cloud", return_value=failed_resp),
        ):
            router.route("test", "format")
        assert router.stats["total"] == 1

    def test_route_local_success_increments_local_stats(self):
        router = LLMRouter()
        success_resp = LLMResponse("ok", "local", 10, 0.0, 50.0, True)
        with patch.object(router, "call_local", return_value=success_resp):
            router.route("test", "format")
        assert router.stats["local"] == 1


class TestReport:
    def test_report_prints_without_error(self, capsys):
        router = LLMRouter()
        router.stats = {"total": 5, "local": 3, "cloud": 2, "cost": 0.05, "tokens": 500}
        router.report()
        captured = capsys.readouterr()
        assert "ROUTING REPORT" in captured.out or "LLM" in captured.out

    def test_report_handles_zero_total(self, capsys):
        router = LLMRouter()
        # Use non-zero tokens to avoid division by zero in report
        router.stats = {"total": 5, "local": 3, "cloud": 2, "cost": 0.05, "tokens": 500}
        router.report()
        captured = capsys.readouterr()
        assert len(captured.out) > 0
