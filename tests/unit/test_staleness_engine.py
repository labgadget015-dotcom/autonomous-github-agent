"""Unit tests for autopilot/staleness_engine.py"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_engine(tmp_path, dry_run=True, max_llm_calls=20, token="tok"):
    from autopilot.staleness_engine import StalenessEngine

    config = {
        "repos": [{"owner": "acme", "name": "repo"}],
    }
    mock_gh = MagicMock()
    with (
        patch("autopilot.staleness_engine.Github", return_value=mock_gh),
        patch.dict("os.environ", {"GITHUB_TOKEN": token}),
    ):
        engine = StalenessEngine(
            config=config,
            dry_run=dry_run,
            max_llm_calls=max_llm_calls,
            state_file=tmp_path / "staleness_state.json",
        )
    engine._github = mock_gh
    return engine


def _make_pr(number=1, title="Test PR", days_old=10, html_url="http://example.com/1"):
    pr = MagicMock()
    pr.number = number
    pr.title = title
    pr.html_url = html_url
    pr.created_at = datetime.now(timezone.utc) - timedelta(days=days_old)
    return pr


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestStalenessEngineInit:
    def test_requires_github_token(self, tmp_path):
        from autopilot.staleness_engine import StalenessEngine

        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="GITHUB_TOKEN"),
        ):
            StalenessEngine(config={}, state_file=tmp_path / "s.json")

    def test_dry_run_default(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.dry_run is True

    def test_live_mode_via_env(self, tmp_path):
        from autopilot.staleness_engine import StalenessEngine

        mock_gh = MagicMock()
        with (
            patch("autopilot.staleness_engine.Github", return_value=mock_gh),
            patch.dict("os.environ", {"GITHUB_TOKEN": "tok", "ENABLE_LIVE_MODE": "true"}),
        ):
            engine = StalenessEngine(
                config={},
                state_file=tmp_path / "s.json",
            )
        assert engine.dry_run is False

    def test_dry_run_explicit_false(self, tmp_path):
        engine = _make_engine(tmp_path, dry_run=False)
        assert engine.dry_run is False

    def test_tiers_sorted_descending(self, tmp_path):
        engine = _make_engine(tmp_path)
        days = [t["min_days"] for t in engine.tiers]
        assert days == sorted(days, reverse=True)


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------


class TestStateIO:
    def test_load_returns_empty_when_missing(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.load_state() == {}

    def test_save_and_load_roundtrip(self, tmp_path):
        engine = _make_engine(tmp_path)
        data = {"acme/repo#1": {"tier": 2, "last_comment_at": None}}
        engine.save_state(data)
        assert engine.load_state() == data

    def test_load_returns_empty_on_corrupt_json(self, tmp_path):
        engine = _make_engine(tmp_path)
        engine.state_file.write_text("not json", encoding="utf-8")
        assert engine.load_state() == {}

    def test_save_failure_is_logged_not_raised(self, tmp_path, caplog):
        engine = _make_engine(tmp_path)
        engine.state_file = Path("/nonexistent_dir/state.json")
        import logging

        with caplog.at_level(logging.ERROR, logger="autopilot.staleness_engine"):
            engine.save_state({"x": 1})  # should not raise
        assert "Failed to save staleness state" in caplog.text


# ---------------------------------------------------------------------------
# Tier assignment
# ---------------------------------------------------------------------------


class TestAssignTier:
    def test_tier_0_for_fresh_pr(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.assign_tier(0) == 0
        assert engine.assign_tier(6) == 0

    def test_tier_1_at_boundary(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.assign_tier(7) == 1
        assert engine.assign_tier(30) == 1

    def test_tier_2_at_boundary(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.assign_tier(31) == 2
        assert engine.assign_tier(60) == 2

    def test_tier_3_at_boundary(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.assign_tier(61) == 3
        assert engine.assign_tier(200) == 3

    def test_custom_tiers_respected(self, tmp_path):
        from autopilot.staleness_engine import StalenessEngine

        mock_gh = MagicMock()
        config = {
            "tiers": [
                {"tier": 1, "min_days": 14, "label": "old", "template": "tier1"},
            ]
        }
        with (
            patch("autopilot.staleness_engine.Github", return_value=mock_gh),
            patch.dict("os.environ", {"GITHUB_TOKEN": "t"}),
        ):
            engine = StalenessEngine(
                config=config, dry_run=True, state_file=tmp_path / "s.json"
            )
        assert engine.assign_tier(13) == 0
        assert engine.assign_tier(14) == 1


# ---------------------------------------------------------------------------
# Comment generation
# ---------------------------------------------------------------------------


class TestGenerateComment:
    def test_returns_template_text(self, tmp_path):
        engine = _make_engine(tmp_path)
        comment = engine.generate_comment(age_days=35, tier=2)
        assert "35 days" in comment
        assert "⚠️" in comment

    def test_tier3_template(self, tmp_path):
        engine = _make_engine(tmp_path)
        comment = engine.generate_comment(age_days=65, tier=3)
        assert "🚨" in comment
        assert "65 days" in comment

    def test_tier1_template(self, tmp_path):
        engine = _make_engine(tmp_path)
        comment = engine.generate_comment(age_days=10, tier=1)
        assert "👋" in comment
        assert "10 days" in comment

    def test_llm_used_when_client_provided(self, tmp_path):
        engine = _make_engine(tmp_path, max_llm_calls=5)
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(
            return_value={"content": "LLM comment", "usage": {"total_tokens": 100}}
        )
        comment = engine.generate_comment(
            age_days=10, tier=1, llm_client=mock_llm, pr_title="My PR", repo_full_name="a/b"
        )
        assert comment == "LLM comment"
        assert engine._llm_calls_used == 1

    def test_llm_not_called_when_budget_exhausted(self, tmp_path):
        engine = _make_engine(tmp_path, max_llm_calls=0)
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value={"content": "LLM comment"})
        comment = engine.generate_comment(age_days=10, tier=1, llm_client=mock_llm)
        mock_llm.generate.assert_not_called()
        assert engine._llm_calls_used == 0
        assert "👋" in comment  # fell back to template

    def test_llm_failure_falls_back_to_template(self, tmp_path):
        engine = _make_engine(tmp_path, max_llm_calls=5)
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=Exception("network error"))
        comment = engine.generate_comment(
            age_days=20, tier=1, llm_client=mock_llm
        )
        assert "👋" in comment  # template fallback


# ---------------------------------------------------------------------------
# scan_repos
# ---------------------------------------------------------------------------


class TestScanRepos:
    def test_returns_stale_prs(self, tmp_path):
        engine = _make_engine(tmp_path)
        pr = _make_pr(days_old=40)
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = [pr]
        engine._github.get_repo.return_value = mock_repo

        stale = engine.scan_repos([{"owner": "acme", "name": "repo"}])
        assert len(stale) == 1
        assert stale[0]["tier"] == 2
        assert stale[0]["age_days"] == 40

    def test_skips_fresh_prs(self, tmp_path):
        engine = _make_engine(tmp_path)
        pr = _make_pr(days_old=3)
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = [pr]
        engine._github.get_repo.return_value = mock_repo

        stale = engine.scan_repos([{"owner": "acme", "name": "repo"}])
        assert stale == []

    def test_skips_repo_on_github_exception(self, tmp_path, caplog):
        from github import GithubException

        engine = _make_engine(tmp_path)
        engine._github.get_repo.side_effect = GithubException(403, {"message": "Forbidden"})

        import logging

        with caplog.at_level(logging.WARNING, logger="autopilot.staleness_engine"):
            stale = engine.scan_repos([{"owner": "acme", "name": "private"}])
        assert stale == []
        assert "Skipping" in caplog.text

    def test_skips_repo_on_unexpected_exception(self, tmp_path, caplog):
        engine = _make_engine(tmp_path)
        engine._github.get_repo.side_effect = RuntimeError("boom")

        import logging

        with caplog.at_level(logging.WARNING, logger="autopilot.staleness_engine"):
            stale = engine.scan_repos([{"owner": "acme", "name": "repo"}])
        assert stale == []

    def test_multiple_repos(self, tmp_path):
        engine = _make_engine(tmp_path)
        pr_stale = _make_pr(days_old=100, number=1)
        pr_fresh = _make_pr(days_old=2, number=2)

        mock_repo_a = MagicMock()
        mock_repo_a.get_pulls.return_value = [pr_stale]
        mock_repo_b = MagicMock()
        mock_repo_b.get_pulls.return_value = [pr_fresh]
        engine._github.get_repo.side_effect = [mock_repo_a, mock_repo_b]

        stale = engine.scan_repos(
            [{"owner": "acme", "name": "a"}, {"owner": "acme", "name": "b"}]
        )
        assert len(stale) == 1
        assert stale[0]["pr_number"] == 1


# ---------------------------------------------------------------------------
# process_stale_prs
# ---------------------------------------------------------------------------


class TestProcessStalePRs:
    def _make_stale_pr(self, repo="acme/repo", number=1, age=40, tier=2):
        return {
            "repo_full_name": repo,
            "pr_number": number,
            "pr_title": "Test PR",
            "pr_url": "http://example.com/1",
            "age_days": age,
            "tier": tier,
        }

    def test_initializes_state_on_first_encounter(self, tmp_path):
        engine = _make_engine(tmp_path, dry_run=True)
        stale = [self._make_stale_pr()]
        summary = engine.process_stale_prs(stale)
        assert summary["state_initialized"] == 1
        assert summary["dry_run_previews"] == 0
        state = engine.load_state()
        assert "acme/repo#1" in state

    def test_dry_run_previews_comment_on_tier_advance(self, tmp_path):
        engine = _make_engine(tmp_path, dry_run=True)
        # PR is now tier 2 but only a tier-1 comment has been posted — expect a preview
        engine.save_state(
            {
                "acme/repo#1": {
                    "tier": 2,
                    "first_seen_at": "2024-01-01",
                    "last_comment_at": "2024-01-01",
                    "last_comment_tier": 1,
                }
            }
        )
        stale = [self._make_stale_pr(tier=2)]
        summary = engine.process_stale_prs(stale)
        assert summary["dry_run_previews"] == 1
        assert summary["comments_posted"] == 0

    def test_skips_when_tier_unchanged(self, tmp_path):
        engine = _make_engine(tmp_path, dry_run=True)
        engine.save_state(
            {
                "acme/repo#1": {
                    "tier": 2,
                    "first_seen_at": "2024-01-01",
                    "last_comment_at": "2024-01-02",
                    "last_comment_tier": 2,
                }
            }
        )
        stale = [self._make_stale_pr(tier=2)]
        summary = engine.process_stale_prs(stale)
        assert summary["skipped"] == 1
        assert summary["dry_run_previews"] == 0

    def test_posts_comment_in_live_mode(self, tmp_path):
        engine = _make_engine(tmp_path, dry_run=False)
        # PR has advanced to tier 2 but only a tier-1 comment was posted — expect a new comment
        engine.save_state(
            {
                "acme/repo#1": {
                    "tier": 2,
                    "first_seen_at": "2024-01-01",
                    "last_comment_at": "2024-01-01",
                    "last_comment_tier": 1,
                }
            }
        )
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        engine._github.get_repo.return_value = mock_repo

        stale = [self._make_stale_pr(tier=2)]
        summary = engine.process_stale_prs(stale)

        mock_pr.create_issue_comment.assert_called_once()
        assert summary["comments_posted"] == 1
        assert summary["errors"] == 0

    def test_live_mode_error_counted(self, tmp_path):
        from github import GithubException

        engine = _make_engine(tmp_path, dry_run=False)
        engine.save_state(
            {
                "acme/repo#1": {
                    "tier": 2,
                    "first_seen_at": "2024-01-01",
                    "last_comment_at": "2024-01-01",
                    "last_comment_tier": 1,
                }
            }
        )
        engine._github.get_repo.side_effect = GithubException(404, {"message": "Not Found"})

        stale = [self._make_stale_pr(tier=2)]
        summary = engine.process_stale_prs(stale)
        assert summary["errors"] == 1
        assert summary["comments_posted"] == 0

    def test_returns_summary_structure(self, tmp_path):
        engine = _make_engine(tmp_path, dry_run=True)
        summary = engine.process_stale_prs([])
        for key in (
            "dry_run",
            "stale_prs_found",
            "comments_posted",
            "dry_run_previews",
            "state_initialized",
            "skipped",
            "errors",
            "llm_calls_used",
            "llm_cost_log",
            "actions",
        ):
            assert key in summary

    def test_state_persisted_after_processing(self, tmp_path):
        engine = _make_engine(tmp_path, dry_run=True)
        stale = [self._make_stale_pr(number=99)]
        engine.process_stale_prs(stale)
        state = engine.load_state()
        assert "acme/repo#99" in state


# ---------------------------------------------------------------------------
# run (integration-level, no real network)
# ---------------------------------------------------------------------------


class TestRun:
    def test_run_uses_config_repos_by_default(self, tmp_path):
        engine = _make_engine(tmp_path, dry_run=True)
        engine._github.get_repo.side_effect = Exception("should not be called with no stale")
        # Override scan to avoid real GitHub calls
        engine.scan_repos = MagicMock(return_value=[])
        engine.process_stale_prs = MagicMock(
            return_value={
                "dry_run": True,
                "stale_prs_found": 0,
                "comments_posted": 0,
                "dry_run_previews": 0,
                "state_initialized": 0,
                "skipped": 0,
                "errors": 0,
                "llm_calls_used": 0,
                "llm_cost_log": [],
                "actions": [],
            }
        )
        summary = engine.run()
        engine.scan_repos.assert_called_once_with(engine.config.get("repos", []))
        assert summary["dry_run"] is True

    def test_run_accepts_custom_repos(self, tmp_path):
        engine = _make_engine(tmp_path, dry_run=True)
        custom_repos = [{"owner": "x", "name": "y"}]
        engine.scan_repos = MagicMock(return_value=[])
        engine.process_stale_prs = MagicMock(
            return_value={
                "dry_run": True,
                "stale_prs_found": 0,
                "comments_posted": 0,
                "dry_run_previews": 0,
                "state_initialized": 0,
                "skipped": 0,
                "errors": 0,
                "llm_calls_used": 0,
                "llm_cost_log": [],
                "actions": [],
            }
        )
        engine.run(repos=custom_repos)
        engine.scan_repos.assert_called_once_with(custom_repos)
