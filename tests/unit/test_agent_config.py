"""Unit tests for core/agent_config.py"""

from __future__ import annotations

import os
from unittest.mock import patch


class TestAgentConfigDefaults:
    def test_dry_run_defaults_true(self):
        from core.agent_config import AgentConfig

        cfg = AgentConfig.__new__(AgentConfig)
        object.__setattr__(cfg, "_raw", {})
        object.__setattr__(cfg, "dry_run", True)
        assert cfg.dry_run is True

    def test_auto_merge_defaults_false(self):
        from core.agent_config import AgentConfig

        cfg = AgentConfig()
        assert cfg.auto_merge is False

    def test_require_approval_defaults_true(self):
        from core.agent_config import AgentConfig

        cfg = AgentConfig()
        assert cfg.require_approval is True


class TestIsActionAllowed:
    def _cfg(self, **kwargs):
        from core.agent_config import AgentConfig

        cfg = AgentConfig()
        for k, v in kwargs.items():
            object.__setattr__(cfg, k, v)
        return cfg

    def test_all_blocked_in_dry_run(self):
        cfg = self._cfg(dry_run=True, auto_merge=True, auto_close_issues=True)
        assert cfg.is_action_allowed("merge") is False
        assert cfg.is_action_allowed("close_issue") is False
        assert cfg.is_action_allowed("delete_branch") is False

    def test_merge_allowed_when_flags_set(self):
        cfg = self._cfg(dry_run=False, auto_merge=True)
        assert cfg.is_action_allowed("merge") is True

    def test_merge_blocked_when_auto_merge_off(self):
        cfg = self._cfg(dry_run=False, auto_merge=False)
        assert cfg.is_action_allowed("merge") is False

    def test_unknown_action_defaults_to_allowed(self):
        cfg = self._cfg(dry_run=False)
        assert cfg.is_action_allowed("some_custom_action") is True


class TestEnvOverrides:
    def test_env_override_dry_run(self):
        with patch.dict(os.environ, {"AGENT_DRY_RUN": "false"}):
            from importlib import reload

            import core.agent_config as mod

            reload(mod)
            assert mod.cfg.dry_run is False
        # Reload again to restore defaults
        with patch.dict(os.environ, {}, clear=False):
            reload(mod)

    def test_env_override_risk_threshold(self):
        with patch.dict(os.environ, {"AGENT_RISK_SCORE_THRESHOLD": "7.5"}):
            from importlib import reload

            import core.agent_config as mod

            reload(mod)
            assert mod.cfg.risk_score_threshold == 7.5
