"""Unit tests for autopilot/staleness_engine.py"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pr(number: int = 1, days_old: int = 5, title: str = "Test PR") -> MagicMock:
    pr = MagicMock()
    pr.number = number
    pr.title = title
    pr.html_url = f"https://github.com/acme/repo/pull/{number}"
    pr.created_at = MagicMock()
    pr.created_at.replace.return_value = datetime.now() - timedelta(days=days_old)
    return pr


def _make_repo_data(pulls: list | None = None) -> dict:
    return {
        "acme/repo": {
            "pulls": pulls or [],
            "issues": [],
            "commits": [],
            "repo_obj": MagicMock(),
            "priority": "critical",
        }
    }


def _make_engine(tmp_path: Path, env: dict | None = None, config: dict | None = None):
    from autopilot.staleness_engine import StalenessEngine

    state_file = tmp_path / "staleness_state.json"
    env = env or {}
    with patch.dict("os.environ", env, clear=False):
        return StalenessEngine(
            config=config or {},
            state_file=state_file,
        )


# ---------------------------------------------------------------------------
# classify_tier (module-level function)
# ---------------------------------------------------------------------------

class TestClassifyTier:
    def test_zero_days_is_t0(self):
        from autopilot.staleness_engine import classify_tier
        assert classify_tier(0) == "T0"

    def test_six_days_is_t0(self):
        from autopilot.staleness_engine import classify_tier
        assert classify_tier(6) == "T0"

    def test_seven_days_is_t1(self):
        from autopilot.staleness_engine import classify_tier
        assert classify_tier(7) == "T1"

    def test_twenty_nine_days_is_t1(self):
        from autopilot.staleness_engine import classify_tier
        assert classify_tier(29) == "T1"

    def test_thirty_days_is_t2(self):
        from autopilot.staleness_engine import classify_tier
        assert classify_tier(30) == "T2"

    def test_eighty_nine_days_is_t2(self):
        from autopilot.staleness_engine import classify_tier
        assert classify_tier(89) == "T2"

    def test_ninety_days_is_t3(self):
        from autopilot.staleness_engine import classify_tier
        assert classify_tier(90) == "T3"

    def test_one_hundred_days_is_t3(self):
        from autopilot.staleness_engine import classify_tier
        assert classify_tier(108) == "T3"


# ---------------------------------------------------------------------------
# StalenessEngine.__init__ / dry-run flag
# ---------------------------------------------------------------------------

class TestDryRunFlag:
    def test_dry_run_true_by_default(self, tmp_path):
        engine = _make_engine(tmp_path, env={})
        assert engine.dry_run is True

    def test_dry_run_false_when_enable_live_mode_true(self, tmp_path):
        engine = _make_engine(tmp_path, env={"ENABLE_LIVE_MODE": "true"})
        assert engine.dry_run is False

    def test_dry_run_still_true_for_other_values(self, tmp_path):
        for val in ("1", "yes", ""):
            engine = _make_engine(tmp_path, env={"ENABLE_LIVE_MODE": val})
            assert engine.dry_run is True, f"Expected dry_run=True for ENABLE_LIVE_MODE={val!r}"

    def test_dry_run_false_for_uppercase_true(self, tmp_path):
        engine = _make_engine(tmp_path, env={"ENABLE_LIVE_MODE": "TRUE"})
        assert engine.dry_run is False


# ---------------------------------------------------------------------------
# Claude call cap
# ---------------------------------------------------------------------------

class TestClaudeCallCap:
    def test_default_cap_is_20(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.max_claude_calls == 20

    def test_env_var_overrides_cap(self, tmp_path):
        engine = _make_engine(tmp_path, env={"MAX_CLAUDE_CALLS_PER_RUN": "5"})
        assert engine.max_claude_calls == 5

    def test_config_key_sets_cap(self, tmp_path):
        engine = _make_engine(tmp_path, config={"max_claude_calls_per_run": 10})
        assert engine.max_claude_calls == 10

    def test_env_var_takes_precedence_over_config(self, tmp_path):
        engine = _make_engine(
            tmp_path,
            env={"MAX_CLAUDE_CALLS_PER_RUN": "3"},
            config={"max_claude_calls_per_run": 15},
        )
        assert engine.max_claude_calls == 3


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

class TestStatePersistence:
    def test_empty_state_when_no_file(self, tmp_path):
        engine = _make_engine(tmp_path)
        state = engine.get_state()
        assert state["schema_version"] == 1
        assert state["prs"] == {}

    def test_loads_existing_state_file(self, tmp_path):
        state_file = tmp_path / "staleness_state.json"
        state_file.write_text(
            json.dumps({"schema_version": 1, "prs": {"acme/repo/42": {"tier": "T2"}}})
        )
        from autopilot.staleness_engine import StalenessEngine

        engine = StalenessEngine(state_file=state_file)
        assert "acme/repo/42" in engine.get_state()["prs"]

    def test_resets_state_on_schema_mismatch(self, tmp_path):
        state_file = tmp_path / "staleness_state.json"
        state_file.write_text(json.dumps({"schema_version": 99, "prs": {"x": {}}}))
        from autopilot.staleness_engine import StalenessEngine

        engine = StalenessEngine(state_file=state_file)
        assert engine.get_state()["prs"] == {}

    def test_save_state_noop_in_dry_run(self, tmp_path):
        engine = _make_engine(tmp_path, env={})
        assert engine.dry_run is True
        engine._save_state()
        assert not engine.state_file.exists()

    def test_save_state_writes_file_in_live_mode(self, tmp_path):
        engine = _make_engine(tmp_path, env={"ENABLE_LIVE_MODE": "true"})
        engine._save_state()
        assert engine.state_file.exists()
        data = json.loads(engine.state_file.read_text())
        assert data["schema_version"] == 1


# ---------------------------------------------------------------------------
# init_state_from_prs
# ---------------------------------------------------------------------------

class TestInitStateFromPrs:
    def test_seeds_prs_without_posting_comments(self, tmp_path):
        engine = _make_engine(tmp_path)
        pr = _make_pr(number=10, days_old=100)
        repo_data = _make_repo_data(pulls=[pr])

        engine.init_state_from_prs(repo_data)

        state = engine.get_state()
        assert "acme/repo/10" in state["prs"]
        entry = state["prs"]["acme/repo/10"]
        assert entry["tier"] == "T3"
        assert entry["last_comment_at"] is None
        assert entry["comment_count"] == 0

    def test_does_not_overwrite_existing_entry(self, tmp_path):
        state_file = tmp_path / "staleness_state.json"
        state_file.write_text(
            json.dumps({
                "schema_version": 1,
                "prs": {
                    "acme/repo/10": {
                        "tier": "T2",
                        "last_escalated_tier": "T2",
                        "comment_count": 1,
                    }
                },
            })
        )
        from autopilot.staleness_engine import StalenessEngine

        engine = StalenessEngine(state_file=state_file)
        pr = _make_pr(number=10, days_old=100)
        engine.init_state_from_prs({"acme/repo": {"pulls": [pr]}})

        entry = engine.get_state()["prs"]["acme/repo/10"]
        # Original entry preserved — not overwritten
        assert entry["tier"] == "T2"
        assert entry["comment_count"] == 1

    def test_state_file_not_written_in_dry_run(self, tmp_path):
        engine = _make_engine(tmp_path, env={})
        pr = _make_pr(number=5, days_old=40)
        engine.init_state_from_prs(_make_repo_data(pulls=[pr]))
        assert not engine.state_file.exists()


# ---------------------------------------------------------------------------
# process_prs
# ---------------------------------------------------------------------------

class TestProcessPrs:
    def test_no_actions_when_no_prs(self, tmp_path):
        engine = _make_engine(tmp_path)
        actions = engine.process_prs(_make_repo_data(pulls=[]))
        assert actions == []

    def test_new_pr_seeded_without_escalation(self, tmp_path):
        engine = _make_engine(tmp_path)
        pr = _make_pr(number=1, days_old=50)
        actions = engine.process_prs(_make_repo_data(pulls=[pr]))
        # Brand-new PR — no escalation on first observation
        assert actions == []
        assert "acme/repo/1" in engine.get_state()["prs"]

    def test_tier_increase_triggers_escalation(self, tmp_path):
        state_file = tmp_path / "staleness_state.json"
        state_file.write_text(
            json.dumps({
                "schema_version": 1,
                "prs": {
                    "acme/repo/7": {
                        "tier": "T1",
                        "days_open": 20,
                        "last_escalated_tier": "T1",
                        "last_comment_at": None,
                        "comment_count": 0,
                    }
                },
            })
        )
        from autopilot.staleness_engine import StalenessEngine

        engine = StalenessEngine(state_file=state_file)
        # PR is now 35 days old → T2
        pr = _make_pr(number=7, days_old=35)
        actions = engine.process_prs(_make_repo_data(pulls=[pr]))
        assert len(actions) == 1
        assert actions[0]["tier"] == "T2"
        assert actions[0]["dry_run"] is True
        assert actions[0]["posted"] is False

    def test_no_escalation_when_tier_unchanged(self, tmp_path):
        state_file = tmp_path / "staleness_state.json"
        state_file.write_text(
            json.dumps({
                "schema_version": 1,
                "prs": {
                    "acme/repo/3": {
                        "tier": "T2",
                        "days_open": 31,
                        "last_escalated_tier": "T2",
                        "last_comment_at": None,
                        "comment_count": 0,
                    }
                },
            })
        )
        from autopilot.staleness_engine import StalenessEngine

        engine = StalenessEngine(state_file=state_file)
        pr = _make_pr(number=3, days_old=40)  # Still T2
        actions = engine.process_prs(_make_repo_data(pulls=[pr]))
        assert actions == []

    def test_no_escalation_when_tier_decreases(self, tmp_path):
        """Tier should never decrease for open PRs, but guard against it."""
        state_file = tmp_path / "staleness_state.json"
        state_file.write_text(
            json.dumps({
                "schema_version": 1,
                "prs": {
                    "acme/repo/9": {
                        "tier": "T3",
                        "days_open": 100,
                        "last_escalated_tier": "T3",
                        "last_comment_at": None,
                        "comment_count": 0,
                    }
                },
            })
        )
        from autopilot.staleness_engine import StalenessEngine

        engine = StalenessEngine(state_file=state_file)
        pr = _make_pr(number=9, days_old=10)  # Would be T1, but last_escalated was T3
        actions = engine.process_prs(_make_repo_data(pulls=[pr]))
        assert actions == []


# ---------------------------------------------------------------------------
# Static comment templates
# ---------------------------------------------------------------------------

class TestStaticComment:
    def _make_pr_obj(self, number=1):
        pr = MagicMock()
        pr.number = number
        pr.title = "Add feature X"
        pr.html_url = f"https://github.com/acme/repo/pull/{number}"
        return pr

    def test_t1_comment_mentions_aging(self, tmp_path):
        from autopilot.staleness_engine import StalenessEngine

        engine = _make_engine(tmp_path)
        pr = self._make_pr_obj()
        comment = engine._static_comment(pr, "T1", "aging", "🟡", 10)
        assert "aging" in comment.lower() or "🟡" in comment
        assert "10" in comment

    def test_t2_comment_mentions_stale(self, tmp_path):
        from autopilot.staleness_engine import StalenessEngine

        engine = _make_engine(tmp_path)
        pr = self._make_pr_obj()
        comment = engine._static_comment(pr, "T2", "stale", "🟠", 45)
        assert "stale" in comment.lower() or "⚠" in comment
        assert "45" in comment

    def test_t3_comment_mentions_critical(self, tmp_path):
        from autopilot.staleness_engine import StalenessEngine

        engine = _make_engine(tmp_path)
        pr = self._make_pr_obj()
        comment = engine._static_comment(pr, "T3", "critical", "🔴", 100)
        assert "critical" in comment.lower() or "🚨" in comment
        assert "100" in comment


# ---------------------------------------------------------------------------
# _post_comment — dry-run safety
# ---------------------------------------------------------------------------

class TestPostComment:
    def test_returns_false_when_repo_obj_none(self, tmp_path):
        engine = _make_engine(tmp_path, env={"ENABLE_LIVE_MODE": "true"})
        pr = _make_pr()
        result = engine._post_comment(None, pr, "hello")
        assert result is False

    def test_posts_comment_in_live_mode(self, tmp_path):
        engine = _make_engine(tmp_path, env={"ENABLE_LIVE_MODE": "true"})
        mock_repo = MagicMock()
        mock_pull = MagicMock()
        mock_repo.get_pull.return_value = mock_pull
        pr = _make_pr(number=42)

        result = engine._post_comment(mock_repo, pr, "Escalation notice")

        assert result is True
        mock_repo.get_pull.assert_called_once_with(42)
        mock_pull.create_issue_comment.assert_called_once_with("Escalation notice")

    def test_returns_false_on_github_exception(self, tmp_path):
        from github import GithubException

        engine = _make_engine(tmp_path, env={"ENABLE_LIVE_MODE": "true"})
        mock_repo = MagicMock()
        mock_repo.get_pull.side_effect = GithubException(403, {"message": "Forbidden"})
        pr = _make_pr(number=5)

        result = engine._post_comment(mock_repo, pr, "notice")
        assert result is False


# ---------------------------------------------------------------------------
# _generate_comment — falls back to static when llm_config absent
# ---------------------------------------------------------------------------

class TestGenerateComment:
    def test_uses_static_when_no_llm_config(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.llm_config is None
        pr = _make_pr(number=1, days_old=95)
        comment = engine._generate_comment(pr, "T3", "critical", "🔴", 95)
        assert "95" in comment

    def test_uses_static_when_cap_reached(self, tmp_path):
        engine = _make_engine(tmp_path, config={"max_claude_calls_per_run": 0})
        engine.llm_config = {"llm_provider": "anthropic"}  # set but cap=0
        pr = _make_pr(number=2, days_old=40)
        comment = engine._generate_comment(pr, "T2", "stale", "🟠", 40)
        assert "40" in comment


# ---------------------------------------------------------------------------
# Escalate — dry_run suppresses posting
# ---------------------------------------------------------------------------

class TestEscalate:
    def _setup_engine_with_entry(self, tmp_path, pr_key: str, last_tier: str):
        state_file = tmp_path / "staleness_state.json"
        state_file.write_text(
            json.dumps({
                "schema_version": 1,
                "prs": {
                    pr_key: {
                        "tier": last_tier,
                        "days_open": 20,
                        "last_escalated_tier": last_tier,
                        "last_comment_at": None,
                        "comment_count": 0,
                    }
                },
            })
        )
        from autopilot.staleness_engine import StalenessEngine

        return StalenessEngine(state_file=state_file)

    def test_dry_run_does_not_post_comment(self, tmp_path):
        engine = self._setup_engine_with_entry(tmp_path, "acme/repo/1", "T1")
        assert engine.dry_run is True
        pr = _make_pr(number=1, days_old=35)
        mock_repo = MagicMock()

        action = engine._escalate("acme/repo/1", pr, "T2", 35, mock_repo)

        assert action["posted"] is False
        assert action["dry_run"] is True
        mock_repo.get_pull.assert_not_called()

    def test_live_mode_posts_and_updates_entry(self, tmp_path):
        engine = self._setup_engine_with_entry(tmp_path, "acme/repo/2", "T1")
        engine.dry_run = False  # Force live mode directly
        pr = _make_pr(number=2, days_old=35)
        mock_repo = MagicMock()
        mock_pull = MagicMock()
        mock_repo.get_pull.return_value = mock_pull

        action = engine._escalate("acme/repo/2", pr, "T2", 35, mock_repo)

        assert action["posted"] is True
        mock_pull.create_issue_comment.assert_called_once()

        entry = engine.get_state()["prs"]["acme/repo/2"]
        assert entry["last_escalated_tier"] == "T2"
        assert entry["comment_count"] == 1
        assert entry["last_comment_at"] is not None


# ---------------------------------------------------------------------------
# StalenessEngine.classify_tier method delegates to module function
# ---------------------------------------------------------------------------

class TestClassifyTierMethod:
    def test_method_matches_module_function(self, tmp_path):
        from autopilot.staleness_engine import classify_tier

        engine = _make_engine(tmp_path)
        for days in [0, 6, 7, 29, 30, 89, 90, 120]:
            assert engine.classify_tier(days) == classify_tier(days)
