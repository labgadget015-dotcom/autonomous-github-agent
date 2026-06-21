#!/usr/bin/env python3
"""
auto_pr.py — generates a draft PR from a DRC recommendation.

Safety gates (ALL must pass):
  1. Issue must be labeled `auto-pr-candidate` (explicit user authorization)
  2. Risk score of proposed files < 3.0 (LOW band)
  3. DRY_RUN env var must be "false" to create the actual PR

Usage (via GitHub Actions workflow_dispatch):
  python .github/scripts/auto_pr.py \
    --issue 42 \
    --recommendation "Add retry logic to the HTTP client in core/http_client.py"
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
import urllib.request

DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_PAT", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
REPO = os.getenv("GITHUB_REPOSITORY", "")
AUTO_PR_LABEL = "auto-pr-candidate"
RISK_THRESHOLD = 3.0


# ---------- GitHub helpers ----------


def gh(method: str, path: str, body: dict | None = None) -> dict | list:
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_issue(number: int) -> dict:
    return gh("GET", f"/repos/{REPO}/issues/{number}")  # type: ignore[return-value]


def has_label(issue: dict, label: str) -> bool:
    return any(lb["name"] == label for lb in issue.get("labels", []))


def post_comment(issue_number: int, body: str) -> None:
    gh("POST", f"/repos/{REPO}/issues/{issue_number}/comments", {"body": body})


def create_pr(title: str, head: str, base: str, body: str) -> str:
    resp = gh(
        "POST",
        f"/repos/{REPO}/pulls",
        {"title": title, "head": head, "base": base, "body": body, "draft": True},
    )
    return resp["html_url"]  # type: ignore[index]


# ---------- LLM helpers ----------


def ask_claude(prompt: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    payload = json.dumps(
        {
            "model": "claude-sonnet-4-6",
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["content"][0]["text"]


# ---------- Risk scoring (path-based) ----------

import re as _re

_PROTECTED = _re.compile(
    r"(\.github/workflows|\.github/actions|config/|core/policy|core/risk|"
    r"requirements.*\.txt|pyproject\.toml|Dockerfile|\.env)",
    _re.IGNORECASE,
)


def estimate_risk(paths: list[str]) -> float:
    """Simple path-based risk estimate; returns 0–10 score."""
    if not paths:
        return 5.0
    score = 0.0
    for p in paths:
        if _PROTECTED.search(p):
            score += 4.0
        elif p.endswith((".sql", ".sh", ".bash")):
            score += 3.0
        elif p.startswith("tests/") or p.endswith(".md"):
            score += 0.5
        else:
            score += 1.5
    return min(score / len(paths), 10.0)


# ---------- Code generation ----------

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an AI code contributor. Given an issue description and a DRC recommendation,
    produce ONLY a JSON object with two keys:
      "files": list of {"path": str, "content": str} — the full new content of each file to change
      "branch_suffix": str — a short kebab-case label for the branch name (max 30 chars)
    Do not change .github/workflows/, config/, core/policy_engine.py, or core/risk_scorer.py.
    Limit changes to at most 3 files. Keep diffs minimal. Return valid JSON only.
"""
).strip()


def generate_fix(issue: dict, recommendation: str) -> dict:
    prompt = (
        f"Issue title: {issue['title']}\n"
        f"Issue body: {(issue.get('body') or '')[:800]}\n\n"
        f"DRC recommendation: {recommendation}\n\n"
        f"Repo: {REPO}\n\n"
        "Produce the JSON fix as instructed."
    )
    raw = ask_claude(f"{SYSTEM_PROMPT}\n\n{prompt}")
    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw.strip())


# ---------- Git helpers ----------


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=check)
    return result.stdout.strip()


def apply_files(files: list[dict]) -> list[str]:
    paths = []
    for f in files:
        path = f["path"]
        import pathlib

        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(path).write_text(f["content"], encoding="utf-8")
        paths.append(path)
    return paths


# ---------- Main ----------


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--recommendation", required=True)
    args = parser.parse_args()

    if not REPO:
        print("GITHUB_REPOSITORY not set", file=sys.stderr)
        sys.exit(1)
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN / GH_PAT not set", file=sys.stderr)
        sys.exit(1)

    issue = get_issue(args.issue)

    # Gate 1: explicit label required
    if not has_label(issue, AUTO_PR_LABEL):
        print(f"Issue #{args.issue} does not have the `{AUTO_PR_LABEL}` label — skipping.")
        sys.exit(0)

    print(f"Generating fix for issue #{args.issue}: {issue['title']}")
    fix = generate_fix(issue, args.recommendation)

    files = fix.get("files", [])
    branch_suffix = fix.get("branch_suffix", f"issue-{args.issue}")
    changed_paths = [f["path"] for f in files]

    # Gate 2: risk check
    risk = estimate_risk(changed_paths)
    print(f"Risk score for {changed_paths}: {risk:.1f}")
    if risk >= RISK_THRESHOLD:
        msg = (
            f"🤖 **Auto-PR skipped** — risk score `{risk:.1f}` exceeds threshold `{RISK_THRESHOLD}`.\n\n"
            f"Proposed changes: {', '.join(f'`{p}`' for p in changed_paths)}\n\n"
            f"DRC recommendation: {args.recommendation}"
        )
        post_comment(args.issue, msg)
        print("Risk too high — commented on issue and skipped.")
        sys.exit(0)

    branch = f"agent/auto-pr-{args.issue}-{branch_suffix}"

    if DRY_RUN:
        print(f"DRY RUN: would create branch `{branch}` with changes to {changed_paths}")
        for f in files:
            print(f"  {f['path']} ({len(f['content'])} chars)")
        post_comment(
            args.issue,
            f"🤖 **Auto-PR dry run** — would create branch `{branch}` changing:\n"
            + "\n".join(f"- `{p}`" for p in changed_paths)
            + f"\n\nRisk score: `{risk:.1f}` (LOW)\n\nSet `DRY_RUN=false` to create the actual PR.",
        )
        return

    # Apply changes
    git("config", "user.name", "GadgetLab Agent")
    git("config", "user.email", "labgadget015@gmail.com")
    git("checkout", "-b", branch)
    apply_files(files)
    git("add", *changed_paths)
    git("commit", "-m", f"fix: auto-fix for issue #{args.issue} [agent]")
    git("push", "origin", branch)

    # Create draft PR
    pr_body = (
        f"Closes #{args.issue}\n\n"
        f"## DRC Recommendation\n{args.recommendation}\n\n"
        f"## Changes\n"
        + "\n".join(f"- `{p}`" for p in changed_paths)
        + f"\n\n**Risk score:** `{risk:.1f}` (LOW)\n\n"
        "---\n_Generated by GadgetLab autonomous agent — review before merging._"
    )
    pr_url = create_pr(
        title=f"fix: auto-fix for issue #{args.issue}",
        head=branch,
        base="main",
        body=pr_body,
    )
    print(f"✅ Draft PR created: {pr_url}")
    post_comment(args.issue, f"🤖 **Draft PR created:** {pr_url}")


if __name__ == "__main__":
    main()
