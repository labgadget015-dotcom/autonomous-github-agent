#!/usr/bin/env python3
"""Triage Agent — classifies GitHub issues via LLM and reports LLM costs to Slack."""

import argparse
import asyncio
import json
import logging
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agent_base import BaseAgent  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRIAGE_SYSTEM = (
    "You are an issue triage assistant. Given an issue title and body, "
    'respond with a JSON object: {"type": "bug|feature|debt|security|ci", '
    '"priority": "P0|P1|P2", "reason": "one sentence"}. '
    "P0=critical/urgent, P1=important, P2=nice-to-have."
)

PRIORITY_KEYWORDS = {
    "P0": ["critical", "crash", "data loss", "security", "outage", "urgent", "blocker"],
    "P1": ["important", "regression", "broken", "failing", "high priority"],
}


class TriageAgent(BaseAgent):
    """Classifies issues via LLM and sends cost reports to Slack."""

    def __init__(self, config: dict[str, Any]):
        super().__init__("triage_agent", config)

    def get_supported_actions(self) -> list:
        return ["triage_issue", "cost_report"]

    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action")
        if action == "triage_issue":
            return await self._triage_issue(task.get("params", {}))
        if action == "cost_report":
            return await self._cost_report(task.get("params", {}))
        raise ValueError(f"Unsupported action: {action}")

    def _keyword_priority(self, text: str) -> str | None:
        """Override LLM priority based on keyword matching."""
        lower = text.lower()
        for priority, keywords in PRIORITY_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return priority
        return None

    async def _triage_issue(self, params: dict[str, Any]) -> dict[str, Any]:
        """Classify an issue and apply GitHub labels."""
        repo_name = params["repo"]
        issue_number = int(params["issue_number"])

        repo = self.github.client.get_repo(repo_name)
        issue = repo.get_issue(issue_number)

        prompt = f"Title: {issue.title}\n\nBody:\n{issue.body or '(no body)'}"
        llm_response = await self.llm.generate(
            prompt=prompt,
            system_prompt=TRIAGE_SYSTEM,
            max_tokens=200,
            temperature=0.1,
        )

        # Parse LLM JSON — fall back gracefully
        try:
            classification = json.loads(llm_response["content"])
        except (json.JSONDecodeError, KeyError):
            classification = {
                "type": "feature",
                "priority": "P2",
                "reason": "parse error",
            }

        issue_type = classification.get("type", "feature")
        priority = classification.get("priority", "P2")

        # Keyword override for priority
        kw_priority = self._keyword_priority(f"{issue.title} {issue.body or ''}")
        if kw_priority:
            priority = kw_priority

        # Ensure labels exist and apply them
        existing_labels = {lbl.name for lbl in repo.get_labels()}
        for label_name in (issue_type, priority):
            if label_name not in existing_labels:
                repo.create_label(label_name, "ededed")
        issue.add_to_labels(issue_type, priority)

        logger.info("Triaged issue #%d as %s/%s", issue_number, issue_type, priority)
        return {
            "issue": issue_number,
            "type": issue_type,
            "priority": priority,
            "reason": classification.get("reason", ""),
        }

    def _load_costs(self, days: int = 30) -> list[dict[str, Any]]:
        """Read .llm_costs.jsonl and return records from the last *days* days."""
        costs_path = project_root / ".llm_costs.jsonl"
        cutoff = datetime.now() - timedelta(days=days)
        records: list[dict] = []
        if not costs_path.exists():
            return records
        for line in costs_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = datetime.fromisoformat(rec["timestamp"])
                if ts >= cutoff:
                    records.append(rec)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        return records

    async def _cost_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Aggregate LLM costs for the last 30 days and post to Slack."""
        records = self._load_costs(30)

        total_cost = sum(r.get("cost_usd", 0) for r in records)
        total_input = sum(r.get("input_tokens", 0) for r in records)
        total_output = sum(r.get("output_tokens", 0) for r in records)

        by_model: dict[str, float] = {}
        for r in records:
            model = r.get("model", "unknown")
            by_model[model] = by_model.get(model, 0) + r.get("cost_usd", 0)

        model_lines = "\n".join(
            f"  • {m}: ${c:.4f}"
            for m, c in sorted(by_model.items(), key=lambda x: -x[1])
        )

        message = (
            f"*LLM Cost Report — last 30 days*\n"
            f"Total: *${total_cost:.4f}*\n"
            f"Tokens in/out: {total_input:,} / {total_output:,}\n"
            f"By model:\n{model_lines or '  (no data)'}\n"
            f"Records: {len(records)}"
        )

        slack_url = os.getenv("SLACK_WEBHOOK_URL", "")
        if slack_url:
            payload = json.dumps({"text": message}).encode()
            req = urllib.request.Request(
                slack_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
            logger.info("Posted cost report to Slack (HTTP %d)", status)
        else:
            logger.warning("SLACK_WEBHOOK_URL not set — printing report instead")
            print(message)
            status = 0
        return {
            "total_cost_usd": round(total_cost, 4),
            "records": len(records),
            "slack_status": status,
        }


def main():
    parser = argparse.ArgumentParser(description="Triage issues or report LLM costs.")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument(
        "--issue", type=int, default=0, help="Issue number (triage_issue)"
    )
    parser.add_argument(
        "--action",
        choices=["triage_issue", "cost_report"],
        default="triage_issue",
        help="Action to perform",
    )
    args = parser.parse_args()

    config = {
        "github_token": os.getenv("GITHUB_TOKEN"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "llm_provider": "anthropic",
    }
    agent = TriageAgent(config)
    params: dict[str, Any] = {"repo": args.repo}
    if args.action == "triage_issue":
        params["issue_number"] = args.issue
    task = {"action": args.action, "params": params}
    result = asyncio.run(agent.execute(task))
    print(result)


if __name__ == "__main__":
    main()
