#!/usr/bin/env python3
"""
Escalation Workflow Script (Objective 5)

Automatically creates GitHub issues when code quality thresholds are violated.
This script analyzes quality metrics and escalates issues with appropriate labels
and assignees for immediate attention.
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Try importing github library
try:
    from github import Github, GithubException
except ImportError:
    print("PyGithub not installed. Install with: pip install PyGithub")
    sys.exit(1)


class QualityEscalator:
    """Handles quality metric threshold violations and issue creation."""

    def __init__(self, repo_name: str, token: str):
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)

        # Load thresholds from environment or use defaults
        self.thresholds = {
            "complexity": int(os.getenv("ESCALATE_COMPLEXITY_THRESHOLD", "20")),
            "coverage_drop": int(os.getenv("ESCALATE_COVERAGE_DROP_PERCENT", "10")),
            "quality_score": float(os.getenv("QUALITY_THRESHOLD", "7.0")),
            "max_critical_vulns": int(os.getenv("MAX_CRITICAL_VULNS", "0")),
            "max_high_vulns": int(os.getenv("MAX_HIGH_SEVERITY_VULNS", "0")),
        }

        # Issue configuration
        self.issue_labels = os.getenv("ISSUE_LABELS", "quality,automated").split(",")
        self.issue_assignees = (
            os.getenv("ISSUE_ASSIGNEES", "").split(",")
            if os.getenv("ISSUE_ASSIGNEES")
            else []
        )
        self.auto_create = os.getenv("AUTO_CREATE_ISSUES", "true").lower() == "true"

    def check_complexity_violation(self, complexity_data: dict) -> dict | None:
        """Check if code complexity exceeds threshold."""
        violations = []

        for file, metrics in complexity_data.items():
            if metrics.get("complexity", 0) > self.thresholds["complexity"]:
                violations.append(
                    {
                        "file": file,
                        "complexity": metrics["complexity"],
                        "threshold": self.thresholds["complexity"],
                    }
                )

        if violations:
            return {
                "type": "complexity",
                "severity": "high" if len(violations) > 3 else "medium",
                "violations": violations,
                "summary": f"{len(violations)} file(s) exceed complexity threshold",
            }
        return None

    def check_coverage_drop(
        self, current_coverage: float, previous_coverage: float
    ) -> dict | None:
        """Check if test coverage has dropped significantly."""
        if previous_coverage == 0:
            return None

        drop_percent = (
            (previous_coverage - current_coverage) / previous_coverage
        ) * 100

        if drop_percent > self.thresholds["coverage_drop"]:
            return {
                "type": "coverage_drop",
                "severity": "high",
                "current": current_coverage,
                "previous": previous_coverage,
                "drop": drop_percent,
                "summary": f"Test coverage dropped by {drop_percent:.1f}%",
            }
        return None

    def check_security_violations(self, security_data: dict) -> dict | None:
        """Check if security vulnerabilities exceed threshold."""
        critical = security_data.get("critical", 0)
        high = security_data.get("high", 0)

        if (
            critical > self.thresholds["max_critical_vulns"]
            or high > self.thresholds["max_high_vulns"]
        ):
            return {
                "type": "security",
                "severity": "critical" if critical > 0 else "high",
                "critical_count": critical,
                "high_count": high,
                "summary": f"{critical} critical and {high} high severity vulnerabilities found",
            }
        return None

    def check_quality_score(self, quality_score: float) -> dict | None:
        """Check if overall quality score is below threshold."""
        if quality_score < self.thresholds["quality_score"]:
            return {
                "type": "quality_score",
                "severity": "medium",
                "score": quality_score,
                "threshold": self.thresholds["quality_score"],
                "summary": f"Quality score {quality_score:.1f} below threshold {self.thresholds['quality_score']}",
            }
        return None

    def create_issue(
        self, violation: dict, pr_number: int | None = None
    ) -> str | None:
        """Create a GitHub issue for the violation."""
        if not self.auto_create:
            print(
                f"Auto-creation disabled. Would create issue for: {violation['summary']}"
            )
            return None

        # Format issue title
        severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        emoji = severity_emoji.get(violation["severity"], "⚪")
        title = f"{emoji} {violation['type'].replace('_', ' ').title()}: {violation['summary']}"

        # Format issue body
        body_parts = [
            "## Automated Quality Escalation",
            f"**Type:** {violation['type']}",
            f"**Severity:** {violation['severity'].upper()}",
            f"**Detected:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
        ]

        # Add type-specific details
        if violation["type"] == "complexity":
            body_parts.extend(
                [
                    "### Complexity Violations",
                    "",
                    "| File | Complexity | Threshold |",
                    "|------|------------|-----------|",
                ]
            )
            for v in violation["violations"][:10]:  # Limit to 10 files
                body_parts.append(
                    f"| {v['file']} | {v['complexity']} | {v['threshold']} |"
                )
            if len(violation["violations"]) > 10:
                body_parts.append(
                    f"\n*...and {len(violation['violations']) - 10} more files*"
                )

        elif violation["type"] == "coverage_drop":
            body_parts.extend(
                [
                    "### Coverage Drop Details",
                    f"- Previous Coverage: {violation['previous']:.1f}%",
                    f"- Current Coverage: {violation['current']:.1f}%",
                    f"- Drop: {violation['drop']:.1f}%",
                ]
            )

        elif violation["type"] == "security":
            body_parts.extend(
                [
                    "### Security Vulnerabilities",
                    f"- Critical: {violation['critical_count']}",
                    f"- High: {violation['high_count']}",
                    "",
                    "**Action Required:** Review and fix security vulnerabilities immediately.",
                ]
            )

        elif violation["type"] == "quality_score":
            body_parts.extend(
                [
                    "### Quality Score",
                    f"- Current Score: {violation['score']:.1f}/10",
                    f"- Threshold: {violation['threshold']:.1f}/10",
                    f"- Gap: {violation['threshold'] - violation['score']:.1f} points",
                ]
            )

        # Add PR reference if applicable
        if pr_number:
            body_parts.extend(["", f"**Related PR:** #{pr_number}"])

        # Add action items
        body_parts.extend(
            [
                "",
                "### Recommended Actions",
                "- [ ] Review the violations listed above",
                "- [ ] Create a plan to address the issues",
                "- [ ] Update the code to meet quality standards",
                "- [ ] Re-run quality checks to verify fixes",
                "",
                "---",
                "*This issue was created automatically by the quality escalation workflow.*",
            ]
        )

        body = "\n".join(body_parts)

        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=self.issue_labels,
                assignees=self.issue_assignees if self.issue_assignees else None,
            )
            print(f"✅ Created issue #{issue.number}: {title}")
            return issue.html_url
        except GithubException as e:
            print(f"❌ Failed to create issue: {e}")
            return None

    def analyze_and_escalate(self, metrics_file: str, pr_number: int | None = None):
        """Analyze metrics and create issues for violations."""
        try:
            with open(metrics_file) as f:
                metrics = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Failed to load metrics file: {e}")
            return

        violations = []

        # Check complexity
        if "complexity" in metrics:
            violation = self.check_complexity_violation(metrics["complexity"])
            if violation:
                violations.append(violation)

        # Check coverage drop
        if "coverage" in metrics and "previous_coverage" in metrics:
            violation = self.check_coverage_drop(
                metrics["coverage"], metrics["previous_coverage"]
            )
            if violation:
                violations.append(violation)

        # Check security
        if "security" in metrics:
            violation = self.check_security_violations(metrics["security"])
            if violation:
                violations.append(violation)

        # Check quality score
        if "quality_score" in metrics:
            violation = self.check_quality_score(metrics["quality_score"])
            if violation:
                violations.append(violation)

        # Create issues for violations
        if violations:
            print(f"\n🚨 Found {len(violations)} violation(s):\n")
            for violation in violations:
                print(f"  - {violation['summary']}")
                self.create_issue(violation, pr_number)
        else:
            print("✅ No quality violations detected!")


def main():
    parser = argparse.ArgumentParser(
        description="Escalate quality issues by creating GitHub issues"
    )
    parser.add_argument(
        "--metrics-file",
        required=True,
        help="Path to JSON file containing quality metrics",
    )
    parser.add_argument(
        "--pr-number", type=int, help="Pull request number if applicable"
    )
    parser.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPOSITORY"),
        help="Repository name (owner/repo)",
    )
    parser.add_argument(
        "--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub access token"
    )

    args = parser.parse_args()

    if not args.repo:
        print("❌ Repository name not provided. Use --repo or set GITHUB_REPOSITORY")
        sys.exit(1)

    if not args.token:
        print("❌ GitHub token not provided. Use --token or set GITHUB_TOKEN")
        sys.exit(1)

    escalator = QualityEscalator(args.repo, args.token)
    escalator.analyze_and_escalate(args.metrics_file, args.pr_number)


if __name__ == "__main__":
    main()
