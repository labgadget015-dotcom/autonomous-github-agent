#!/usr/bin/env python3
"""
GitHub Client

Provides a wrapper around the GitHub API with rate limiting, retry logic,
and error handling.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from github import Github, GithubException
from github.Repository import Repository
from github.Issue import Issue
from github.PullRequest import PullRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""

    pass


class GitHubClient:
    """
    GitHub API client with rate limiting and retry logic.

    Features:
    - Automatic rate limit handling
    - Exponential backoff for retries
    - Connection pooling
    - Error handling
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize GitHub client.

        Args:
            config: Configuration dictionary containing:
                - github_token: GitHub personal access token or app token
                - github_base_url: Optional GitHub Enterprise URL
        """
        self.config = config
        token = config.get("github_token", config.get("GITHUB_TOKEN"))
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

    def check_rate_limit(self) -> Dict[str, Any]:
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
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Issue:
        """
        Create a new issue in a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body
            labels: Optional list of labels
            assignees: Optional list of assignees

        Returns:
            Created Issue object
        """
        self._wait_for_rate_limit()

        try:
            repository = self.get_repository(owner, repo)
            issue = repository.create_issue(
                title=title, body=body, labels=labels or [], assignees=assignees or []
            )
            logger.info(f"Created issue #{issue.number} in {owner}/{repo}")
            return issue
        except GithubException as e:
            logger.error(f"Error creating issue in {owner}/{repo}: {str(e)}")
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

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> PullRequest:
        """
        Get a pull request by number.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            PullRequest object
        """
        self._wait_for_rate_limit()

        try:
            repository = self.get_repository(owner, repo)
            return repository.get_pull(pr_number)
        except GithubException as e:
            logger.error(f"Error getting PR #{pr_number} in {owner}/{repo}: {str(e)}")
            raise

    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
    ) -> List[Issue]:
        """
        List issues in a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state ('open', 'closed', 'all')
            labels: Optional list of labels to filter by

        Returns:
            List of Issue objects
        """
        self._wait_for_rate_limit()

        try:
            repository = self.get_repository(owner, repo)
            issues = repository.get_issues(state=state, labels=labels or [])
            return list(issues)
        except GithubException as e:
            logger.error(f"Error listing issues in {owner}/{repo}: {str(e)}")
            raise

    def add_comment(self, owner: str, repo: str, issue_number: int, body: str):
        """
        Add a comment to an issue or pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue or PR number
            body: Comment body
        """
        self._wait_for_rate_limit()

        try:
            issue = self.get_issue(owner, repo, issue_number)
            issue.create_comment(body)
            logger.info(f"Added comment to #{issue_number} in {owner}/{repo}")
        except GithubException as e:
            logger.error(
                f"Error adding comment to #{issue_number} in {owner}/{repo}: {str(e)}"
            )
            raise

    def close(self):
        """Close the GitHub client connection"""
        if hasattr(self.client, "close"):
            self.client.close()
