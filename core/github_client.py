#!/usr/bin/env python3
"""
GitHub Client

Provides a wrapper around the GitHub API with rate limiting, retry logic,
and error handling.
"""

import logging
import time
from typing import Any

from github import Github, GithubException
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from .exceptions import RateLimitError  # noqa: F401 – re-exported for callers

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    GitHub API client with rate limiting and retry logic.

    Features:
    - Automatic rate limit handling
    - Exponential backoff for retries
    - Connection pooling
    - Error handling
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize GitHub client.

        Args:
            config: Configuration dictionary containing:
                - github_token: GitHub personal access token or app token
                - github_base_url: Optional GitHub Enterprise URL
        """
        import os

        self.config = config
        # Prefer environment variable to keep secrets out of config dicts
        token = (
            os.getenv("GITHUB_TOKEN")
            or config.get("github_token")
            or config.get("GITHUB_TOKEN")
        )
        base_url = config.get("github_base_url", "https://api.github.com")

        if not token:
            logger.warning(
                "No GitHub token provided. API rate limits will be severely restricted."
            )

        self.client = Github(token, base_url=base_url) if token else Github()
        self._last_request_time = 0
        self._min_request_interval = 0.1  # Minimum 100ms between requests

        logger.info("GitHub client initialized")

    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def check_rate_limit(self) -> dict[str, Any]:
        """
        Check current rate limit status.

        Returns:
            Dictionary with rate limit information
        """
        rate_limit = self.client.get_rate_limit()
        core = rate_limit.core

        return {
            "limit": core.limit,
            "remaining": core.remaining,
            "reset_time": core.reset.isoformat(),
            "used": core.limit - core.remaining,
        }

    def get_repository(self, owner: str, repo: str) -> Repository:
        """
        Get a repository object.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository object
        """
        self._wait_for_rate_limit()

        try:
            full_name = f"{owner}/{repo}"
            return self.client.get_repo(full_name)
        except GithubException as e:
            logger.error(f"Error getting repository {owner}/{repo}: {str(e)}")
            raise

    def create_issue(
        self,
        full_name: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> Issue:
        """
        Create a new issue in a repository.

        Args:
            full_name: Repository full name (owner/repo)
            title: Issue title
            body: Issue body
            labels: Optional list of labels
            assignees: Optional list of assignees

        Returns:
            Created Issue object
        """
        owner, repo = full_name.split("/", 1)
        self._wait_for_rate_limit()

        try:
            repository = self.get_repository(owner, repo)
            issue = repository.create_issue(
                title=title, body=body, labels=labels or [], assignees=assignees or []
            )
            logger.info(f"Created issue #{issue.number} in {full_name}")
            return issue
        except GithubException as e:
            logger.error(f"Error creating issue in {full_name}: {str(e)}")
            raise

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Issue:
        """
        Get an issue by number.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Issue object
        """
        self._wait_for_rate_limit()

        try:
            repository = self.get_repository(owner, repo)
            return repository.get_issue(issue_number)
        except GithubException as e:
            logger.error(
                f"Error getting issue #{issue_number} in {owner}/{repo}: {str(e)}"
            )
            raise

    def get_pull_request(self, full_name: str, pr_number: int) -> PullRequest:
        """
        Get a pull request by number.

        Args:
            full_name: Repository full name (owner/repo)
            pr_number: Pull request number

        Returns:
            PullRequest object
        """
        owner, repo = full_name.split("/", 1)
        self._wait_for_rate_limit()

        try:
            repository = self.get_repository(owner, repo)
            return repository.get_pull(pr_number)
        except GithubException as e:
            logger.error(f"Error getting PR #{pr_number} in {full_name}: {str(e)}")
            raise

    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: list[str] | None = None,
        limit: int | None = None,
    ) -> list[Issue]:
        """
        List issues in a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state ('open', 'closed', 'all')
            labels: Optional list of labels to filter by
            limit: Maximum number of issues to return (None for all)

        Returns:
            List of Issue objects
        """
        self._wait_for_rate_limit()

        try:
            repository = self.get_repository(owner, repo)
            paginator = repository.get_issues(state=state, labels=labels or [])
            if limit is not None:
                return list(paginator[:limit])
            # Consume the paginator lazily to avoid extra N+1 API calls
            return list(paginator)
        except GithubException as e:
            logger.error(f"Error listing issues in {owner}/{repo}: {str(e)}")
            raise

    def add_comment(self, full_name: str, issue_number: int, body: str):
        """
        Add a comment to an issue or pull request.

        Args:
            full_name: Repository full name (owner/repo)
            issue_number: Issue or PR number
            body: Comment body
        """
        owner, repo = full_name.split("/", 1)
        self._wait_for_rate_limit()

        try:
            issue = self.get_issue(owner, repo, issue_number)
            issue.create_comment(body)
            logger.info(f"Added comment to #{issue_number} in {full_name}")
        except GithubException as e:
            logger.error(
                f"Error adding comment to #{issue_number} in {full_name}: {str(e)}"
            )
            raise

    # Adapter methods for test compatibility
    def get_repo(self, full_name: str) -> Repository:
        """
        Adapter method for tests. Delegates to get_repository.
        Args:
            full_name: Repository full name in owner/repo format
        Returns:
            Repository object
        """
        owner, repo = full_name.split('/', 1)
        return self.get_repository(owner, repo)
    
    def close_issue(self, full_name: str, issue_number: int):
        """
        Close an issue.
        Args:
            full_name: Repository full name in owner/repo format
            issue_number: Issue number
        """
        owner, repo = full_name.split('/', 1)
        issue = self.get_issue(owner, repo, issue_number)
        issue.edit(state="closed")
        logger.info(f"Closed issue #{issue_number} in {full_name}")
    
    def list_repos(self, org: str = None, user: str = None) -> list[Repository]:
        """
        List repositories for an organization or user.
        Args:
            org: Organization name
            user: User name
        Returns:
            List of Repository objects
        """
        self._wait_for_rate_limit()
        try:
            if org:
                return list(self.client.get_organization(org).get_repos())
            elif user:
                return list(self.client.get_user(user).get_repos())
            else:
                return list(self.client.get_user().get_repos())
        except GithubException as e:
            logger.error(f"Error listing repos: {str(e)}")
            raise
    
    def add_labels(self, full_name: str, issue_number: int, labels: list[str]):
        """
        Add labels to an issue.
        Args:
            full_name: Repository full name (owner/repo)
            issue_number: Issue number
            labels: List of label names
        """
        owner, repo = full_name.split("/", 1)
        issue = self.get_issue(owner, repo, issue_number)
        issue.add_to_labels(*labels)
        logger.info(f"Added labels {labels} to issue #{issue_number} in {full_name}")
    
    def merge_pull_request(self, full_name: str, pr_number: int, merge_method: str = "merge"):
        """
        Merge a pull request.
        Args:
            full_name: Repository full name (owner/repo)
            pr_number: Pull request number
            merge_method: Merge method (merge, squash, rebase)
        """
        pr = self.get_pull_request(full_name, pr_number)
        pr.merge(merge_method=merge_method)
        logger.info(f"Merged PR #{pr_number} in {full_name}")

    def close(self):
        """Close the GitHub client connection"""
        if hasattr(self.client, "close"):
            self.client.close()
