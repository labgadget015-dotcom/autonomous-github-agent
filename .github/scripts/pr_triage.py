#!/usr/bin/env python3
"""
PR Triage Pipeline — MVP

Classifies open PRs across configured repos into priority tiers and
creates/updates a single aggregated triage issue in autonomous-github-agent.

Tiers:
  TIER_1_SAFE   — Dependabot patch or minor version bump (auto-merge candidate)
  TIER_2_REVIEW — Dependabot major version bump OR non-dep PR open <30 days
  TIER_3_STALE  — Any PR with no activity for 30+ days

Usage:
    GITHUB_TOKEN=<pat> python pr_triage.py [--config autopilot/config.yaml] [--dry-run]
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml
from github import Github, GithubException

TRIAGE_ISSUE_TITLE = "PR Triage Queue"
TRIAGE_LABEL = "pr-triage"
HOME_REPO = "labgadget015-dotcom/autonomous-github-agent"
STALE_DAYS = 30


def _load_repos(config_path: str) -> list[dict]:
    """Read repo list from autopilot config.yaml."""
    p = Path(config_path)
    if not p.exists():
        sys.exit(f"Config not found: {config_path}")
    with open(p) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("repos", [])


def _is_dependabot(pr) -> bool:
    return pr.user and pr.user.login in ("dependabot[bot]", "dependabot-preview[bot]")


def _bump_tier(title: str) -> str:
    """Return 'major' or 'minor_patch' by parsing 'from X to Y' in the title."""
    m = re.search(r"\bfrom\s+(\S+)\s+to\s+(\S+)", title, re.IGNORECASE)
    if not m:
        return "minor_patch"
    old_ver, new_ver = m.group(1), m.group(2)
    old_major = re.match(r"(\d+)", old_ver)
    new_major = re.match(r"(\d+)", new_ver)
    if old_major and new_major and old_major.group(1) != new_major.group(1):
        return "major"
    return "minor_patch"


def _classify_pr(pr, now: datetime) -> str:
    """Return one of: TIER_1_SAFE, TIER_2_REVIEW, TIER_3_STALE."""
    if pr.draft:
        return "DRAFT"

    days_since_activity = (now - pr.updated_at.replace(tzinfo=None)).days

    if days_since_activity >= STALE_DAYS:
        return "TIER_3_STALE"

    if _is_dependabot(pr):
        if _bump_tier(pr.title) == "major":
            return "TIER_2_REVIEW"
        return "TIER_1_SAFE"

    return "TIER_2_REVIEW"


def triage_repos(repos: list[dict], g: Github) -> dict[str, list[dict]]:
    """Fetch and classify open PRs across all repos."""
    now = datetime.utcnow()
    buckets: dict[str, list[dict]] = {
        "TIER_1_SAFE": [],
        "TIER_2_REVIEW": [],
        "TIER_3_STALE": [],
        "DRAFT": [],
    }

    for repo_cfg in repos:
        full_name = f"{repo_cfg['owner']}/{repo_cfg['name']}"
        try:
            repo = g.get_repo(full_name)
            prs = list(repo.get_pulls(state="open", sort="updated", direction="desc"))
        except GithubException as e:
            print(f"  SKIP {full_name}: {e.status} {e.data}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"  SKIP {full_name}: {e}", file=sys.stderr)
            continue

        for pr in prs:
            tier = _classify_pr(pr, now)
            days_open = (now - pr.created_at.replace(tzinfo=None)).days
            buckets[tier].append(
                {
                    "repo": full_name,
                    "number": pr.number,
                    "title": pr.title,
                    "url": pr.html_url,
                    "days_open": days_open,
                    "days_since_activity": (now - pr.updated_at.replace(tzinfo=None)).days,
                    "author": pr.user.login if pr.user else "unknown",
                }
            )

        print(f"  {full_name}: {len(prs)} open PRs")

    return buckets


def _render_table(prs: list[dict]) -> str:
    if not prs:
        return "_None_\n"
    rows = [
        "| Repo | PR | Title | Open | Last Activity |",
        "|------|----|-------|------|---------------|",
    ]
    for p in prs:
        short_repo = p["repo"].split("/")[-1]
        title = p["title"][:60] + ("…" if len(p["title"]) > 60 else "")
        rows.append(
            f"| {short_repo} | [#{p['number']}]({p['url']}) "
            f"| {title} | {p['days_open']}d | {p['days_since_activity']}d ago |"
        )
    return "\n".join(rows) + "\n"


def _build_body(buckets: dict, timestamp: str) -> str:
    t1 = buckets["TIER_1_SAFE"]
    t2 = buckets["TIER_2_REVIEW"]
    t3 = buckets["TIER_3_STALE"]
    drafts = buckets["DRAFT"]

    total = len(t1) + len(t2) + len(t3)
    body = f"""## PR Triage Queue

**Generated:** {timestamp}
**Total open (non-draft):** {total} | Tier 1: {len(t1)} | Tier 2: {len(t2)} | Tier 3 (stale): {len(t3)} | Drafts skipped: {len(drafts)}

---

### Tier 1 — Safe Dependency Bumps (patch/minor, Dependabot)
_Auto-merge candidates — no breaking changes expected._

{_render_table(t1)}

---

### Tier 2 — Needs Review
_Major version bumps or feature PRs open <{STALE_DAYS} days._

{_render_table(t2)}

---

### Tier 3 — Stale (>{STALE_DAYS} days no activity)
_Review or close these._

{_render_table(t3)}

---
_Generated by pr_triage.py — [source](.github/scripts/pr_triage.py)_
"""
    return body


def upsert_triage_issue(g: Github, body: str, dry_run: bool) -> None:
    """Find existing open triage issue and update it, or create a new one."""
    repo = g.get_repo(HOME_REPO)

    # Ensure the label exists
    if not dry_run:
        try:
            repo.get_label(TRIAGE_LABEL)
        except GithubException:
            repo.create_label(TRIAGE_LABEL, "0075ca")

    all_triage = repo.get_issues(state="open", labels=[TRIAGE_LABEL])
    existing = list(all_triage)[:10]
    triage_issues = [i for i in existing if i.title == TRIAGE_ISSUE_TITLE]

    if dry_run:
        print(
            f"\n[dry-run] Would {'update' if triage_issues else 'create'} "
            f"issue '{TRIAGE_ISSUE_TITLE}' in {HOME_REPO}"
        )
        print("\n--- BODY PREVIEW ---")
        print(body[:1200] + ("…" if len(body) > 1200 else ""))
        return

    if triage_issues:
        issue = triage_issues[0]
        issue.edit(body=body)
        print(f"\nUpdated issue #{issue.number}: {issue.html_url}")
    else:
        issue = repo.create_issue(
            title=TRIAGE_ISSUE_TITLE,
            body=body,
            labels=[TRIAGE_LABEL],
        )
        print(f"\nCreated issue #{issue.number}: {issue.html_url}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PR Triage Pipeline MVP")
    parser.add_argument(
        "--config",
        default="autopilot/config.yaml",
        help="Path to autopilot config.yaml",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print triage output without writing to GitHub",
    )
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN not set")

    g = Github(token)
    try:
        g.get_rate_limit()
    except Exception as e:
        sys.exit(f"Token validation failed: {e}")

    repos = _load_repos(args.config)
    print(f"Triaging PRs across {len(repos)} repos...")

    buckets = triage_repos(repos, g)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    body = _build_body(buckets, timestamp)
    upsert_triage_issue(g, body, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
