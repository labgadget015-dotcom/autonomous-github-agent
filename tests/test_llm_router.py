"""Tests for llm_router.py — LLM routing and Claude integration."""
import os
import sys
import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.github', 'scripts'))

from llm_router import LLMRouter, LLMResponse, TaskComplexity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def router(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-ant-test')
    monkeypatch.setenv('LOCAL_LLM_URL', 'http://localhost:1234/v1')
    return LLMRouter()


def _make_usage(input_tokens=100, output_tokens=50, cache_read=0, cache_write=0):
    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    usage.cache_read_input_tokens = cache_read
    usage.cache_creation_input_tokens = cache_write
    return usage


def _make_message(text="ok", input_tokens=100, output_tokens=50, cache_read=0, cache_write=0):
    block = MagicMock()
    block.type = "text"
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    msg.usage = _make_usage(input_tokens, output_tokens, cache_read, cache_write)
    return msg


# ---------------------------------------------------------------------------
# classify()
# ---------------------------------------------------------------------------

class TestClassify:
    def test_format_is_simple(self, router):
        assert router.classify('format', {}) == TaskComplexity.SIMPLE

    def test_lint_simple_is_simple(self, router):
        assert router.classify('lint_simple', {}) == TaskComplexity.SIMPLE

    def test_doc_is_simple(self, router):
        assert router.classify('doc', {}) == TaskComplexity.SIMPLE

    def test_security_high_is_critical(self, router):
        assert router.classify('security', {'severity': 'HIGH'}) == TaskComplexity.CRITICAL

    def test_security_critical_is_critical(self, router):
        assert router.classify('security', {'severity': 'CRITICAL'}) == TaskComplexity.CRITICAL

    def test_security_low_is_simple(self, router):
        assert router.classify('security', {'severity': 'LOW'}) == TaskComplexity.SIMPLE

    def test_security_medium_is_simple(self, router):
        assert router.classify('security', {'severity': 'MEDIUM'}) == TaskComplexity.SIMPLE

    def test_security_defaults_to_simple(self, router):
        assert router.classify('security', {}) == TaskComplexity.SIMPLE

    def test_complexity_high_score_is_complex(self, router):
        assert router.classify('complexity', {'score': 25}) == TaskComplexity.COMPLEX

    def test_complexity_low_score_is_moderate(self, router):
        assert router.classify('complexity', {'score': 10}) == TaskComplexity.MODERATE

    def test_complexity_boundary_score_is_moderate(self, router):
        assert router.classify('complexity', {'score': 20}) == TaskComplexity.MODERATE

    def test_unknown_task_is_moderate(self, router):
        assert router.classify('refactor', {}) == TaskComplexity.MODERATE


# ---------------------------------------------------------------------------
# call_local()
# ---------------------------------------------------------------------------

class TestCallLocal:
    def test_successful_local_call(self, router):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'fixed code'}}],
            'usage': {'total_tokens': 42}
        }
        with patch('requests.post', return_value=mock_response):
            result = router.call_local('fix this')

        assert result.success is True
        assert result.content == 'fixed code'
        assert result.tokens_used == 42
        assert result.cost == 0.0
        assert result.model == 'local-llama-70b'

    def test_local_call_no_usage_field(self, router):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'done'}}]
        }
        with patch('requests.post', return_value=mock_response):
            result = router.call_local('prompt')

        assert result.success is True
        assert result.tokens_used == 0

    def test_local_call_network_error(self, router):
        with patch('requests.post', side_effect=Exception('connection refused')):
            result = router.call_local('prompt')

        assert result.success is False
        assert result.content == ''
        assert result.cost == 0.0


# ---------------------------------------------------------------------------
# call_claude()
# ---------------------------------------------------------------------------

