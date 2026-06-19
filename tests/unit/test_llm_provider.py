"""Unit tests for core/llm_provider.py"""

from __future__ import annotations

import json
from unittest.mock import patch


class TestLLMClientInit:
    def _make_client(self, provider="openai", **kwargs):
        from core.llm_provider import LLMClient

        config = {
            "llm_provider": provider,
            "openai_api_key": "sk-test",
            "anthropic_api_key": "ant-test",
            **kwargs,
        }
        with patch("openai.OpenAI"), patch("anthropic.Anthropic"):
            return LLMClient(config)

    def test_default_provider_is_openai(self):
        client = self._make_client()
        assert client.provider == "openai"

    def test_anthropic_provider_selected(self):
        client = self._make_client(provider="anthropic")
        assert client.provider == "anthropic"

    def test_default_model_for_openai(self):
        client = self._make_client()
        assert client.model == "gpt-4"

    def test_custom_model_respected(self):
        client = self._make_client(model="gpt-4o")
        assert client.model == "gpt-4o"

    def test_initial_token_count_is_zero(self):
        client = self._make_client()
        assert client.total_tokens == 0

    def test_initial_session_cost_is_zero(self):
        client = self._make_client()
        assert client._session_cost_usd == 0.0

    def test_unsupported_provider_raises(self):
        from core.llm_provider import LLMClient, LLMConfigError

        with pytest.raises((LLMConfigError, Exception)):
            with patch("openai.OpenAI"):
                LLMClient({"llm_provider": "unknownllm", "openai_api_key": "x"})

    def test_missing_openai_key_raises_config_error(self):
        from core.llm_provider import LLMClient, LLMConfigError

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(LLMConfigError):
                LLMClient({"llm_provider": "openai"})


import pytest


class TestTokenTracking:
    def _make_client(self):
        from core.llm_provider import LLMClient

        with patch("openai.OpenAI"):
            c = LLMClient({"llm_provider": "openai", "openai_api_key": "sk-test"})
        return c

    def test_reset_token_usage(self):
        client = self._make_client()
        client.total_tokens = 500
        client.reset_token_usage()
        assert client.total_tokens == 0

    def test_get_token_usage_returns_total(self):
        client = self._make_client()
        client.total_tokens = 300
        assert client.get_token_usage() == 300


class TestCostTracking:
    def _make_client(self, model="gpt-4o", tmp_path=None):
        from core.llm_provider import LLMClient

        config = {
            "llm_provider": "openai",
            "openai_api_key": "sk-test",
            "model": model,
        }
        if tmp_path:
            config["llm_costs_file"] = str(tmp_path / ".llm_costs.jsonl")
        with patch("openai.OpenAI"):
            return LLMClient(config)

    def test_record_cost_accumulates(self):
        client = self._make_client()
        client._record_cost(100, 50)
        assert client._session_cost_usd > 0
        assert client._session_input_tokens == 100
        assert client._session_output_tokens == 50

    def test_record_cost_multiple_calls_sum(self):
        client = self._make_client()
        client._record_cost(100, 50)
        first = client._session_cost_usd
        client._record_cost(100, 50)
        assert client._session_cost_usd > first

    def test_get_session_cost_structure(self):
        client = self._make_client()
        client._record_cost(200, 100)
        summary = client.get_session_cost()
        assert summary["model"] == "gpt-4o"
        assert summary["input_tokens"] == 200
        assert summary["output_tokens"] == 100
        assert summary["total_tokens"] == 300
        assert "cost_usd" in summary

    def test_cost_limit_not_exceeded_initially(self):
        client = self._make_client()
        assert client.cost_limit_exceeded(1.0) is False

    def test_cost_limit_exceeded_after_large_call(self):
        client = self._make_client()
        # Force a huge cost manually
        client._session_cost_usd = 5.0
        assert client.cost_limit_exceeded(1.0) is True

    def test_cost_written_to_file(self, tmp_path):
        client = self._make_client(tmp_path=tmp_path)
        client._record_cost(10, 5)
        cost_file = tmp_path / ".llm_costs.jsonl"
        assert cost_file.exists()
        record = json.loads(cost_file.read_text().strip())
        assert record["model"] == "gpt-4o"
        assert record["input_tokens"] == 10
        assert record["output_tokens"] == 5

    def test_unknown_model_uses_default_pricing(self):
        client = self._make_client(model="unknown-model")
        client._record_cost(100, 100)
        # Should not raise, uses default pricing (0.01, 0.03)
        assert client._session_cost_usd > 0


class TestGetDefaultModel:
    def _make_client(self, provider):
        from core.llm_provider import LLMClient

        with patch("openai.OpenAI"), patch("anthropic.Anthropic"):
            return LLMClient(
                {
                    "llm_provider": provider,
                    "openai_api_key": "sk-test",
                    "anthropic_api_key": "ant-test",
                }
            )

    def test_openai_default_model(self):
        client = self._make_client("openai")
        assert client.model == "gpt-4"

    def test_anthropic_default_model(self):
        client = self._make_client("anthropic")
        assert client.model == "claude-3-opus-20240229"
