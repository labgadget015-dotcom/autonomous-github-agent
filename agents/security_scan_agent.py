#!/usr/bin/env python3
"""Security Scan Agent — runs bandit + pip-audit and reports to GitHub."""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agent_base import BaseAgent  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityScanAgent(BaseAgent):
    """Runs bandit and pip-audit then posts results to GitHub."""

    def __init__(self, config: dict[str, Any]):
        super().__init__("security_scan_agent", config)

    def get_supported_actions(self) -> list:
        return ["scan_repo"]

    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action")
        if action == "scan_repo":
            return await self._scan_repo(task.get("params", {}))
        raise ValueError(f"Unsupported action: {action}")

    def _run_bandit(self) -> dict[str, Any]:
        """Run bandit and return parsed JSON results."""
        subprocess.run(
            ["bandit", "-r", ".", "-f", "json", "-o", "/tmp/bandit.json"],
            capture_output=True,
        )
        try:
            with open("/tmp/bandit.json") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _run_pip_audit(self) -> list[dict[str, Any]]:
        """Run pip-audit and return parsed JSON results."""
        subprocess.run(
            ["pip-audit", "--format", "json", "--output", "/tmp/pip-audit.json"],
            capture_output=True,
        )
        try:
            with open("/tmp/pip-audit.json") as f:
                data = json.load(f)
            return data if isinstance(data, list) else data.get("dependencies", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _format_summary(
        self, bandit_data: dict[str, Any], pip_data: list[dict[str, Any]]
    ) -> str:
        """Build a markdown security summary."""
        lines = ["## Security Scan Report\n"]

        # Bandit section
        results = bandit_data.get("results", [])
        metrics = bandit_data.get("metrics", {})
        total_issues = (
            sum(
                v.get("SEVERITY.HIGH", 0)
                + v.get("SEVERITY.MEDIUM", 0)
                + v.get("SEVERITY.LOW", 0)
                for v in metrics.values()
            )
            if metrics
            else len(results)
        )
        lines.append(f"### Bandit — {total_issues} issue(s) found\n")
        for item in results[:20]:
            sev = item.get("issue_severity", "?")
            conf = item.get("issue_confidence", "?")
            text = item.get("issue_text", "")
            fname = item.get("filename", "")
            lineno = item.get("line_number", "")
            lines.append(f"- **[{sev}/{conf}]** `{fname}:{lineno}` — {text}")

        # pip-audit section
        vuln_pkgs = [d for d in pip_data if d.get("vulns")]
        lines.append(f"\n### pip-audit — {len(vuln_pkgs)} vulnerable package(s)\n")
        for dep in vuln_pkgs:
            pkg = dep.get("name", "?")
            ver = dep.get("version", "?")
            for v in dep.get("vulns", []):
                vid = v.get("id", "?")
                fix = ", ".join(v.get("fix_versions", [])) or "none"
                lines.append(f"- **{pkg}=={ver}** {vid} (fix: {fix})")

        return "\n".join(lines)

    async def _scan_repo(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run scanners and post results to GitHub."""
        repo_name = params["repo"]
        issue_number = int(params.get("issue_number", 0))

        bandit_data = self._run_bandit()
        pip_data = self._run_pip_audit()
        summary = self._format_summary(bandit_data, pip_data)

        repo = self.github.client.get_repo(repo_name)

        if issue_number > 0:
            issue = repo.get_issue(issue_number)
            issue.create_comment(summary)
            logger.info("Posted security scan to issue #%d", issue_number)
            return {"repo": repo_name, "posted_to_issue": issue_number}
        else:
            issue = repo.create_issue(
                title="Security Scan Results",
                body=summary,
                labels=["security"],
            )
            logger.info("Created security issue #%d", issue.number)
            return {"repo": repo_name, "created_issue": issue.number}


def main():
    parser = argparse.ArgumentParser(
        description="Run security scans and report to GitHub."
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument(
        "--issue",
        type=int,
        default=0,
        help="Issue number to comment on (0 = create new issue)",
    )
    args = parser.parse_args()

    config = {
        "github_token": os.getenv("GITHUB_TOKEN"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
    }
    agent = SecurityScanAgent(config)
    task = {
        "action": "scan_repo",
        "params": {"repo": args.repo, "issue_number": args.issue},
    }
    result = asyncio.run(agent.execute(task))
    print(result)


if __name__ == "__main__":
    main()
