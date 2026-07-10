"""Tests for the CLI (autonomous_agent/cli.py) — focuses on branch coverage."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from autonomous_agent.cli import main


def _config(token="ghp_abc", provider="openai", api_key="sk-test",
            automation="semi-auto", agents=("health", "review")):
    cfg = MagicMock()
    cfg.github.token = token
    cfg.llm.provider = provider
    cfg.llm.api_key = api_key
    cfg.automation_level = automation
    cfg.enabled_agents = list(agents)
    return cfg


def test_config_check_token_set():
    runner = CliRunner()
    with patch("autonomous_agent.cli.get_config", return_value=_config(token="ghp_xyz")):
        result = runner.invoke(main, ["config-check"])
    assert result.exit_code == 0
    assert "GitHub Token" in result.output
    assert "✓ Set" in result.output


def test_config_check_token_missing():
    runner = CliRunner()
    with patch("autonomous_agent.cli.get_config", return_value=_config(token="")):
        result = runner.invoke(main, ["config-check"])
    assert result.exit_code == 0
    assert "GitHub token not configured" in result.output


def test_list_agents():
    runner = CliRunner()
    result = runner.invoke(main, ["list-agents"])
    assert result.exit_code == 0
    assert "health_monitor" in result.output
    assert "code_reviewer" in result.output
    assert "security_scanner" in result.output


def test_version_option():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
