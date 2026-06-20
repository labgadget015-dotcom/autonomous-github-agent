"""Issue management and triage agent."""

from typing import Any
from github.Issue import Issue
from github.Repository import Repository
from autonomous_agent.core.base_agent import BaseAgent


class IssueManagerAgent(BaseAgent):
    """Agent for automated issue triage and management."""

    LABELS = {
        "bug": ["bug", "error", "crash", "broken", "fix"],
        "enhancement": ["feature", "enhancement", "improve", "add"],
        "documentation": ["docs", "documentation", "readme"],
        "security": ["security", "vulnerability", "cve"],
        "performance": ["performance", "slow", "optimization"],
        "question": ["question", "help", "how to"],
        "duplicate": ["duplicate", "already exists"],
    }

    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute issue management tasks."""
        repo = self.github.get_repository(repository)
        issues = self.github.get_issues(repo, state="open")

        results = {
            "repository": repository,
            "processed": 0,
            "labeled": 0,
            "duplicates_found": 0,
            "auto_closed": 0,
        }

        for issue in issues:
            if issue.pull_request:  # Skip PRs
                continue

            # Auto-label
            if not issue.labels:
                await self._auto_label_issue(issue)
                results["labeled"] += 1

            # Check for duplicates
            if await self._check_duplicate(repo, issue):
                results["duplicates_found"] += 1

            results["processed"] += 1

        self.log_action(
            action="issue_management", repository=repository, details=results
        )

        return results

    async def _auto_label_issue(self, issue: Issue) -> None:
        """Automatically label an issue based on content."""
        text = f"{issue.title} {issue.body or ''}".lower()

        labels_to_add = []

        for label, keywords in self.LABELS.items():
            if any(keyword in text for keyword in keywords):
                labels_to_add.append(label)

        if labels_to_add:
            try:
                issue.add_to_labels(*labels_to_add)
            except Exception:
                pass

    async def _check_duplicate(self, repo: Repository, issue: Issue) -> bool:
        """Check if issue is a duplicate using LLM."""
        # Get recent closed issues
        closed_issues = list(repo.get_issues(state="closed"))[:50]

        # Use LLM to detect duplicates
        prompt = f"""Is the following issue a duplicate of any previous issues?

New Issue:
Title: {issue.title}
Body: {issue.body or 'No description'}

Previous Issues:
"""
        for closed in closed_issues[:10]:
            prompt += f"- #{closed.number}: {closed.title}\n"

        prompt += "\nIf duplicate, respond with the issue number. Otherwise, respond 'NOT_DUPLICATE'."

        try:
            response = self.llm.complete(prompt)
            if "NOT_DUPLICATE" not in response and "#" in response:
                # Found duplicate - post comment
                dup_num = response.split("#")[1].split()[0]
                comment = f"This appears to be a duplicate of #{dup_num}. Please check if that issue addresses your concern."
                self.github.create_issue_comment(issue, comment)
                issue.add_to_labels("duplicate")
                return True
        except Exception:
            pass

        return False