class TestCallClaude:
    def test_successful_claude_call(self, router):
        msg = _make_message("great code", input_tokens=200, output_tokens=100)
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.get_final_message.return_value = msg

        with patch('anthropic.Anthropic') as MockClient:
            MockClient.return_value.messages.stream.return_value = mock_stream
            result = router.call_claude('review this', TaskComplexity.COMPLEX)

        assert result.success is True
        assert result.content == 'great code'
        assert result.model == 'claude-opus-4-6'
        assert result.tokens_used == 300
        assert result.cost > 0

    def test_critical_complexity_adds_thinking_param(self, router):
        msg = _make_message("analysis", input_tokens=500, output_tokens=200)
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.get_final_message.return_value = msg

        with patch('anthropic.Anthropic') as MockClient:
            mock_messages = MockClient.return_value.messages
            mock_messages.stream.return_value = mock_stream
            router.call_claude('security review', TaskComplexity.CRITICAL)

            call_kwargs = mock_messages.stream.call_args[1]
            assert 'thinking' in call_kwargs
            assert call_kwargs['thinking'] == {'type': 'adaptive'}

    def test_non_critical_has_no_thinking_param(self, router):
        msg = _make_message()
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.get_final_message.return_value = msg

        with patch('anthropic.Anthropic') as MockClient:
            mock_messages = MockClient.return_value.messages
            mock_messages.stream.return_value = mock_stream
            router.call_claude('refactor', TaskComplexity.COMPLEX)

            call_kwargs = mock_messages.stream.call_args[1]
            assert 'thinking' not in call_kwargs

    def test_cache_tokens_tracked(self, router):
        msg = _make_message(cache_read=1000, cache_write=500)
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.get_final_message.return_value = msg

        with patch('anthropic.Anthropic') as MockClient:
            MockClient.return_value.messages.stream.return_value = mock_stream
            router.call_claude('prompt', TaskComplexity.COMPLEX)

        assert router.stats['cache_read_tokens'] == 1000
        assert router.stats['cache_write_tokens'] == 500

    def test_claude_api_failure_returns_failed_response(self, router):
        with patch('anthropic.Anthropic') as MockClient:
            MockClient.return_value.messages.stream.side_effect = Exception('API error')
            result = router.call_claude('prompt', TaskComplexity.COMPLEX)

        assert result.success is False
        assert result.content == ''
        assert result.model == 'claude-opus-4-6'

    def test_system_prompt_uses_cache_control(self, router):
        msg = _make_message()
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.get_final_message.return_value = msg

        with patch('anthropic.Anthropic') as MockClient:
            mock_messages = MockClient.return_value.messages
            mock_messages.stream.return_value = mock_stream
            router.call_claude('prompt', TaskComplexity.COMPLEX)

            call_kwargs = mock_messages.stream.call_args[1]
            system = call_kwargs['system']
            assert isinstance(system, list)
            assert system[0]['cache_control'] == {'type': 'ephemeral'}


# ---------------------------------------------------------------------------
# route()
# ---------------------------------------------------------------------------

class TestRoute:
    def test_simple_task_tries_local_first(self, router):
        local_resp = LLMResponse('result', 'local-llama-70b', 10, 0.0, 50.0, True)
        with patch.object(router, 'call_local', return_value=local_resp) as mock_local:
            result = router.route('fix formatting', 'format')

        mock_local.assert_called_once()
        assert result.model == 'local-llama-70b'
        assert router.stats['local'] == 1
        assert router.stats['total'] == 1

    def test_local_failure_escalates_to_claude(self, router):
        failed = LLMResponse('', 'local', 0, 0.0, 0, False)
        cloud_resp = LLMResponse('analysis', 'claude-opus-4-6', 300, 0.005, 1200.0, True)
        with patch.object(router, 'call_local', return_value=failed), \
             patch.object(router, 'call_claude', return_value=cloud_resp) as mock_claude:
            result = router.route('moderate task', 'refactor')

        mock_claude.assert_called_once()
        assert result.model == 'claude-opus-4-6'
        assert router.stats['cloud'] == 1

    def test_critical_task_goes_directly_to_claude(self, router):
        cloud_resp = LLMResponse('vuln found', 'claude-opus-4-6', 500, 0.01, 2000.0, True)
        with patch.object(router, 'call_local') as mock_local, \
             patch.object(router, 'call_claude', return_value=cloud_resp) as mock_claude:
            result = router.route('high severity vuln', 'security', {'severity': 'HIGH'})

        mock_local.assert_not_called()
        mock_claude.assert_called_once_with('high severity vuln', TaskComplexity.CRITICAL)
        assert result.content == 'vuln found'

    def test_stats_accumulate_across_calls(self, router):
        local_resp = LLMResponse('ok', 'local-llama-70b', 10, 0.0, 30.0, True)
        cloud_resp = LLMResponse('analysis', 'claude-opus-4-6', 300, 0.005, 1200.0, True)
        with patch.object(router, 'call_local', return_value=local_resp), \
             patch.object(router, 'call_claude', return_value=cloud_resp):
            router.route('format', 'format')
            router.route('security', 'security', {'severity': 'HIGH'})

        assert router.stats['total'] == 2
        assert router.stats['local'] == 1
        assert router.stats['cloud'] == 1

    def test_context_defaults_to_empty_dict(self, router):
        local_resp = LLMResponse('ok', 'local', 0, 0.0, 0, True)
        with patch.object(router, 'call_local', return_value=local_resp):
            # Should not raise even with no context arg
            result = router.route('fix lint', 'format')
        assert result is not None


# ---------------------------------------------------------------------------
# report()
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_with_no_calls(self, router, capsys):
        router.report()
        out = capsys.readouterr().out
        assert 'LLM ROUTING REPORT' in out
        assert 'Requests: 0' in out

    def test_report_with_cloud_calls(self, router, capsys):
        router.stats['total'] = 2
        router.stats['cloud'] = 2
        router.stats['tokens'] = 1000
        router.stats['cost'] = 0.01
        router.stats['cache_read_tokens'] = 500
        router.stats['cache_write_tokens'] = 200
        router.report()
        out = capsys.readouterr().out
        assert 'SAVINGS' in out
        assert '500' in out  # cache reads
        assert '200' in out  # cache writes
