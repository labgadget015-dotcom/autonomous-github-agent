#!/usr/bin/env python3
"""
PR Inline Commenter Bot
Provides proactive inline feedback on pull requests with code quality, security, and complexity issues.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import requests


class PRInlineCommenter:
    """Posts inline comments on PRs for issues detected by analysis tools."""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPOSITORY")
        self.pr_number = os.getenv("PR_NUMBER")
        self.commit_sha = os.getenv("COMMIT_SHA")
        self.api_base = "https://api.github.com"

        if not all([self.github_token, self.repo, self.pr_number, self.commit_sha]):
            print("⚠️  Missing required environment variables")
            sys.exit(0)  # Don't fail the workflow

    def _get_headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, data: dict = None) -> Any:
        """Make authenticated request to GitHub API."""
        url = f"{self.api_base}/repos/{self.repo}/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self._get_headers(), timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json() if response.text else None
        except requests.exceptions.RequestException as e:
            print(f"⚠️  API request failed: {e}")
            return None

    def parse_pylint_report(self, report_path: Path) -> list[dict]:
        """Parse Pylint JSON report and extract actionable issues."""
        comments = []
        try:
            with open(report_path, encoding="utf-8") as f:
                data = json.load(f)

            for issue in data:
                if isinstance(issue, dict):
                    comments.append(
                        {
                            "path": issue.get("path", "").replace("./", ""),
                            "line": issue.get("line", 1),
                            "body": f"🔍 **Pylint**: {issue.get('message', 'Issue detected')}\\n"
                            f"**Type**: `{issue.get('message-id', 'unknown')}`\\n"
                            f"**Severity**: {issue.get('type', 'info')}",
                            "severity": issue.get("type", "info"),
                        }
                    )
        except Exception as e:
            print(f"⚠️  Error parsing Pylint report: {e}")

        return comments

    def parse_bandit_report(self, report_path: Path) -> list[dict]:
        """Parse Bandit JSON report and extract security issues."""
        comments = []
        try:
            with open(report_path, encoding="utf-8") as f:
                data = json.load(f)

            for issue in data.get("results", []):
                severity = issue.get("issue_severity", "LOW")
                icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")

                comments.append(
                    {
                        "path": issue.get("filename", "").replace("./", ""),
                        "line": issue.get("line_number", 1),
                        "body": f"{icon} **Security Issue**: {issue.get('issue_text', 'Issue detected')}\\n"
                        f"**Severity**: {severity}\\n"
                        f"**Confidence**: {issue.get('issue_confidence', 'UNKNOWN')}\\n"
                        f"**CWE**: {issue.get('test_id', 'N/A')}\\n\\n"
                        f"```python\\n{issue.get('code', 'N/A')}\\n```",
                        "severity": severity,
                    }
                )
        except Exception as e:
            print(f"⚠️  Error parsing Bandit report: {e}")

        return comments

    def parse_radon_report(self, report_path: Path) -> list[dict]:
        """Parse Radon complexity report and highlight high complexity."""
        comments = []
        try:
            with open(report_path, encoding="utf-8") as f:
                data = json.load(f)

            for file_path, functions in data.items():
                if isinstance(functions, list):
                    for func in functions:
                        complexity = func.get("complexity", 0)
                        if complexity > 10:  # High complexity threshold
                            icon = "🔴" if complexity > 20 else "🟡" if complexity > 15 else "🟠"
                            comments.append(
                                {
                                    "path": file_path.replace("./", ""),
                                    "line": func.get("lineno", 1),
                                    "body": f"{icon} **High Complexity Detected**\\n"
                                    f"**Function**: `{func.get('name', 'unknown')}`\\n"
                                    f"**Cyclomatic Complexity**: {complexity}\\n"
                                    f"**Recommendation**: Consider refactoring into smaller functions.",
                                    "severity": "warning",
                                }
                            )
        except Exception as e:
            print(f"⚠️  Error parsing Radon report: {e}")

        return comments

    def post_review_comments(self, comments: list[dict]) -> None:
        """Post inline comments as a PR review."""
        if not comments:
            print("✅ No issues to comment on")
            return

        # Filter out duplicate comments and prioritize by severity
        unique_comments = {}
        for comment in comments:
            key = (comment["path"], comment["line"])
            if key not in unique_comments or comment.get("severity") == "HIGH":
                unique_comments[key] = comment

        # Limit to top 20 most critical comments to avoid spam
        sorted_comments = sorted(
            unique_comments.values(),
            key=lambda x: {"HIGH": 0, "MEDIUM": 1, "warning": 2, "info": 3}.get(
                x.get("severity", "info"), 4
            ),
        )[:20]

        # Format for GitHub PR review
        review_comments = []
        for comment in sorted_comments:
            review_comments.append(
                {
                    "path": comment["path"],
                    "line": comment["line"],
                    "body": comment["body"],
                    "side": "RIGHT",
                }
            )

        # Post as a review
        review_data = {
            "commit_id": self.commit_sha,
            "body": f"🤖 **Automated Code Analysis**\\n\\n"
            f"Found {len(unique_comments)} issues in this PR. "
            f"Showing top {len(sorted_comments)} most critical.\\n\\n"
            f"💡 Fix these issues before merging for better code quality.",
            "event": "COMMENT",
            "comments": review_comments,
        }

        result = self._make_request("POST", f"pulls/{self.pr_number}/reviews", review_data)

        if result:
            print(f"✅ Posted {len(review_comments)} inline comments on PR #{self.pr_number}")
        else:
            print("⚠️  Failed to post review comments")

    def run(self, reports_dir: Path) -> None:
        """Main execution: parse all reports and post comments."""
        all_comments = []

        print(f"🔍 Scanning reports in {reports_dir}")

        # Parse all available reports
        for report_file in reports_dir.rglob("*.json"):
            if "pylint" in report_file.name:
                all_comments.extend(self.parse_pylint_report(report_file))
            elif "bandit" in report_file.name:
                all_comments.extend(self.parse_bandit_report(report_file))
            elif "radon-cc" in report_file.name:
                all_comments.extend(self.parse_radon_report(report_file))

        print(f"📊 Found {len(all_comments)} potential issues")

        # Post comments to PR
        self.post_review_comments(all_comments)


def main():
    """Main entry point."""
    reports_dir = Path(os.getenv("REPORTS_DIR", "reports"))

    if not reports_dir.exists():
        print(f"⚠️  Reports directory {reports_dir} does not exist")
        sys.exit(0)

    commenter = PRInlineCommenter()
    commenter.run(reports_dir)


if __name__ == "__main__":
    main()
