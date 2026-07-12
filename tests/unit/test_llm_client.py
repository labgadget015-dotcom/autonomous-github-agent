"""Tests for the unified LLM client (core/llm_client.py)."""

from unittest.mock import MagicMock, patch

import pytest

from autonomous_agent.core.llm_client import LLMClient


def _config(provider="openai", api_key="sk-test", model="gpt-4-turbo-preview"):
    cfg = MagicMock()
    cfg.llm.provider = provider
    cfg.llm.api_key = api_key
    cfg.llm.model = model
    cfg.llm.temperature = 0.2
    cfg.llm.max_tokens = 4000
    return cfg


@patch("autonomous_agent.core.llm_client.get_config")
@patch("autonomous_agent.core.llm_client.OpenAI")
def test_init_openai_provider(mock_openai, mock_get_config):
    mock_get_config.return_value = _config(provider="openai")
    client = LLMClient()
    assert client.provider == "openai"
    mock_openai.assert_called_once_with(api_key="sk-test")


@patch("autonomous_agent.core.llm_client.get_config")
@patch("autonomous_agent.core.llm_client.Anthropic")
def test_init_anthropic_provider(mock_anthropic, mock_get_config):
    mock_get_config.return_value = _config(provider="anthropic", api_key="sk-ant")
    client = LLMClient()
    assert client.provider == "anthropic"
    mock_anthropic.assert_called_once_with(api_key="sk-ant")


@patch("autonomous_agent.core.llm_client.get_config")
def test_init_unsupported_provider_raises(mock_get_config):
    mock_get_config.return_value = _config(provider="watson")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMClient()


@patch("autonomous_agent.core.llm_client.get_config")
@patch("autonomous_agent.core.llm_client.OpenAI")
def test_complete_openai_with_and_without_system(mock_openai, mock_get_config):
    mock_get_config.return_value = _config(provider="openai")
    fake = MagicMock()
    fake.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="hello"))
    ]
    mock_openai.return_value = fake

    client = LLMClient()

    # With system prompt
    out = client.complete("explain", system="be terse")
    assert out == "hello"
    msgs = fake.chat.completions.create.call_args.kwargs["messages"]
    assert msgs[0] == {"role": "system", "content": "be terse"}
    assert msgs[1] == {"role": "user", "content": "explain"}

    # Without system prompt
    out2 = client.complete("explain")
    assert out2 == "hello"
    msgs2 = fake.chat.completions.create.call_args.kwargs["messages"]
    assert msgs2[0] == {"role": "user", "content": "explain"}


@patch("autonomous_agent.core.llm_client.get_config")
@patch("autonomous_agent.core.llm_client.Anthropic")
def test_complete_anthropic_branch(mock_anthropic, mock_get_config):
    mock_get_config.return_value = _config(provider="anthropic", api_key="sk-ant")
    fake = MagicMock()
    content_block = MagicMock()
    content_block.text = "anthropic reply"
    fake.messages.create.return_value.content = [content_block]
    mock_anthropic.return_value = fake

    client = LLMClient()
    out = client.complete("do thing", system="sys")
    assert out == "anthropic reply"
    call = fake.messages.create.call_args.kwargs
    assert call["system"] == "sys"
    assert call["messages"] == [{"role": "user", "content": "do thing"}]


@patch("autonomous_agent.core.llm_client.get_config")
@patch("autonomous_agent.core.llm_client.OpenAI")
def test_analyze_code_builds_prompt(mock_openai, mock_get_config):
    mock_get_config.return_value = _config(provider="openai")
    fake = MagicMock()
    fake.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="reviewed"))
    ]
    mock_openai.return_value = fake

    client = LLMClient()
    out = client.analyze_code("print(1)", "find bugs")
    assert out == "reviewed"
    prompt = fake.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "find bugs" in prompt
    assert "print(1)" in prompt
