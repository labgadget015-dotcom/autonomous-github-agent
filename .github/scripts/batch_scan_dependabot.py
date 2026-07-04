#!/usr/bin/env python3
"""
Batch scan open Dependabot PRs and print a tier classification table.

Reads configuration from environment variables:
    GITHUB_TOKEN        : GitHub PAT with repo read access
    GITHUB_REPOSITORY   : owner/repo string
    DRY_RUN             : "true" / "false" (default: "true")
    EXCEPTIONS_FILE     : path to .github/dependabot-exceptions.yml

Writes a Markdown summary to GITHUB_STEP_SUMMARY (if set).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import yaml
from github import Github, GithubException


def _load_blocklist_pip(exceptions_file: str) -> list[str]:
    p = Path(exceptions_file)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [str(v).lower() for v in data.get("pip", [])]


def _bump_kind(title: str) -> str:
    m = re.search(r"\bfrom\s+(\S+)\s+to\s+(\S+)", title, re.IGNORECASE)
    if not m:
        return "unknown"
    old_major = re.match(r"(\d+)", m.group(1))
    new_major = re.match(r"(\d+)", m.group(2))
    if old_major and new_major and old_major.group(1) != new_major.group(1):
        return "major"
    old_minor = re.match(r"\d+\.(\d+)", m.group(1))
    new_minor = re.match(r"\d+\.(\d+)", m.group(2))
    if old_minor and new_minor and old_minor.group(1) != new_minor.group(1):
        return "minor"
    return "patch"


def _is_blocklisted(title: str, blocklist: list[str]) -> bool:
    m = re.search(r"bump\s+(\S+)\s+from", title, re.IGNORECASE)
    if m:
        return m.group(1).lower() in blocklist
    return False


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN not set")

    repo_name = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo_name:
        sys.exit("GITHUB_REPOSITORY not set")

    dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"
    exceptions_file = os.environ.get("EXCEPTIONS_FILE", ".github/dependabot-exceptions.yml")
    blocklist = _load_blocklist_pip(exceptions_file)

    g = Github(token)
    try:
        repo = g.get_repo(repo_name)
    except GithubException as exc:
        sys.exit(f"Could not fetch repo {repo_name}: {exc}")

    prs = list(repo.get_pulls(state="open"))
    dep_prs = [
        p for p in prs
        if p.user and p.user.login == "dependabot[bot]" and not p.draft
    ]

    rows: list[tuple[int, str, str, str, str]] = []
    for pr in dep_prs:
        bump = _bump_kind(pr.title)
        blocked = _is_blocklisted(pr.title, blocklist)
        if blocked or bump == "major":
            tier, decision = "2", "needs-review"
        elif bump in ("minor", "patch"):
            tier = "1"
            decision = "would-auto-merge" if dry_run else "auto-merge"
        else:
            tier, decision = "2", "needs-review"
        rows.append((pr.number, tier, decision, bump, pr.title[:60]))

    summary_lines = [
        "## 🤖 Dependabot Auto-Merge — Batch Scan",
        "",
        f"**Dry-run:** {dry_run}",
        f"**Open Dependabot PRs found:** {len(dep_prs)}",
        "",
        "| PR | Tier | Decision | Bump | Title |",
        "|----|------|----------|------|-------|",
    ]
    for num, tier, decision, bump, title in rows:
        summary_lines.append(
            f"| #{num} | {tier} | `{decision}` | {bump} | {title} |"
        )

    output = "\n".join(summary_lines)
    print(output)

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(output + "\n")


if __name__ == "__main__":
    main()
