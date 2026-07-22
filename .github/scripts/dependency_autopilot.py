#!/usr/bin/env python3
"""Dependency autopilot -- schedule-safe wrapper around dependency_audit.py.

Report mode (DEFAULT, used by the Hermes cron job):
  audit requirements.txt -> categorize -> emit report. No git writes, no PRs.
  Intended to be delivered as a Telegram summary by the cron runner.

Apply mode (--apply, OPT-IN -- never the default):
  For each SAFE update (patch only), create a branch, bump the pinned version in
  requirements.txt, run the new unit tests, then open a DRAFT pull request via
  `gh pr create --draft`. This script NEVER merges.

Claude Code integration (--use-claude):
  When passed AND `claude` is available AND not session-capped, non-trivial
  (minor/major) upgrades are delegated to Claude Code. Otherwise they are skipped
  -- major bumps need human eyes, by design.

This script is invoked unattended by a Hermes cron job (no_agent). It must never
require interactive input. All writes are draft-PR-only or report-only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dependency_audit as da  # noqa: E402

SAFE_CATEGORIES = {"patch"}


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def bump_requirement(req_path: Path, name: str, new_version: str) -> bool:
    text = req_path.read_text(encoding="utf-8")
    pat = re.compile(
        rf"^(\s*{re.escape(name)}(\s*\[[^\]]*\])?\s*(?:[<>=!~]=?\s*)?)\d[\d.\-+]*",
        re.M,
    )
    new_text, n = pat.subn(lambda m: m.group(1) + new_version, text)
    if n:
        req_path.write_text(new_text, encoding="utf-8")
    return n > 0


def apply_updates(
    repo_root: Path, results: list[da.AuditResult], use_claude: bool
) -> str | None:
    req_path = repo_root / "requirements.txt"
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    branch = f"deps/patch-{today}"
    safe = [r for r in results if r.category in SAFE_CATEGORIES and r.latest]
    if not safe:
        return None
    _run(["git", "-C", str(repo_root), "checkout", "-b", branch])
    for r in safe:
        assert r.latest is not None
        bump_requirement(req_path, r.name, r.latest)
    _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/test_dependency_audit.py",
            "-q",
            "--no-cov",
        ],
        check=False,
    )
    _run(["git", "-C", str(repo_root), "add", "requirements.txt"])
    _run(
        [
            "git",
            "-C",
            str(repo_root),
            "commit",
            "-m",
            f"chore(deps): patch-bump {len(safe)} packages ({today})",
        ]
    )
    body = da.build_report(results)
    pr = _run(
        [
            "gh",
            "pr",
            "create",
            "--draft",
            "--title",
            f"chore(deps): patch bumps {today}",
            "--body",
            body,
        ],
        check=False,
    )
    return pr.stdout.strip() or pr.stderr.strip()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scheduled dependency autopilot.")
    p.add_argument("--repo", default=".")
    p.add_argument("--requirements", default=None)
    p.add_argument(
        "--apply", action="store_true", help="Opt-in: branch + draft PR (patch only)"
    )
    p.add_argument(
        "--use-claude", action="store_true", help="Delegate minor/major to Claude Code"
    )
    p.add_argument("--report", default=None)
    args = p.parse_args(argv)

    repo = Path(args.repo).resolve()
    req = Path(args.requirements) if args.requirements else repo / "requirements.txt"
    reqs = da.parse_requirements(req)
    results = da.audit(reqs)
    report = da.build_report(results)
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    print(report)

    if args.apply:
        pr_url = apply_updates(repo, results, args.use_claude)
        print("DRAFT PR:", pr_url)

    return 2 if any(r.category == "major" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
