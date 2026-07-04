#!/usr/bin/env python3
"""
Tier Classifier for Dependabot PRs.

Reads PR metadata from environment variables (set by the calling workflow or
by dependabot/fetch-metadata) and writes a tier classification + merge
decision to GITHUB_OUTPUT.

Environment variables consumed
-------------------------------
PR_TITLE          : Full PR title (e.g. "chore(deps): bump stripe from 8.1.0 to 9.0.0")
UPDATE_TYPE       : semver classification from dependabot/fetch-metadata:
                    "version-update:semver-patch", "version-update:semver-minor",
                    "version-update:semver-major", or empty string for non-dep PRs
DEPENDENCY_NAMES  : comma-separated list of dependency names (from fetch-metadata)
PACKAGE_ECOSYSTEM : ecosystem string ("pip", "npm", "actions", …)
EXCEPTIONS_FILE   : path to YAML blocklist (default: .github/dependabot-exceptions.yml)
DRY_RUN           : "true" / "false" (default: "true")

Outputs written to GITHUB_OUTPUT
---------------------------------
tier              : "1" (safe auto-merge), "2" (needs review)
merge_decision    : "auto-merge" or "needs-review"
reason            : human-readable explanation
blocklisted_names : comma-separated names that hit the blocklist (may be empty)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_exceptions(path: str) -> dict[str, list[str]]:
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {k: [str(v).lower() for v in vs] for k, vs in data.items() if isinstance(vs, list)}


def _is_blocklisted(
    dep_names: list[str],
    ecosystem: str,
    exceptions: dict[str, list[str]],
) -> list[str]:
    blocked: list[str] = []
    ecosystem_key = ecosystem.lower() if ecosystem else ""
    blocklist = exceptions.get(ecosystem_key, [])
    for name in dep_names:
        if name.lower() in blocklist:
            blocked.append(name)
    return blocked


def _write_outputs(outputs: dict[str, str]) -> None:
    out_file = os.environ.get("GITHUB_OUTPUT")
    if out_file:
        with open(out_file, "a", encoding="utf-8") as f:
            for key, val in outputs.items():
                f.write(f"{key}={val}\n")
    for key, val in outputs.items():
        print(f"  {key}={val}")


def _write_summary(lines: list[str]) -> None:
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    content = "\n".join(lines)
    print(content)
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(content + "\n")


# ---------------------------------------------------------------------------
# Main classification logic
# ---------------------------------------------------------------------------

def classify() -> None:
    pr_title = os.environ.get("PR_TITLE", "")
    update_type = os.environ.get("UPDATE_TYPE", "")
    dependency_names_raw = os.environ.get("DEPENDENCY_NAMES", "")
    ecosystem = os.environ.get("PACKAGE_ECOSYSTEM", "pip")
    exceptions_file = os.environ.get(
        "EXCEPTIONS_FILE", ".github/dependabot-exceptions.yml"
    )
    dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"

    dep_names = [n.strip() for n in dependency_names_raw.split(",") if n.strip()]

    exceptions = _load_exceptions(exceptions_file)
    blocklisted = _is_blocklisted(dep_names, ecosystem, exceptions)

    # Determine update class from fetch-metadata output
    is_patch = "semver-patch" in update_type
    is_minor = "semver-minor" in update_type
    is_major = "semver-major" in update_type

    # Classification
    if blocklisted:
        tier = "2"
        merge_decision = "needs-review"
        reason = (
            f"Blocklisted package(s) require human review: "
            f"{', '.join(blocklisted)}"
        )
    elif is_major:
        tier = "2"
        merge_decision = "needs-review"
        reason = "Major version bump detected — potential breaking changes."
    elif is_patch or is_minor:
        tier = "1"
        merge_decision = "auto-merge"
        reason = (
            f"{'Patch' if is_patch else 'Minor'} version bump from a "
            f"non-blocklisted package — safe to auto-merge."
        )
    else:
        # Unknown / non-Dependabot PR or no update-type info
        tier = "2"
        merge_decision = "needs-review"
        reason = (
            "Non-Dependabot PR or unrecognised update type "
            f"(update_type={update_type!r}) — routing to human review."
        )

    summary_lines = [
        "## 🤖 Tier Classifier Result",
        "",
        f"**PR title:** {pr_title}",
        f"**Dependencies:** {', '.join(dep_names) or '(none detected)'}",
        f"**Ecosystem:** {ecosystem}",
        f"**Update type:** {update_type or '(unknown)'}",
        f"**Blocklisted:** {', '.join(blocklisted) or 'none'}",
        "",
        f"### Decision: Tier {tier} — `{merge_decision}`",
        f"**Reason:** {reason}",
        "",
        f"**Dry-run mode:** {dry_run}",
    ]
    if dry_run:
        summary_lines.append(
            "\n> ⚠️ Dry-run is ON — merge command will be logged but not executed."
        )

    _write_summary(summary_lines)
    _write_outputs(
        {
            "tier": tier,
            "merge_decision": merge_decision,
            "reason": reason.replace("\n", " "),
            "blocklisted_names": ",".join(blocklisted),
        }
    )


if __name__ == "__main__":
    try:
        classify()
    except (OSError, yaml.YAMLError) as exc:
        print(f"::error::tier_classifier.py I/O or YAML error: {exc}", file=sys.stderr)
        sys.exit(1)
