"""GitHub API client wrapper with rate limiting and error handling."""

from typing import Any

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from tenacity import retry, stop_after_attempt, wait_exponential

from autonomous_agent.core.config import get_config


class GitHubClient:
    """Wrapper around PyGithub with enhanced features."""

    def __init__(self, token: str | None = None):
        """Initialize GitHub client."""
        config = get_config()
        self.token = token or config.github.token
        self.client = Github(self.token, timeout=config.github.timeout)
        self.user = self.client.get_user()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_repository(self, repo_name: str) -> Repository:
        """Get a repository by name (owner/repo)."""
        return self.client.get_repo(repo_name)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_pull_requests(
        self, repo: Repository, state: str = "open"
    ) -> list[PullRequest]:
        """Get pull requests from a repository."""
        return list(repo.get_pulls(state=state))

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_issues(self, repo: Repository, state: str = "open") -> list[Issue]:
        """Get issues from a repository."""
        return list(repo.get_issues(state=state))

    def create_issue_comment(self, issue: Issue, comment: str) -> None:
        """Add a comment to an issue or PR."""
        issue.create_comment(comment)

    def create_pr_review_comment(
        self, pr: PullRequest, body: str, commit_id: str, path: str, line: int
    ) -> None:
        """Create an inline review comment on a PR."""
        pr.create_review_comment(body=body, commit_id=commit_id, path=path, line=line)

    def get_rate_limit(self) -> dict[str, Any]:
        """Get current API rate limit status."""
        rate_limit = self.client.get_rate_limit()
        return {
            "core": {
                "remaining": rate_limit.core.remaining,
                "limit": rate_limit.core.limit,
                "reset": rate_limit.core.reset,
            }
        }

    def close(self) -> None:
        """Close the GitHub client connection."""
        self.client.close()
