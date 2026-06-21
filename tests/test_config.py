"""Tests for configuration module."""

from autonomous_agent.core.config import Config


def test_config_initialization():
    """Test config can be initialized."""
    config = Config(
        github={"token": "test_token"},
        llm={"provider": "openai", "api_key": "test_key"},
    )

    assert config.github.token == "test_token"
    assert config.llm.provider == "openai"


def test_automation_levels():
    """Test automation level options."""
    for level in ["manual", "semi-auto", "full-auto"]:
        config = Config(github={"token": "test"}, automation_level=level)
        assert config.automation_level == level
