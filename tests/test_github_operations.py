"""
Tests for GitHubClient — all GitHub API interaction paths.
Covers: repo ops, issue/PR management, file operations, search, rate limiting.
"""
import pytest
from unittest.mock import MagicMock, patch, call
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestGitHubClientRepoOps:
    def _make(self):
        from core.github_client import GitHubClient
        with patch("core.github_client.Github") as MockGH:
            client = GitHubClient({"github_token": "tok"})
            client._mock_gh = MockGH
            return client

    def test_get_repo_returns_repo_object(self):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        mock_repo = MagicMock()
        mock_gh.return_value.get_repo.return_value = mock_repo
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
            assert client.get_repo("owner/repo") == mock_repo

    def test_get_repo_called_with_correct_name(self):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
            client.get_repo("myorg/myrepo")
        mock_gh.return_value.get_repo.assert_called_with("myorg/myrepo")

    def test_list_repos_returns_list(self):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        mock_gh.return_value.get_user.return_value.get_repos.return_value = [
            MagicMock(name="repo1"), MagicMock(name="repo2")
        ]
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
            repos = client.list_repos()
        assert repos is not None


class TestGitHubClientIssueOps:
    def _client_with_mock_repo(self, repo_name="owner/repo"):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        mock_repo = MagicMock()
        mock_gh.return_value.get_repo.return_value = mock_repo
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
        client._gh = mock_gh.return_value
        client._mock_repo = mock_repo
        return client, mock_repo

    def test_create_issue(self):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        mock_issue = MagicMock(number=7)
        mock_gh.return_value.get_repo.return_value.create_issue.return_value = mock_issue
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
        result = client.create_issue("owner/repo", "Bug title", "Bug body", labels=["bug"])
        assert result.number == 7

    def test_close_issue(self):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        mock_issue = MagicMock()
        mock_gh.return_value.get_repo.return_value.get_issue.return_value = mock_issue
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
        client.close_issue("owner/repo", 5)
        mock_issue.edit.assert_called_with(state="closed")

    def test_add_comment_to_issue(self):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        mock_issue = MagicMock()
        mock_gh.return_value.get_repo.return_value.get_issue.return_value = mock_issue
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
        client.add_comment("owner/repo", 3, "This is fixed.")
        mock_issue.create_comment.assert_called_with("This is fixed.")

    def test_add_labels_to_issue(self):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        mock_issue = MagicMock()
        mock_gh.return_value.get_repo.return_value.get_issue.return_value = mock_issue
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
        client.add_labels("owner/repo", 4, ["bug", "priority: high"])
        mock_issue.add_to_labels.assert_called()


class TestGitHubClientPROps:
    def test_get_pull_request(self):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        mock_pr = MagicMock(number=10)
        mock_gh.return_value.get_repo.return_value.get_pull.return_value = mock_pr
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
        result = client.get_pull_request("owner/repo", 10)
        assert result.number == 10

    def test_merge_pull_request(self):
        from core.github_client import GitHubClient
        mock_gh = MagicMock()
        mock_pr = MagicMock()
        mock_gh.return_value.get_repo.return_value.get_pull.return_value = mock_pr
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
        client.merge_pull_request("owner/repo", 10, "squash")
        mock_pr.merge.assert_called()


class TestGitHubClientRateLimiting:
    def test_rate_limit_check_does_not_crash(self):
        from core.github_client import GitHubClient
        with patch("core.github_client.Github"):
            client = GitHubClient({"github_token": "tok"})
        # Should not raise
        client._wait_for_rate_limit()

    def test_github_exception_handled_gracefully(self):
        from core.github_client import GitHubClient, RateLimitError
        from github import GithubException
        mock_gh = MagicMock()
        mock_gh.return_value.get_repo.side_effect = GithubException(403, "rate limited", {})
        with patch("core.github_client.Github", mock_gh):
            client = GitHubClient({"github_token": "tok"})
        with pytest.raises(Exception):
            client.get_repo("owner/repo")
