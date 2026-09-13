#!/usr/bin/env python3
"""
Inline PR Comment Bot
Posts inline comments on PRs with specific code quality issues and suggestions
"""

import ast
import json
import os
import re

import requests


class InlinePRCommentBot:
    """Bot that posts inline comments on PR code"""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPOSITORY")
        self.pr_number = os.getenv("PR_NUMBER")
        self.commit_sha = os.getenv("COMMIT_SHA")

        if not all([self.github_token, self.repo, self.pr_number]):
            print("⚠️  Missing required environment variables")
            print("Required: GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER")

        self.api_base = f"https://api.github.com/repos/{self.repo}"
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def load_analysis_results(self) -> list[dict]:
        """Load all analysis results and convert to comments"""
        comments = []

        # Load Flake8 results
        comments.extend(self._load_flake8_results())

        # Load Pylint results
        comments.extend(self._load_pylint_results())

        # Load Bandit results
        comments.extend(self._load_bandit_results())

        # Load complexity results
        comments.extend(self._load_complexity_results())

        return comments

    def _load_flake8_results(self) -> list[dict]:
        """Parse Flake8 results"""
        # Flake8 JSON output would be parsed here
        return []

    def _load_pylint_results(self) -> list[dict]:
        """Parse Pylint JSON results"""
        comments = []

        try:
            with open("pylint-report.json", encoding="utf-8") as f:
                results = json.load(f)

            for issue in results:
                comments.append(
                    {
                        "path": issue.get("path", ""),
                        "line": issue.get("line", 1),
                        "body": self._format_pylint_comment(issue),
                        "severity": self._map_pylint_severity(
                            issue.get("type", "convention")
                        ),
                    }
                )
        except FileNotFoundError:
            pass

        return comments

    def _load_bandit_results(self) -> list[dict]:
        """Parse Bandit security results"""
        comments = []

        try:
            with open("bandit-report.json", encoding="utf-8") as f:
                report = json.load(f)

            for issue in report.get("results", []):
                severity = issue.get("issue_severity", "LOW").lower()
                if self._is_likely_safe_b608(issue):
                    severity = "low"
                comments.append(
                    {
                        "path": issue.get("filename", ""),
                        "line": issue.get("line_number", 1),
                        "body": self._format_bandit_comment(issue),
                        "severity": severity,
                    }
                )
        except FileNotFoundError:
            pass

        return comments

    def _load_complexity_results(self) -> list[dict]:
        """Parse complexity results"""
        comments = []

        try:
            with open("complexity.json", encoding="utf-8") as f:
                data = json.load(f)

            for filepath, functions in data.items():
                for func in functions:
                    if func.get("complexity", 0) > 10:
                        comments.append(
                            {
                                "path": filepath,
                                "line": func.get("lineno", 1),
                                "body": self._format_complexity_comment(func),
                                "severity": "medium",
                            }
                        )
        except FileNotFoundError:
            pass

        return comments

    def _format_pylint_comment(self, issue: dict) -> str:
        """Format Pylint issue as PR comment"""
        symbol = issue.get("symbol", "unknown")
        message = issue.get("message", "No message")
        message_id = issue.get("message-id", "")

        comment = f"""### 🔍 Pylint: `{symbol}`

{message}

**Type:** {issue.get('type', 'convention')}
**Message ID:** `{message_id}`

<details>
<summary>How to fix</summary>

{self._get_pylint_fix_suggestion(symbol)}

</details>
"""
        return comment

    def _format_bandit_comment(self, issue: dict) -> str:
        """Format Bandit security issue as PR comment"""
        severity = issue.get("issue_severity", "LOW")
        confidence = issue.get("issue_confidence", "LOW")
        text = issue.get("issue_text", "Security issue")

        emoji = {"HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "ℹ️"}.get(severity, "ℹ️")

        comment = f"""{emoji} **Security Issue:** {text}

**Severity:** {severity}
**Confidence:** {confidence}
**CWE:** {issue.get('issue_cwe', {}).get('id', 'N/A')}

<details>
<summary>Code snippet</summary>

```python
{issue.get('code', 'N/A')}
```

</details>

<details>
<summary>Recommendation</summary>

{self._get_security_recommendation(issue)}

</details>
"""
        return comment

    def _format_complexity_comment(self, func: dict) -> str:
        """Format complexity warning as PR comment"""
        name = func.get("name", "unknown")
        complexity = func.get("complexity", 0)

        comment = f"""### 🔧 High Complexity Warning

Function `{name}` has a cyclomatic complexity of **{complexity}** (threshold: 10)

**Recommendations:**
1. Break this function into smaller, focused functions
2. Extract complex conditional logic into separate functions
3. Use early returns to reduce nesting
4. Consider using design patterns (Strategy, Command, etc.)

**Complexity Guide:**
- 1-5: Simple, low risk
- 6-10: Moderate complexity
- 11-20: High complexity, consider refactoring
- 21+: Very high complexity, definitely refactor
"""
        return comment

    def _get_pylint_fix_suggestion(self, symbol: str) -> str:
        """Get fix suggestion for Pylint symbol"""
        suggestions = {
            "line-too-long": "Break the line at logical points or use implicit string concatenation.",
            "missing-docstring": "Add a docstring explaining what this code does.",
            "invalid-name": "Rename to follow PEP 8 naming conventions (snake_case for functions/variables).",
            "unused-variable": "Remove this variable if unused, or prefix with underscore if intentionally unused.",
            "undefined-variable": "Define this variable before using it.",
            "trailing-whitespace": "Remove trailing whitespace from the line.",
            "no-else-return": "Remove the else clause; it's unnecessary after a return statement.",
        }

        return suggestions.get(
            symbol, "Check Pylint documentation for details on how to fix this issue."
        )

    def _get_security_recommendation(self, issue: dict) -> str:
        """Get security fix recommendation"""
        test_id = issue.get("test_id", "")

        if self._is_likely_safe_b608(issue):
            return (
                "This B608 finding already shows a parameterized query pattern "
                "(for example `cursor.execute(query, params)`). Keep values bound "
                "separately, and only allowlist any dynamic table/column identifiers "
                "from trusted code-defined names."
            )

        recommendations = {
            "B101": "Avoid using assert statements in production code. Use proper error handling.",
            "B201": "Never enable debug mode in production Flask applications.",
            "B301": "Avoid using pickle for untrusted data. Use JSON instead.",
            "B303": "MD5 is cryptographically broken. Use SHA-256 or better.",
            "B311": "Use secrets.SystemRandom() for cryptographic randomness, not random.",
            "B501": "Always verify SSL certificates in production.",
            "B601": "Avoid shell=True in subprocess calls. Use a list of arguments instead.",
            "B602": "Avoid using shell=True. It can lead to shell injection vulnerabilities.",
            "B608": "Avoid building SQL values into query strings. Keep values parameterized and restrict any dynamic identifiers to an allowlist.",
        }

        return recommendations.get(
            test_id, "Review the security documentation for this issue type."
        )

    @staticmethod
    def _is_likely_safe_b608(issue: dict) -> bool:
        """Detect Bandit B608 findings that already use a bound-parameter execute call."""
        if issue.get("test_id") != "B608":
            return False

        code = str(issue.get("code", ""))
        if not code:
            return False

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False

        literal_queries: dict[str, str] = {}

        for stmt in tree.body:
            for target, value in InlinePRCommentBot._iter_name_assignments(stmt):
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    literal_queries[target] = value.value
                else:
                    literal_queries.pop(target, None)

            for node in ast.walk(stmt):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"execute", "executemany"}
                    and len(node.args) >= 2
                ):
                    first_arg = node.args[0]
                    query_text = None
                    if isinstance(first_arg, ast.Constant) and isinstance(
                        first_arg.value, str
                    ):
                        query_text = first_arg.value
                    elif isinstance(first_arg, ast.Name):
                        query_text = literal_queries.get(first_arg.id)

                    if query_text and any(
                        re.search(pattern, query_text)
                        for pattern in (r"%s", r"%\([^)]+\)s", r"\?", r":[A-Za-z_]\w*")
                    ):
                        return True

        return False

    @staticmethod
    def _iter_name_assignments(stmt: ast.stmt) -> list[tuple[str, ast.AST]]:
        """Return simple name assignments from a statement in execution order."""
        if isinstance(stmt, ast.Assign):
            return [
                (target.id, stmt.value)
                for target in stmt.targets
                if isinstance(target, ast.Name)
            ]
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            value = stmt.value if stmt.value is not None else ast.Constant(value=None)
            return [(stmt.target.id, value)]
        if isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
            return [(stmt.target.id, stmt.value)]
        return []

    def _map_pylint_severity(self, pylint_type: str) -> str:
        """Map Pylint type to severity"""
        mapping = {
            "error": "high",
            "warning": "medium",
            "refactor": "low",
            "convention": "low",
            "info": "low",
        }
        return mapping.get(pylint_type.lower(), "low")

    def post_review_comments(self, comments: list[dict]) -> int:
        """Post review comments to PR"""
        if not all([self.github_token, self.repo, self.pr_number]):
            print("⚠️  Cannot post comments: missing configuration")
            return 0

        # Filter and deduplicate comments
        unique_comments = self._deduplicate_comments(comments)

        # Group by severity and limit
        critical_comments = [
            c for c in unique_comments if c["severity"] in ["high", "critical"]
        ]
        other_comments = [
            c for c in unique_comments if c["severity"] not in ["high", "critical"]
        ]

        # Post critical comments always, limit others
        comments_to_post = critical_comments + other_comments[:10]

        posted_count = 0

        for comment in comments_to_post:
            success = self._post_single_comment(comment)
            if success:
                posted_count += 1

        # Post summary comment
        self._post_summary_comment(len(unique_comments), posted_count)

        return posted_count

    def _deduplicate_comments(self, comments: list[dict]) -> list[dict]:
        """Remove duplicate comments for same file/line"""
        seen = set()
        unique = []

        for comment in comments:
            key = (comment["path"], comment["line"])
            if key not in seen:
                seen.add(key)
                unique.append(comment)

        return unique

    def _post_single_comment(self, comment: dict) -> bool:
        """Post a single review comment"""
        url = f"{self.api_base}/pulls/{self.pr_number}/comments"

        payload = {
            "body": comment["body"],
            "path": comment["path"],
            "line": comment["line"],
            "side": "RIGHT",
        }

        if self.commit_sha:
            payload["commit_id"] = self.commit_sha

        try:
            response = requests.post(
                url, headers=self.headers, json=payload, timeout=30
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to post comment: {e}")
            return False

    def _post_summary_comment(self, total: int, posted: int):
        """Post summary comment on PR"""
        url = f"{self.api_base}/issues/{self.pr_number}/comments"

        body = f"""## 🤖 Code Quality Review Summary

**Total Issues Found:** {total}
**Comments Posted:** {posted}

The inline comments show critical and high-priority issues.
{'Additional issues were found but not displayed to keep the review focused.' if total > posted else ''}

To see all issues, check the workflow artifacts.
"""

        try:
            requests.post(url, headers=self.headers, json={"body": body}, timeout=30)
        except requests.exceptions.RequestException:
            pass


def main():
    """Main entry point"""
    print("🤖 Starting inline PR comment bot...")

    bot = InlinePRCommentBot()

    # Load analysis results
    comments = bot.load_analysis_results()
    print(f"📋 Found {len(comments)} potential issues to comment on")

    # Post comments
    posted = bot.post_review_comments(comments)
    print(f"✅ Posted {posted} inline comments")

    # Save comment data for reference
    with open("pr-comments.json", "w", encoding="utf-8") as f:
        json.dump(comments, f, indent=2)

    print("✅ Inline comment bot complete")


if __name__ == "__main__":
    main()
