#!/usr/bin/env python3
"""Dependency Agent — audits vulnerabilities and unpinned packages, reports to GitHub."""

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


class DependencyAgent(BaseAgent):
    """Checks dependencies for vulnerabilities and loose pins."""

    def __init__(self, config: dict[str, Any]):
        super().__init__("dependency_agent", config)

    def get_supported_actions(self) -> list:
        return ["check_dependencies"]

    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action")
        if action == "check_dependencies":
            return await self._check_dependencies(task.get("params", {}))
        raise ValueError(f"Unsupported action: {action}")

    def _run_pip_audit(self) -> list[dict[str, Any]]:
        """Run pip-audit and return results list."""
        result = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True,
            text=True,
        )
        try:
            data = json.loads(result.stdout)
            return data if isinstance(data, list) else data.get("dependencies", [])
        except (json.JSONDecodeError, AttributeError):
            return []

    def _check_unpinned(self, req_path: Path) -> list[str]:
        """Return package lines without an upper bound pin."""
        unpinned: list[str] = []
        if not req_path.exists():
            return unpinned
        for line in req_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Has no upper bound if missing <= or ~= or == with no upper range
            if ">=" in line and "<" not in line and "~=" not in line:
                unpinned.append(line)
            elif (
                "==" not in line
                and ">=" not in line
                and "~=" not in line
                and "<" not in line
            ):
                unpinned.append(line)
        return unpinned

    def _build_report(
        self, audit_data: list[dict[str, Any]], unpinned: list[str]
    ) -> str:
        """Format a markdown dependency report."""
        lines = ["## Dependency Audit Report\n"]

        vuln_pkgs = [d for d in audit_data if d.get("vulns")]
        lines.append(f"### Vulnerabilities — {len(vuln_pkgs)} package(s) affected\n")
        lines.append("| Package | Version | ID | Severity | Fix |")
        lines.append("|---------|---------|-----|----------|-----|")
        for dep in vuln_pkgs:
            pkg = dep.get("name", "?")
            ver = dep.get("version", "?")
            for v in dep.get("vulns", []):
                vid = v.get("id", "?")
                aliases = v.get("aliases") or [vid]
                sev = aliases[0]
                fix = ", ".join(v.get("fix_versions", [])) or "none"
                lines.append(f"| {pkg} | {ver} | {vid} | {sev} | {fix} |")

        lines.append(f"\n### Unpinned packages — {len(unpinned)} found\n")
        for pkg in unpinned:
            lines.append(f"- `{pkg}`")

        return "\n".join(lines)

    async def _check_dependencies(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run audit, build report, post or update GitHub issue."""
        repo_name = params["repo"]
        req_path = project_root / "requirements.txt"

        audit_data = self._run_pip_audit()
        unpinned = self._check_unpinned(req_path)
        report = self._build_report(audit_data, unpinned)

        repo = self.github.client.get_repo(repo_name)

        # Look for existing open dependency issue to update
        existing = None
        for issue in repo.get_issues(state="open", labels=["dependencies"]):
            existing = issue
            break

        if existing:
            existing.create_comment(report)
            logger.info("Updated dependency issue #%d", existing.number)
            return {"repo": repo_name, "updated_issue": existing.number}
        else:
            issue = repo.create_issue(
                title="Dependency Audit Report",
                body=report,
                labels=["dependencies"],
            )
            logger.info("Created dependency issue #%d", issue.number)
            return {"repo": repo_name, "created_issue": issue.number}


def main():
    parser = argparse.ArgumentParser(
        description="Audit dependencies and report to GitHub."
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    args = parser.parse_args()

    config = {
        "github_token": os.getenv("GITHUB_TOKEN"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
    }
    agent = DependencyAgent(config)
    task = {
        "action": "check_dependencies",
        "params": {"repo": args.repo},
    }
    result = asyncio.run(agent.execute(task))
    print(result)


if __name__ == "__main__":
    main()
