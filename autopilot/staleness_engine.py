#!/usr/bin/env python3
"""
Staleness Sentinel — Automated PR aging & escalation pipeline.

Scans configured repos for stale pull requests, assigns tier levels based on
age, and (when live mode is enabled) posts escalation comments.

Environment variables:
    ENABLE_LIVE_MODE    Set to "true" to post comments (default: dry-run only)
    GITHUB_TOKEN        GitHub personal access token

Tier definitions (configurable in config.yaml under ``staleness.tiers``):
    Tier 0   < 7 days  — normal, no action
    Tier 1   7–30 days — gentle nudge comment
    Tier 2  31–60 days — escalation comment
    Tier 3   > 60 days — critical escalation comment

State is persisted to ``staleness_state.json`` so that the engine only posts
one comment per tier transition — preventing spam on first live run and on
subsequent identical-tier scans.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from github import Github, GithubException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default tier definitions
# ---------------------------------------------------------------------------

DEFAULT_TIERS: list[dict[str, Any]] = [
    {"tier": 1, "min_days": 7, "label": "stale", "template": "tier1"},
    {"tier": 2, "min_days": 31, "label": "stale-escalated", "template": "tier2"},
    {"tier": 3, "min_days": 61, "label": "stale-critical", "template": "tier3"},
]

COMMENT_TEMPLATES: dict[str, str] = {
    "tier1": (
        "👋 **Staleness Sentinel** — This PR has been open for **{age_days} days**. "
        "Would you like any help moving it forward? If it is blocked, please add a "
        "`blocked` label so it can be tracked."
    ),
    "tier2": (
        "⚠️ **Staleness Sentinel** — This PR has been open for **{age_days} days** "
        "without merging. Please consider:\n"
        "- Rebasing / resolving conflicts\n"
        "- Requesting a review\n"
        "- Closing it if the work has been superseded\n\n"
        "If this PR is still relevant, please leave a status update."
    ),
    "tier3": (
        "🚨 **Staleness Sentinel** — This PR has been open for **{age_days} days**. "
        "It is now critically stale. Action required:\n"
        "- **Merge** if ready\n"
        "- **Close** if no longer needed\n"
        "- **Add a comment** explaining why it must stay open\n\n"
        "This PR will continue to be flagged until resolved."
    ),
}


class StalenessEngine:
    """
    Scans GitHub repos for stale PRs and posts tiered escalation comments.

    Args:
        config:         Staleness config dict (from ``config.yaml`` staleness section).
        github_token:   GitHub PAT.  Defaults to ``GITHUB_TOKEN`` env var.
        dry_run:        When *True* (the default) no GitHub writes are performed.
                        Pass *False* or set ``ENABLE_LIVE_MODE=true`` to activate writes.
        max_llm_calls:  Hard cap on LLM calls per run (default 20).  Unused calls are
                        silently skipped; templates are used as fallback.
        state_file:     Path to the JSON state cache.  Defaults to
                        ``staleness_state.json`` next to this module.
    """

    def __init__(
        self,
        config: dict[str, Any],
        github_token: str | None = None,
        dry_run: bool | None = None,
        max_llm_calls: int = 20,
        state_file: Path | str | None = None,
    ) -> None:
        self.config = config

        token = github_token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN is required for StalenessEngine")
        self._github = Github(token)

        # dry_run: explicit arg > env var > True (safe default)
        if dry_run is None:
            dry_run = os.getenv("ENABLE_LIVE_MODE", "").lower() != "true"
        self.dry_run: bool = dry_run

        self.max_llm_calls: int = max_llm_calls
        self._llm_calls_used: int = 0

        self.state_file: Path = (
            Path(state_file)
            if state_file is not None
            else Path(__file__).parent / "staleness_state.json"
        )

        self.tiers: list[dict[str, Any]] = config.get("tiers", DEFAULT_TIERS)
        # Sort tiers descending so we match the highest applicable tier first
        self.tiers = sorted(self.tiers, key=lambda t: t["min_days"], reverse=True)

        self._cost_log: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def load_state(self) -> dict[str, Any]:
        """Load persisted staleness state from disk.

        Returns an empty dict if the state file does not exist yet.
        """
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load staleness state (%s); starting fresh.", exc)
            return {}

    def save_state(self, state: dict[str, Any]) -> None:
        """Persist staleness state to disk."""
        try:
            self.state_file.write_text(
                json.dumps(state, indent=2, default=str), encoding="utf-8"
            )
        except OSError as exc:
            logger.error("Failed to save staleness state: %s", exc)

    # ------------------------------------------------------------------
    # Tier assignment
    # ------------------------------------------------------------------

    def assign_tier(self, age_days: int) -> int:
        """Return the staleness tier for a PR that has been open *age_days* days.

        Returns 0 if the PR is not yet stale.
        """
        for tier_def in self.tiers:
            if age_days >= tier_def["min_days"]:
                return int(tier_def["tier"])
        return 0

    # ------------------------------------------------------------------
    # Comment generation
    # ------------------------------------------------------------------

    def generate_comment(
        self,
        age_days: int,
        tier: int,
        llm_client: Any | None = None,
        pr_title: str = "",
        repo_full_name: str = "",
    ) -> str:
        """Generate an escalation comment for a stale PR.

        Uses an LLM when *llm_client* is supplied and the call budget has not
        been exhausted; otherwise falls back to the built-in template.
        """
        # Find the template key for this tier (allow config-defined template mapping)
        tier_def = next((t for t in self.tiers if int(t.get("tier", 0)) == tier), {})
        template_key = str(tier_def.get("template") or f"tier{tier}")
        templates: dict[str, str] = self.config.get("templates", COMMENT_TEMPLATES)
        template = templates.get(template_key, COMMENT_TEMPLATES.get(template_key, ""))
        base_comment = template.format(
            age_days=age_days,
            pr_title=pr_title,
            repo=repo_full_name,
        )

        if llm_client is not None and self._llm_calls_used < self.max_llm_calls:
            try:
                import asyncio

                prompt = (
                    f"Rewrite the following staleness comment for PR '{pr_title}' in "
                    f"repo '{repo_full_name}' (open {age_days} days, tier {tier}). "
                    f"Keep it concise, actionable, and friendly. "
                    f"Preserve the emoji prefix.\n\nBase comment:\n{base_comment}"
                )
                result = asyncio.run(
                    llm_client.generate(prompt, max_tokens=300, temperature=0.4)
                )
                self._llm_calls_used += 1
                cost = result.get("usage", {})
                self._cost_log.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "repo": repo_full_name,
                        "tier": tier,
                        "usage": cost,
                    }
                )
                return result.get("content", base_comment)
            except Exception as exc:
                logger.warning(
                    "LLM call failed for %s (falling back to template): %s",
                    repo_full_name,
                    exc,
                )

        return base_comment

    # ------------------------------------------------------------------
    # Repo scanning
    # ------------------------------------------------------------------

    def scan_repos(self, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Scan *repos* and return a list of stale PR descriptors.

        Each descriptor contains:
            repo_full_name, pr_number, pr_title, pr_url, age_days, tier
        """
        stale: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        for repo_cfg in repos:
            owner = repo_cfg["owner"]
            name = repo_cfg["name"]
            full_name = f"{owner}/{name}"
            try:
                repo = self._github.get_repo(full_name)
                pulls = repo.get_pulls(state="open", sort="created", direction="asc")
                for pr in pulls:
                    created = pr.created_at
                    if created.tzinfo is None:
                        created = created.replace(tzinfo=timezone.utc)
                    age_days = (now - created).days
                    tier = self.assign_tier(age_days)
                    if tier > 0:
                        stale.append(
                            {
                                "repo_full_name": full_name,
                                "pr_number": pr.number,
                                "pr_title": pr.title,
                                "pr_url": pr.html_url,
                                "age_days": age_days,
                                "tier": tier,
                            }
                        )
            except GithubException as exc:
                logger.warning(
                    "Skipping %s — GitHub API error %s: %s",
                    full_name,
                    exc.status,
                    exc.data,
                )
            except Exception as exc:
                logger.warning(
                    "Skipping %s — unexpected error: %s: %s",
                    full_name,
                    type(exc).__name__,
                    exc,
                )

        return stale

    # ------------------------------------------------------------------
    # Core processing loop
    # ------------------------------------------------------------------

    def process_stale_prs(
        self,
        stale_prs: list[dict[str, Any]],
        llm_client: Any | None = None,
    ) -> dict[str, Any]:
        """Post escalation comments for PRs whose tier has advanced.

        Only posts a comment when a PR moves to a *higher* tier than the last
        recorded tier — preventing duplicate comments on re-runs.

        Returns a summary dict with counts and per-PR actions taken.
        """
        state = self.load_state()
        now_iso = datetime.now(timezone.utc).isoformat()
        actions: list[dict[str, Any]] = []

        for pr_info in stale_prs:
            key = f"{pr_info['repo_full_name']}#{pr_info['pr_number']}"
            last_tier = state.get(key, {}).get("tier", 0)
            current_tier = pr_info["tier"]

            # Pre-populate on first encounter (no comment yet — just record state)
            if key not in state:
                state[key] = {
                    "tier": current_tier,
                    "first_seen_at": now_iso,
                    "last_comment_at": None,
                    "last_comment_tier": 0,
                }
                actions.append({**pr_info, "action": "state_initialized"})
                logger.info(
                    "[init] %s — tier %d (%d days), state pre-populated (no comment)",
                    key,
                    current_tier,
                    pr_info["age_days"],
                )
                continue

            # Update stored tier
            state[key]["tier"] = current_tier

            last_comment_tier = state[key].get("last_comment_tier", 0)

            if current_tier <= last_comment_tier:
                logger.debug(
                    "[skip] %s — tier %d (last comment tier %d), no escalation needed",
                    key,
                    current_tier,
                    last_comment_tier,
                )
                actions.append({**pr_info, "action": "skipped"})
                continue

            # Tier advanced — generate and (optionally) post comment
            comment = self.generate_comment(
                age_days=pr_info["age_days"],
                tier=current_tier,
                llm_client=llm_client,
                pr_title=pr_info["pr_title"],
                repo_full_name=pr_info["repo_full_name"],
            )

            if self.dry_run:
                logger.info(
                    "[dry-run] %s — would post tier-%d comment:\n%s",
                    key,
                    current_tier,
                    comment,
                )
                actions.append({**pr_info, "action": "dry_run", "comment": comment})
            else:
                try:
                    repo_obj = self._github.get_repo(pr_info["repo_full_name"])
                    pr_obj = repo_obj.get_pull(pr_info["pr_number"])
                    pr_obj.create_issue_comment(comment)
                    state[key]["last_comment_at"] = now_iso
                    state[key]["last_comment_tier"] = current_tier
                    logger.info(
                        "[posted] %s — tier-%d comment posted", key, current_tier
                    )
                    actions.append(
                        {**pr_info, "action": "comment_posted", "comment": comment}
                    )
                except GithubException as exc:
                    logger.error("Failed to post comment on %s: %s", key, exc)
                    actions.append({**pr_info, "action": "error", "error": str(exc)})

        self.save_state(state)

        summary: dict[str, Any] = {
            "dry_run": self.dry_run,
            "stale_prs_found": len(stale_prs),
            "comments_posted": sum(
                1 for a in actions if a["action"] == "comment_posted"
            ),
            "dry_run_previews": sum(1 for a in actions if a["action"] == "dry_run"),
            "state_initialized": sum(
                1 for a in actions if a["action"] == "state_initialized"
            ),
            "skipped": sum(1 for a in actions if a["action"] == "skipped"),
            "errors": sum(1 for a in actions if a["action"] == "error"),
            "llm_calls_used": self._llm_calls_used,
            "llm_cost_log": self._cost_log,
            "actions": actions,
        }
        return summary

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(
        self,
        repos: list[dict[str, Any]] | None = None,
        llm_client: Any | None = None,
    ) -> dict[str, Any]:
        """Scan repos and process stale PRs end-to-end.

        Args:
            repos:      List of repo config dicts (``[{owner, name}]``).
                        Defaults to ``config["repos"]``.
            llm_client: Optional LLM client for personalised comments.

        Returns:
            Summary dict from :meth:`process_stale_prs`.
        """
        if repos is None:
            repos = self.config.get("repos", [])

        mode = "DRY-RUN" if self.dry_run else "LIVE"
        logger.info(
            "[staleness] Starting scan (%s, max_llm_calls=%d)", mode, self.max_llm_calls
        )

        stale_prs = self.scan_repos(repos)
        logger.info(
            "[staleness] Found %d stale PRs across %d repos", len(stale_prs), len(repos)
        )

        summary = self.process_stale_prs(stale_prs, llm_client=llm_client)

        if self.dry_run:
            print(
                f"[staleness] DRY-RUN complete — {summary['stale_prs_found']} stale PRs found, "
                f"{summary['dry_run_previews']} comments previewed."
            )
        else:
            print(
                f"[staleness] LIVE run complete — {summary['comments_posted']} comments posted, "
                f"{summary['errors']} errors."
            )

        return summary


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for the Staleness Sentinel."""
    import argparse

    import yaml

    parser = argparse.ArgumentParser(
        description="Staleness Sentinel — PR escalation pipeline"
    )
    parser.add_argument(
        "--config", default="config.yaml", help="Path to autopilot config.yaml"
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Path to staleness state JSON (default: staleness_state.json next to config)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable live mode (post comments). Default is dry-run.",
    )
    parser.add_argument(
        "--max-llm-calls",
        type=int,
        default=None,
        help="Hard cap on LLM calls per run (default: staleness.max_llm_calls_per_run or 20)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    config_file = Path(__file__).parent / args.config
    if not config_file.exists():
        print(f"Config file not found: {config_file}", file=sys.stderr)
        sys.exit(1)

    with open(config_file, encoding="utf-8") as f:
        full_config = yaml.safe_load(f)

    staleness_cfg = full_config.get("staleness", {})
    staleness_cfg["repos"] = full_config.get("repos", [])

    max_llm_calls = (
        args.max_llm_calls
        if args.max_llm_calls is not None
        else int(staleness_cfg.get("max_llm_calls_per_run", 20))
    )

    state_file = (
        Path(args.state_file)
        if args.state_file
        else Path(__file__).parent / "staleness_state.json"
    )

    engine = StalenessEngine(
        config=staleness_cfg,
        dry_run=not args.live,
        max_llm_calls=max_llm_calls,
        state_file=state_file,
    )
    summary = engine.run()

    # Print cost summary
    if summary["llm_calls_used"]:
        print(f"LLM calls used: {summary['llm_calls_used']} / {args.max_llm_calls}")


if __name__ == "__main__":
    main()
