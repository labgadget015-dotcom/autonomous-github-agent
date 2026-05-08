"""Unit tests for core/idempotency.py"""

from __future__ import annotations

from unittest.mock import MagicMock

from core.idempotency import BranchGuard, IssueGuard, PRGuard, _title_similarity


class TestTitleSimilarity:
    def test_identical_titles(self):
        assert _title_similarity("fix auth bug", "fix auth bug") == 1.0

    def test_completely_different(self):
        sim = _title_similarity("fix auth bug", "update documentation")
        assert sim < 0.2

    def test_partial_overlap(self):
        sim = _title_similarity("fix auth token bug", "fix token expiry")
        assert 0.0 < sim < 1.0

    def test_empty_strings(self):
        assert _title_similarity("", "fix bug") == 0.0


class TestIssueGuard:
    def _make_client(self, issues: list[dict]) -> MagicMock:
        client = MagicMock()
        client.list_issues.return_value = issues
        return client

    def test_no_duplicate_when_empty(self):
        guard = IssueGuard(self._make_client([]))
        result = guard.find_duplicate("Fix: urllib3 CVE", labels=["security"])
        assert result is None

    def test_finds_exact_title_duplicate(self):
        existing = [
            {
                "number": 42,
                "title": "Fix: urllib3 CVE",
                "labels": [{"name": "security"}],
            }
        ]
        guard = IssueGuard(self._make_client(existing))
        result = guard.find_duplicate("Fix: urllib3 CVE", labels=["security"])
        assert result is not None
        assert result["number"] == 42

    def test_no_match_when_labels_differ(self):
        existing = [
            {"number": 42, "title": "Fix: urllib3 CVE", "labels": [{"name": "docs"}]}
        ]
        guard = IssueGuard(self._make_client(existing))
        result = guard.find_duplicate("Fix: urllib3 CVE", labels=["security"])
        assert result is None

    def test_cache_used_on_second_call(self):
        client = self._make_client([])
        guard = IssueGuard(client)
        guard.find_duplicate("title a")
        guard.find_duplicate("title b")
        client.list_issues.assert_called_once()

    def test_invalidate_cache_refetches(self):
        client = self._make_client([])
        guard = IssueGuard(client)
        guard.find_duplicate("title a")
        guard.invalidate_cache()
        guard.find_duplicate("title b")
        assert client.list_issues.call_count == 2

    def test_custom_threshold_applied(self):
        # With threshold=1.0, only exact matches allowed
        existing = [{"number": 5, "title": "Fix urllib3 vuln", "labels": []}]
        guard = IssueGuard(self._make_client(existing), threshold=1.0)
        result = guard.find_duplicate("Fix urllib3 CVE")
        assert result is None


class TestPRGuard:
    def _make_client(self, prs: list[dict]) -> MagicMock:
        client = MagicMock()
        client.list_pull_requests.return_value = prs
        return client

    def test_no_existing_pr(self):
        guard = PRGuard(self._make_client([]))
        assert guard.find_existing("feat/my-feature") is None

    def test_finds_existing_pr(self):
        prs = [{"number": 99, "head": {"ref": "feat/my-feature"}}]
        guard = PRGuard(self._make_client(prs))
        result = guard.find_existing("feat/my-feature")
        assert result is not None
        assert result["number"] == 99

    def test_different_head_not_matched(self):
        prs = [{"number": 99, "head": {"ref": "feat/other-feature"}}]
        guard = PRGuard(self._make_client(prs))
        assert guard.find_existing("feat/my-feature") is None


class TestBranchGuard:
    def _make_client(self, branch_exists: bool) -> MagicMock:
        client = MagicMock()
        client.get_branch.return_value = {"name": "test"} if branch_exists else None
        client.create_branch.return_value = {"ref": "refs/heads/test"}
        return client

    def test_exists_true_when_branch_found(self):
        guard = BranchGuard(self._make_client(True))
        assert guard.exists("test") is True

    def test_exists_false_when_branch_missing(self):
        guard = BranchGuard(self._make_client(False))
        assert guard.exists("test") is False

    def test_safe_create_skips_existing(self):
        client = self._make_client(True)
        guard = BranchGuard(client)
        result = guard.safe_create("test", "abc123")
        assert result is None
        client.create_branch.assert_not_called()

    def test_safe_create_proceeds_when_missing(self):
        client = self._make_client(False)
        guard = BranchGuard(client)
        result = guard.safe_create("test", "abc123")
        assert result is not None
        client.create_branch.assert_called_once_with("test", "abc123")

    def test_safe_delete_skips_protected(self):
        client = self._make_client(True)
        guard = BranchGuard(client)
        deleted = guard.safe_delete("main")
        assert deleted is False
        client.delete_branch = MagicMock()
        client.delete_branch.assert_not_called()

    def test_safe_delete_skips_nonexistent(self):
        client = self._make_client(False)
        guard = BranchGuard(client)
        deleted = guard.safe_delete("feat/gone")
        assert deleted is False

    def test_safe_delete_succeeds(self):
        client = self._make_client(True)
        client.delete_branch = MagicMock()
        guard = BranchGuard(client)
        deleted = guard.safe_delete("feat/old-branch")
        assert deleted is True
        client.delete_branch.assert_called_once_with("feat/old-branch")
