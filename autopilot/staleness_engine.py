#!/usr/bin/env python3
"""
Staleness Sentinel — Automated PR Aging & Escalation Pipeline

Monitors open PRs across configured repositories, assigns age-based tier
classifications, and posts escalation comments via GitHub when a PR moves
to a higher-severity tier.

Safety defaults:
- Dry-run is ON by default.  Set ``ENABLE_LIVE_MODE=true`` in the environment
  to allow write operations (GitHub PR comments + state file writes).
- Claude call cap defaults to 20 per run.  Override with the
  ``MAX_CLAUDE_CALLS_PER_RUN`` env var or ``staleness.max_claude_calls_per_run``
  config key.

Usage (standalone):
    python -m autopilot.staleness_engine [--config config.yaml] [--init-only]
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from github import GithubException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier definitions
# Format: tier_key -> (min_days_inclusive, max_days_inclusive_or_None, label, emoji)
# ---------------------------------------------------------------------------
TIERS: dict[str, tuple[int, int | None, str, str]] = {
    "T0": (0, 6, "fresh", "🟢"),
    "T1": (7, 29, "aging", "🟡"),
    "T2": (30, 89, "stale", "🟠"),
    "T3": (90, None, "critical", "🔴"),
}

_TIER_ORDER: list[str] = ["T0", "T1", "T2", "T3"]
_DEFAULT_STATE_FILE = Path(__file__).parent / "staleness_state.json"
_SCHEMA_VERSION = 1


def classify_tier(days_open: int) -> str:
    """Return the staleness tier key (T0–T3) for a PR open *days_open* days."""
    for tier_key in reversed(_TIER_ORDER):
        min_days, _, _, _ = TIERS[tier_key]
        if days_open >= min_days:
            return tier_key
    return "T0"


def _utcnow() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


def _days_open(pr: Any) -> int:
    """Return the number of days a PR has been open (timezone-naive arithmetic)."""
    return (datetime.now() - pr.created_at.replace(tzinfo=None)).days


class StalenessEngine:
    """
    Cross-repo PR staleness monitor with tiered escalation.

    Args:
        config:     Staleness-specific config dict (from ``staleness`` section
                    of ``autopilot/config.yaml``).
        state_file: Path to the JSON file that persists per-PR tier state.
                    Defaults to ``autopilot/staleness_state.json``.
        llm_config: Optional dict forwarded to ``LLMClient`` for Claude-powered
                    comment generation.  When omitted, comments fall back to
                    static templates.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        state_file: str | Path | None = None,
        llm_config: dict[str, Any] | None = None,
    ) -> None:
        self.config: dict[str, Any] = config or {}
        self.state_file = Path(state_file) if state_file else _DEFAULT_STATE_FILE
        self.llm_config = llm_config

        # Dry-run: write operations are suppressed unless ENABLE_LIVE_MODE=true
        self.dry_run: bool = (
            os.getenv("ENABLE_LIVE_MODE", "").strip().lower() != "true"
        )

        # Claude call cap (env var takes precedence over config)
        env_cap = os.getenv("MAX_CLAUDE_CALLS_PER_RUN", "").strip()
        cfg_cap = self.config.get("max_claude_calls_per_run", 20)
        self.max_claude_calls: int = int(env_cap) if env_cap.isdigit() else int(cfg_cap)
        self._claude_calls_this_run: int = 0

        self._state: dict[str, Any] = self._load_state()

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _load_state(self) -> dict[str, Any]:
        """Load staleness state from disk; return empty state on miss or error."""
        if self.state_file.exists():
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("schema_version") == _SCHEMA_VERSION:
                    return data
                logger.warning(
                    "staleness_state.json schema mismatch (expected v%d) — resetting.",
                    _SCHEMA_VERSION,
                )
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load staleness state: %s", exc)
        return {"schema_version": _SCHEMA_VERSION, "prs": {}}

    def _save_state(self) -> None:
        """Write current state to disk.  No-op in dry-run mode."""
        if self.dry_run:
            logger.debug("[dry-run] _save_state: skipping state file write.")
            return
        self._state["saved_at"] = _utcnow()
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
        except OSError as exc:
            logger.error("Failed to save staleness state: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        """Return a snapshot of the current in-memory state."""
        import copy

        return copy.deepcopy(self._state)

    def classify_tier(self, days_open: int) -> str:
        """Classify a PR by the number of days it has been open."""
        return classify_tier(days_open)

    def init_state_from_prs(self, repo_data: dict[str, Any]) -> None:
        """
        Pre-populate state for all currently open PRs **without** posting
        any escalation comments.

        Call this on first run to prevent comment-spam on PRs that have
        already been open a long time before the sentinel was deployed.

        Args:
            repo_data:  The ``repo_data`` dict produced by
                        ``GitHubAutopilot.fetch_all_repos()``.
        """
        now = _utcnow()
        seeded = 0
        for repo_key, data in repo_data.items():
            for pr in data.get("pulls", []):
                days_open = _days_open(pr)
                tier = classify_tier(days_open)
                pr_key = f"{repo_key}/{pr.number}"
                if pr_key not in self._state["prs"]:
                    self._state["prs"][pr_key] = {
                        "tier": tier,
                        "days_open": days_open,
                        "pr_number": pr.number,
                        "pr_title": pr.title,
                        "pr_url": pr.html_url,
                        "repo": repo_key,
                        "first_seen": now,
                        "last_escalated_tier": tier,
                        "last_comment_at": None,
                        "comment_count": 0,
                    }
                    seeded += 1

        self._save_state()
        logger.info(
            "[staleness] init_state_from_prs: seeded %d new PR entries (dry_run=%s).",
            seeded,
            self.dry_run,
        )

    def process_prs(
        self,
        repo_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Scan all open PRs, refresh tier assignments, and escalate when a PR
        moves to a higher-severity tier.

        Args:
            repo_data:  The ``repo_data`` dict produced by
                        ``GitHubAutopilot.fetch_all_repos()``.

        Returns:
            A list of action records — one per escalated PR.  Each record
            contains ``pr_key``, ``tier``, ``days_open``, ``comment_body``,
            ``posted``, and ``dry_run`` fields.
        """
        actions: list[dict[str, Any]] = []

        for repo_key, data in repo_data.items():
            repo_obj = data.get("repo_obj")
            for pr in data.get("pulls", []):
                days_open = _days_open(pr)
                current_tier = classify_tier(days_open)
                pr_key = f"{repo_key}/{pr.number}"

                entry = self._state["prs"].get(pr_key)
                if entry is None:
                    # First time we see this PR — seed without escalating
                    self._state["prs"][pr_key] = {
                        "tier": current_tier,
                        "days_open": days_open,
                        "pr_number": pr.number,
                        "pr_title": pr.title,
                        "pr_url": pr.html_url,
                        "repo": repo_key,
                        "first_seen": _utcnow(),
                        "last_escalated_tier": current_tier,
                        "last_comment_at": None,
                        "comment_count": 0,
                    }
                    continue

                # Refresh current values
                entry["tier"] = current_tier
                entry["days_open"] = days_open

                prev_tier = entry.get("last_escalated_tier", entry["tier"])
                if _TIER_ORDER.index(current_tier) > _TIER_ORDER.index(prev_tier):
                    action = self._escalate(
                        pr_key, pr, current_tier, days_open, repo_obj
                    )
                    actions.append(action)

        self._save_state()
        return actions

    # ------------------------------------------------------------------
    # Escalation helpers
    # ------------------------------------------------------------------

    def _escalate(
        self,
        pr_key: str,
        pr: Any,
        tier: str,
        days_open: int,
        repo_obj: Any,
    ) -> dict[str, Any]:
        """Build, optionally post, and return an action record for one PR."""
        tier_label = TIERS[tier][2]
        tier_emoji = TIERS[tier][3]
        comment_body = self._generate_comment(pr, tier, tier_label, tier_emoji, days_open)

        action: dict[str, Any] = {
            "pr_key": pr_key,
            "pr_number": pr.number,
            "pr_title": pr.title,
            "pr_url": pr.html_url,
            "tier": tier,
            "days_open": days_open,
            "comment_body": comment_body,
            "posted": False,
            "dry_run": self.dry_run,
        }

        if self.dry_run:
            logger.info(
                "[dry-run] Would escalate %s to %s (%s, %d days): %s",
                pr_key,
                tier,
                tier_label,
                days_open,
                pr.title,
            )
        else:
            posted = self._post_comment(repo_obj, pr, comment_body)
            action["posted"] = posted
            if posted:
                entry = self._state["prs"][pr_key]
                entry["last_escalated_tier"] = tier
                entry["last_comment_at"] = _utcnow()
                entry["comment_count"] = entry.get("comment_count", 0) + 1

        return action

    def _generate_comment(
        self,
        pr: Any,
        tier: str,
        tier_label: str,
        tier_emoji: str,
        days_open: int,
    ) -> str:
        """
        Return a comment body string.

        Tries Claude first (if ``llm_config`` is set and the per-run call cap
        has not been exhausted); falls back to a static template.
        """
        if self.llm_config and self._claude_calls_this_run < self.max_claude_calls:
            claude_text = self._generate_claude_comment(
                pr, tier, tier_label, tier_emoji, days_open
            )
            if claude_text:
                return claude_text

        return self._static_comment(pr, tier, tier_label, tier_emoji, days_open)

    def _generate_claude_comment(
        self,
        pr: Any,
        tier: str,
        tier_label: str,
        tier_emoji: str,
        days_open: int,
    ) -> str | None:
        """Call Claude to generate a contextual escalation comment."""
        import asyncio

        try:
            from core.llm_provider import LLMClient
        except ImportError:
            logger.warning(
                "core.llm_provider not available — using static template."
            )
            return None

        if self._claude_calls_this_run >= self.max_claude_calls:
            logger.info(
                "[staleness] Claude call cap reached (%d/%d) — using static template.",
                self._claude_calls_this_run,
                self.max_claude_calls,
            )
            return None

        system = (
            "You are a helpful engineering assistant writing concise GitHub PR "
            "escalation comments. Be professional, constructive, and brief "
            "(≤120 words). Do not include greetings."
        )
        prompt = (
            f"Write a PR escalation comment for PR #{pr.number}: '{pr.title}'. "
            f"It has been open for {days_open} days and reached staleness tier "
            f"{tier} ({tier_label} {tier_emoji}). "
            "Remind the team it needs attention and suggest a concrete next step."
        )

        try:
            client = LLMClient(self.llm_config)
            result = asyncio.run(
                client.generate(prompt, system_prompt=system, max_tokens=200)
            )
            self._claude_calls_this_run += 1
            logger.info(
                "[staleness] Claude call %d/%d completed. Session cost: %s",
                self._claude_calls_this_run,
                self.max_claude_calls,
                client.get_session_cost(),
            )
            return result.get("content", "").strip() or None
        except Exception as exc:
            logger.warning("Claude comment generation failed: %s", exc)
            return None

    @staticmethod
    def _static_comment(
        pr: Any,
        tier: str,
        tier_label: str,
        tier_emoji: str,
        days_open: int,
    ) -> str:
        """Return a static escalation comment template for the given tier."""
        templates: dict[str, str] = {
            "T1": (
                "👋 This PR has been open for **{days} days** and is now "
                "marked **aging** {emoji}. Please review at your earliest "
                "convenience."
            ),
            "T2": (
                "⚠️ This PR has been open for **{days} days** and is now "
                "marked **stale** {emoji}. It needs attention — please review, "
                "update, or close this PR to keep the backlog healthy."
            ),
            "T3": (
                "🚨 This PR has been open for **{days} days** and is now "
                "**critically stale** {emoji}. Immediate action is required — "
                "please merge, close, or leave a status update."
            ),
        }
        template = templates.get(
            tier,
            "This PR has reached staleness tier {tier} ({label} {emoji}) "
            "after {days} days.",
        )
        return template.format(
            days=days_open,
            emoji=tier_emoji,
            tier=tier,
            label=tier_label,
        )

    def _post_comment(self, repo_obj: Any, pr: Any, comment: str) -> bool:
        """Post *comment* to the GitHub PR issue thread."""
        if repo_obj is None:
            logger.warning(
                "[staleness] repo_obj is None for PR #%d — skipping comment.",
                pr.number,
            )
            return False
        try:
            pull = repo_obj.get_pull(pr.number)
            pull.create_issue_comment(comment)
            logger.info(
                "[staleness] Posted escalation comment on %s PR #%d.",
                pr.html_url,
                pr.number,
            )
            return True
        except GithubException as exc:
            logger.error(
                "[staleness] Failed to post comment on PR #%d: %s",
                pr.number,
                exc,
            )
            return False


def main() -> None:
    """CLI entry point for standalone staleness checks."""
    import argparse
    import sys

    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Staleness Sentinel — PR Aging & Escalation"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Autopilot config file (default: config.yaml)",
    )
    parser.add_argument(
        "--state-file",
        default=str(_DEFAULT_STATE_FILE),
        help="Path to staleness_state.json",
    )
    parser.add_argument(
        "--init-only",
        action="store_true",
        help=(
            "Seed state file from current open PRs without posting any comments. "
            "Run this once before going live to avoid comment-spam on old PRs."
        ),
    )
    args = parser.parse_args()

    from autopilot.autopilot import GitHubAutopilot

    try:
        autopilot = GitHubAutopilot(config_path=args.config)
        autopilot.fetch_all_repos()

        staleness_cfg = autopilot.config.get("staleness", {})
        engine = StalenessEngine(
            config=staleness_cfg,
            state_file=args.state_file,
        )

        if args.init_only:
            engine.init_state_from_prs(autopilot.repo_data)
            state = engine.get_state()
            print(
                f"✅ State seeded: {len(state['prs'])} PRs recorded "
                f"(dry_run={engine.dry_run}, no comments posted)"
            )
            return

        actions = engine.process_prs(autopilot.repo_data)
        posted = sum(1 for a in actions if a.get("posted"))
        dry_run_logged = sum(1 for a in actions if a.get("dry_run"))
        print(
            f"✅ Staleness check complete: {len(actions)} escalation(s) "
            f"(posted={posted}, dry_run_logged={dry_run_logged})"
        )

        for action in actions:
            tier_label = TIERS[action["tier"]][2]
            status = "DRY-RUN" if action["dry_run"] else ("✓" if action["posted"] else "✗")
            print(
                f"  [{status}] {action['pr_key']} → {action['tier']} "
                f"({tier_label}, {action['days_open']}d): {action['pr_title']}"
            )

    except Exception as exc:
        print(f"❌ Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
