"""Unit tests for core/github_client.py"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from github import GithubException


def _make_client(token="ghp_test", **config_extra):
    from core.github_client import GitHubClient

    config = {"github_token": token, **config_extra}
    with patch("core.github_client.Github") as mock_gh_cls:
        mock_gh = MagicMock()
        mock_gh_cls.return_value = mock_gh
        client = GitHubClient(config)
        client._mock_gh = mock_gh
        client._mock_gh_cls = mock_gh_cls
    return client


class TestGitHubClientInit:
    def test_client_initialized_with_token(self):
        client = _make_client("ghp_abc")
        assert client.client is not None

    def test_no_token_creates_unauthenticated_client(self):
        with patch("core.github_client.Github") as mock_gh_cls:
            with patch.dict("os.environ", {}, clear=True):
                from core.github_client import GitHubClient

                client = GitHubClient({})
            mock_gh_cls.assert_called()


class TestGetRepository:
    def _setup(self):
        client = _make_client()
        mock_repo = MagicMock()
        client.client.get_repo.return_value = mock_repo
        return client, mock_repo

    def test_get_repository_returns_repo(self):
        client, mock_repo = self._setup()
        result = client.get_repository("owner", "repo")
        assert result is mock_repo

    def test_get_repository_calls_correct_full_name(self):
        client, _ = self._setup()
        client.get_repository("myorg", "myrepo")
        client.client.get_repo.assert_called_once_with("myorg/myrepo")

    def test_get_repository_raises_on_github_exception(self):
        client = _make_client()
        client.client.get_repo.side_effect = GithubException(404, "Not Found")
        with pytest.raises(GithubException):
            client.get_repository("owner", "missing-repo")


class TestCreateIssue:
    def _setup(self):
        client = _make_client()
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_issue.number = 42
        mock_repo.create_issue.return_value = mock_issue
        client.client.get_repo.return_value = mock_repo
        return client, mock_repo, mock_issue

    def test_create_issue_returns_issue(self):
        client, _, mock_issue = self._setup()
        result = client.create_issue("owner/repo", "Bug", "body")
        assert result is mock_issue

    def test_create_issue_passes_labels(self):
        client, mock_repo, _ = self._setup()
        client.create_issue("owner/repo", "T", "B", labels=["bug"])
        call_kwargs = mock_repo.create_issue.call_args[1]
        assert "bug" in call_kwargs["labels"]

    def test_create_issue_passes_assignees(self):
        client, mock_repo, _ = self._setup()
        client.create_issue("owner/repo", "T", "B", assignees=["alice"])
        call_kwargs = mock_repo.create_issue.call_args[1]
        assert "alice" in call_kwargs["assignees"]

    def test_create_issue_raises_on_github_exception(self):
        client = _make_client()
        client.client.get_repo.return_value = MagicMock()
        client.client.get_repo.return_value.create_issue.side_effect = GithubException(
            422, "Validation Failed"
        )
        with pytest.raises(GithubException):
            client.create_issue("owner/repo", "T", "B")


class TestGetIssue:
    def test_get_issue_returns_issue(self):
        client = _make_client()
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_issue.number = 7
        mock_repo.get_issue.return_value = mock_issue
        client.client.get_repo.return_value = mock_repo
        result = client.get_issue("owner", "repo", 7)
        assert result is mock_issue

    def test_get_issue_raises_on_not_found(self):
        client = _make_client()
        mock_repo = MagicMock()
        mock_repo.get_issue.side_effect = GithubException(404, "Not Found")
        client.client.get_repo.return_value = mock_repo
        with pytest.raises(GithubException):
            client.get_issue("owner", "repo", 999)


class TestGetPullRequest:
    def test_get_pull_request_returns_pr(self):
        client = _make_client()
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.number = 3
        mock_repo.get_pull.return_value = mock_pr
        client.client.get_repo.return_value = mock_repo
        result = client.get_pull_request("owner/repo", 3)
        assert result is mock_pr


class TestListIssues:
    def test_list_issues_returns_list(self):
        client = _make_client()
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issues.return_value = [mock_issue]
        client.client.get_repo.return_value = mock_repo
        result = client.list_issues("owner", "repo")
        assert mock_issue in result

    def test_list_issues_respects_limit(self):
        client = _make_client()
        mock_repo = MagicMock()
        issues = [MagicMock() for _ in range(10)]
        mock_repo.get_issues.return_value = issues
        client.client.get_repo.return_value = mock_repo
        result = client.list_issues("owner", "repo", limit=3)
        assert len(result) == 3


class TestAddComment:
    def test_add_comment_calls_create_comment(self):
        client = _make_client()
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_repo.get_issues.return_value = []
        client.client.get_repo.return_value = mock_repo
        client.add_comment("owner/repo", 1, "Hello!")
        mock_issue.create_comment.assert_called_once_with("Hello!")


class TestAdapterMethods:
    def test_get_repo_delegates_to_get_repository(self):
        client = _make_client()
        mock_repo = MagicMock()
        client.client.get_repo.return_value = mock_repo
        result = client.get_repo("owner/repo")
        assert result is mock_repo

    def test_close_issue(self):
        client = _make_client()
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        client.client.get_repo.return_value = mock_repo
        client.close_issue("owner/repo", 5)
        mock_issue.edit.assert_called_once_with(state="closed")

    def test_merge_pull_request(self):
        client = _make_client()
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        client.client.get_repo.return_value = mock_repo
        client.merge_pull_request("owner/repo", 10, merge_method="squash")
        mock_pr.merge.assert_called_once_with(merge_method="squash")

    def test_add_labels_calls_add_to_labels(self):
        client = _make_client()
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        client.client.get_repo.return_value = mock_repo
        client.add_labels("owner/repo", 1, ["bug", "urgent"])
        mock_issue.add_to_labels.assert_called_once_with("bug", "urgent")


class TestListRepos:
    def test_list_repos_for_org(self):
        client = _make_client()
        mock_org = MagicMock()
        mock_repo = MagicMock()
        mock_org.get_repos.return_value = [mock_repo]
        client.client.get_organization.return_value = mock_org
        result = client.list_repos(org="myorg")
        assert mock_repo in result

    def test_list_repos_for_user(self):
        client = _make_client()
        mock_user = MagicMock()
        mock_repo = MagicMock()
        mock_user.get_repos.return_value = [mock_repo]
        client.client.get_user.return_value = mock_user
        result = client.list_repos(user="alice")
        assert mock_repo in result


class TestClose:
    def test_close_calls_underlying_close(self):
        client = _make_client()
        client.client.close = MagicMock()
        client.close()
        client.client.close.assert_called_once()
