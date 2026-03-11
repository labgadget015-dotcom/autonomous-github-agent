"""Idempotency guards for GitHub operations.

Prevents duplicate issue creation, duplicate PRs, and redundant branch ops
by checking existing state before executing writes.

Usage::

    from core.idempotency import IssueGuard, PRGuard, BranchGuard

    guard = IssueGuard(github_client)
    existing = guard.find_duplicate("Fix: urllib3 CVE", labels=["security"])
    if existing:
        print(f"Already exists: #{existing['number']}")
    else:
        create_issue(...)
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _normalise(text: str) -> list[str]:
    """Lowercase, strip punctuation/whitespace for fuzzy matching."""
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()


def _title_similarity(a: str, b: str) -> float:
    """Jaccard similarity of word sets (0.0–1.0)."""
    wa, wb = set(_normalise(a)), set(_normalise(b))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


class IssueGuard:
    """Checks for duplicate issues before creating a new one.

    Uses exact label match + title similarity (Jaccard ≥ threshold).
    """

    DEFAULT_THRESHOLD = 0.60

    def __init__(
        self, github_client: Any, threshold: float = DEFAULT_THRESHOLD
    ) -> None:
        self.client = github_client
        self.threshold = threshold
        self._cache: list[dict[str, Any]] | None = None

    def _get_open_issues(self) -> list[dict[str, Any]]:
        if self._cache is None:
            self._cache = self.client.list_issues(state="open") or []
        return self._cache

    def find_duplicate(
        self,
        title: str,
        labels: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Return the first open issue that looks like a duplicate, or None.

        Args:
            title: Proposed new issue title.
            labels: Proposed labels (at least one must overlap for a match).

        Returns:
            Existing issue dict if duplicate found, else None.
        """
        labels = labels or []
        for issue in self._get_open_issues():
            existing_title = issue.get("title", "")
            sim = _title_similarity(title, existing_title)
            if sim < self.threshold:
                continue
            # Label overlap check (if labels provided)
            if labels:
                existing_labels = {lbl["name"] for lbl in issue.get("labels", [])}
                if not existing_labels.intersection(labels):
                    continue
            logger.info(
                "Duplicate issue detected: proposed=%r matches #%s %r (sim=%.2f)",
                title,
                issue.get("number"),
                existing_title,
                sim,
            )
            return issue
        return None

    def invalidate_cache(self) -> None:
        self._cache = None


class PRGuard:
    """Checks for an existing open PR with the same head/base before creating."""

    def __init__(self, github_client: Any) -> None:
        self.client = github_client

    def find_existing(
        self, head_branch: str, base_branch: str = "main"
    ) -> dict[str, Any] | None:
        """Return an open PR matching head→base, or None."""
        prs = self.client.list_pull_requests(state="open", base=base_branch) or []
        for pr in prs:
            pr_head = pr.get("head", {}).get("ref", "")
            if pr_head == head_branch:
                logger.info(
                    "Existing PR found: #%s head=%r base=%r",
                    pr.get("number"),
                    head_branch,
                    base_branch,
                )
                return pr
        return None


class BranchGuard:
    """Checks branch existence before create/delete operations."""

    def __init__(self, github_client: Any) -> None:
        self.client = github_client

    def exists(self, branch_name: str) -> bool:
        """Return True if the branch already exists on the remote."""
        result = self.client.get_branch(branch_name)
        return result is not None

    def safe_create(self, branch_name: str, sha: str) -> dict[str, Any] | None:
        """Create branch only if it doesn't already exist.

        Returns the branch ref dict, or None if branch already existed.
        """
        if self.exists(branch_name):
            logger.warning("Branch %r already exists — skipping create", branch_name)
            return None
        return self.client.create_branch(branch_name, sha)

    def safe_delete(self, branch_name: str, protected: set[str] | None = None) -> bool:
        """Delete branch only if it exists and is not in the protected set.

        Returns True if deleted, False if skipped.
        """
        protected = protected or {"main", "master", "develop"}
        if branch_name in protected:
            logger.warning("Branch %r is protected — skipping delete", branch_name)
            return False
        if not self.exists(branch_name):
            logger.info("Branch %r does not exist — nothing to delete", branch_name)
            return False
        self.client.delete_branch(branch_name)
        logger.info("Deleted branch %r", branch_name)
        return True
