#!/usr/bin/env python3
"""
Weekly Repo Digest — formats overseer-results.json as a Slack Block Kit message.
Run after repository-overseer.yml. Requires SLACK_WEBHOOK_URL env var.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime


def load_results(path: str = "overseer-results.json") -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Results file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def health_grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def build_blocks(data: dict) -> list:
    analyses = data.get("analyses", {})
    recommendations = data.get("recommendations", [])
    timestamp = data.get("timestamp", datetime.utcnow().isoformat())
    repo = os.getenv("GITHUB_REPOSITORY", "your-repo")
    run_url = f"https://github.com/{repo}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"

    # Compute overall health score from code analysis
    code = analyses.get("code", {})
    quality_score = code.get("code_quality_score", code.get("quality_score", 0)) or 0
    grade = health_grade(quality_score)

    critical = [r for r in recommendations if r.get("priority") == "critical"]
    high = [r for r in recommendations if r.get("priority") == "high"]
    deps = analyses.get("dependencies", {})
    vulns = deps.get("vulnerable_packages", [])

    blocks = []

    # Header
    blocks.append(
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🤖 GadgetLab Weekly Repo Digest"},
        }
    )

    # Score summary
    score_text = (
        f"*Health Score:* `{quality_score}/100` — *{grade}*\n"
        f"*Date:* {timestamp[:10]}\n"
        f"*Repo:* `{repo}`"
    )
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": score_text}})

    blocks.append({"type": "divider"})

    # Code quality
    if code:
        refactor = len(code.get("refactoring_opportunities", []))
        arch = len(code.get("architectural_improvements", []))
        perf = len(code.get("performance_optimizations", []))
        code_text = (
            f"*📊 Code Quality*\n"
            f"• Refactoring opportunities: {refactor}\n"
            f"• Architecture improvements: {arch}\n"
            f"• Performance issues: {perf}"
        )
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": code_text}}
        )

    # Security / dependencies
    if deps:
        outdated = len(deps.get("outdated_packages", []))
        vuln_line = f"⚠️ {len(vulns)} vulnerable" if vulns else "✅ No vulnerabilities"
        dep_text = (
            f"*📦 Dependencies*\n" f"• {vuln_line}\n" f"• Outdated packages: {outdated}"
        )
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": dep_text}})

    # Critical findings
    if critical:
        crit_lines = "\n".join(f"• {r.get('message', '')}" for r in critical[:5])
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔴 Critical Issues*\n{crit_lines}",
                },
            }
        )

    # Top recommendations
    if high:
        high_lines = "\n".join(f"• {r.get('message', '')}" for r in high[:5])
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*🟡 High Priority*\n{high_lines}"},
            }
        )

    if not critical and not high:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✅ *No critical or high-priority issues this week.*",
                },
            }
        )

    blocks.append({"type": "divider"})

    # Footer with link
    blocks.append(
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"<{run_url}|View full analysis →>"},
        }
    )

    return blocks


def send_to_slack(webhook_url: str, blocks: list) -> None:
    payload = json.dumps({"blocks": blocks}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Slack returned {resp.status}")
    print("✅ Weekly digest sent to Slack")


def main():
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("SLACK_WEBHOOK_URL not set — skipping digest", file=sys.stderr)
        sys.exit(0)

    results_path = sys.argv[1] if len(sys.argv) > 1 else "overseer-results.json"
    data = load_results(results_path)
    blocks = build_blocks(data)
    send_to_slack(webhook_url, blocks)


if __name__ == "__main__":
    main()
