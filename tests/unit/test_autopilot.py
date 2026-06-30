"""Unit tests for autopilot/autopilot.py"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


def _make_config(tmp_path, extra=None):
    cfg = {
        "repos": [{"owner": "acme", "name": "repo1", "priority": "critical"}],
        "analysis": {
            "lookback": {"commits": 24},
            "priority_weights": {
                "issue_count": 1,
                "pr_age_days": 2,
                "critical_repo": 5,
                "urgent_label": 10,
                "enhancement_label": 5,
                "recent_activity": 3,
            },
            "top_priorities": 3,
        },
        "output": {"console": False, "file": None},
    }
    if extra:
        cfg.update(extra)
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(cfg))
    return cfg, str(config_file)


def _make_autopilot(tmp_path, token="test-token", extra_cfg=None):
    from autopilot.autopilot import GitHubAutopilot

    cfg, config_path = _make_config(tmp_path, extra_cfg)
    config_name = Path(config_path).name

    mock_github = MagicMock()
    mock_github.get_rate_limit.return_value = MagicMock()

    with (
        patch.dict("os.environ", {"GITHUB_TOKEN": token}),
        patch("autopilot.autopilot.Github", return_value=mock_github),
        patch.object(Path, "parent", new_callable=lambda: property(lambda self: tmp_path)),
    ):
        ap = GitHubAutopilot.__new__(GitHubAutopilot)
        ap.start_time = time.time()
        ap.config = cfg
        ap.github = mock_github
        ap.repo_data = {}
    return ap


class TestLoadConfig:
    def test_raises_if_file_missing(self, tmp_path):
        from autopilot.autopilot import GitHubAutopilot

        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "x"}),
            patch("autopilot.autopilot.Github"),
            pytest.raises(FileNotFoundError),
        ):
            GitHubAutopilot.__new__(GitHubAutopilot)._load_config("nonexistent.yaml")

    def test_loads_yaml_file(self, tmp_path):
        from autopilot.autopilot import GitHubAutopilot

        cfg = {"repos": [], "analysis": {}, "output": {}}
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(yaml.dump(cfg))

        ap = GitHubAutopilot.__new__(GitHubAutopilot)
        ap.start_time = time.time()

        with patch.object(Path, "__truediv__", return_value=config_file):
            result = ap._load_config("test_config.yaml")
        assert result == cfg


class TestInitGithubClient:
    def test_raises_if_no_token(self, tmp_path):
        from autopilot.autopilot import GitHubAutopilot

        ap = GitHubAutopilot.__new__(GitHubAutopilot)
        ap.start_time = time.time()
        ap.config = {}

        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="GITHUB_TOKEN"),
        ):
            ap._init_github_client()

    def test_preflight_check_called(self, tmp_path):
        from autopilot.autopilot import GitHubAutopilot

        ap = GitHubAutopilot.__new__(GitHubAutopilot)
        ap.start_time = time.time()
        ap.config = {}

        mock_client = MagicMock()
        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}),
            patch("autopilot.autopilot.Github", return_value=mock_client),
        ):
            result = ap._init_github_client()
        mock_client.get_rate_limit.assert_called_once()
        assert result is mock_client

    def test_preflight_exception_does_not_raise(self, tmp_path):
        from autopilot.autopilot import GitHubAutopilot

        ap = GitHubAutopilot.__new__(GitHubAutopilot)
        ap.start_time = time.time()
        ap.config = {}

        mock_client = MagicMock()
        mock_client.get_rate_limit.side_effect = Exception("network error")
        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}),
            patch("autopilot.autopilot.Github", return_value=mock_client),
        ):
            result = ap._init_github_client()
        assert result is mock_client


class TestFetchRepoData:
    def setup_method(self):
        pass

    def _make(self, tmp_path):
        return _make_autopilot(tmp_path)

    def test_returns_none_on_github_exception(self, tmp_path):
        from github import GithubException

        ap = self._make(tmp_path)
        ap.github.get_repo.side_effect = GithubException(404, {"message": "Not Found"})
        result = ap.fetch_repo_data("owner", "missing-repo")
        assert result is None

    def test_returns_none_on_unexpected_exception(self, tmp_path):
        ap = self._make(tmp_path)
        ap.github.get_repo.side_effect = RuntimeError("network error")
        result = ap.fetch_repo_data("owner", "bad-repo")
        assert result is None

    def test_returns_data_dict_on_success(self, tmp_path):
        ap = self._make(tmp_path)

        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_issue.pull_request = None
        mock_repo.get_issues.return_value = [mock_issue]
        mock_repo.get_pulls.return_value = []
        mock_repo.get_commits.return_value = []
        ap.github.get_repo.return_value = mock_repo

        result = ap.fetch_repo_data("acme", "api")
        assert result is not None
        assert result["name"] == "api"
        assert result["owner"] == "acme"
        assert mock_issue in result["issues"]

    def test_filters_prs_from_issues(self, tmp_path):
        ap = self._make(tmp_path)

        pr_as_issue = MagicMock()
        pr_as_issue.pull_request = MagicMock()
        real_issue = MagicMock()
        real_issue.pull_request = None

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = [pr_as_issue, real_issue]
        mock_repo.get_pulls.return_value = []
        mock_repo.get_commits.return_value = []
        ap.github.get_repo.return_value = mock_repo

        result = ap.fetch_repo_data("acme", "repo")
        assert real_issue in result["issues"]
        assert pr_as_issue not in result["issues"]


class TestAnalyzePriorities:
    def _make(self, tmp_path):
        return _make_autopilot(tmp_path)

    def _mock_issue(self, labels=None, days_old=2):
        issue = MagicMock()
        issue.number = 1
        issue.title = "Test issue"
        issue.html_url = "http://example.com/1"
        issue.updated_at = MagicMock()
        issue.updated_at.replace.return_value = datetime.now() - timedelta(days=days_old)
        lbl_objs = []
        for name in labels or []:
            lbl = MagicMock()
            lbl.name = name
            lbl_objs.append(lbl)
        issue.labels = lbl_objs
        return issue

    def _mock_pr(self, labels=None, days_old=5):
        pr = MagicMock()
        pr.number = 10
        pr.title = "Test PR"
        pr.html_url = "http://example.com/pr/10"
        pr.updated_at = MagicMock()
        pr.created_at = MagicMock()
        pr.created_at.replace.return_value = datetime.now() - timedelta(days=days_old)
        pr.updated_at.replace.return_value = datetime.now() - timedelta(days=days_old)
        lbl_objs = []
        for name in labels or []:
            lbl = MagicMock()
            lbl.name = name
            lbl_objs.append(lbl)
        pr.labels = lbl_objs
        return pr

    def test_returns_empty_when_no_repos(self, tmp_path):
        ap = self._make(tmp_path)
        ap.repo_data = {}
        assert ap.analyze_priorities() == []

    def test_scores_issue_with_urgent_label_higher(self, tmp_path):
        ap = self._make(tmp_path)
        urgent = self._mock_issue(labels=["urgent"], days_old=5)
        normal = self._mock_issue(labels=[], days_old=5)
        normal.number = 2
        ap.repo_data = {
            "acme/repo": {
                "priority": "medium",
                "issues": [urgent, normal],
                "pulls": [],
                "commits": [],
            }
        }
        results = ap.analyze_priorities()
        assert results[0]["number"] == urgent.number

    def test_pr_included_in_results(self, tmp_path):
        ap = self._make(tmp_path)
        pr = self._mock_pr(days_old=3)
        ap.repo_data = {
            "acme/repo": {"priority": "medium", "issues": [], "pulls": [pr], "commits": []}
        }
        results = ap.analyze_priorities()
        assert any(r["type"] == "pr" for r in results)

    def test_top_priorities_capped(self, tmp_path):
        ap = self._make(tmp_path)
        issues = [self._mock_issue(days_old=i) for i in range(10)]
        for i, iss in enumerate(issues):
            iss.number = i
        ap.repo_data = {
            "acme/repo": {"priority": "medium", "issues": issues, "pulls": [], "commits": []}
        }
        results = ap.analyze_priorities()
        assert len(results) <= ap.config["analysis"]["top_priorities"]


class TestGenerateSummary:
    def _make(self, tmp_path):
        return _make_autopilot(tmp_path)

    def test_contains_header(self, tmp_path):
        ap = self._make(tmp_path)
        ap.repo_data = {}
        summary = ap.generate_summary([])
        assert "GitHub Autopilot Daily Summary" in summary

    def test_contains_date(self, tmp_path):
        ap = self._make(tmp_path)
        ap.repo_data = {}
        summary = ap.generate_summary([])
        assert datetime.now().strftime("%Y-%m-%d") in summary

    def test_priority_items_listed(self, tmp_path):
        ap = self._make(tmp_path)
        ap.repo_data = {}
        priorities = [
            {
                "type": "issue",
                "repo": "acme/api",
                "number": 42,
                "title": "Fix the bug",
                "url": "http://example.com/42",
                "labels": ["urgent"],
                "age_days": None,
            }
        ]
        summary = ap.generate_summary(priorities)
        assert "Fix the bug" in summary
        assert "#42" in summary
        assert "urgent" in summary

    def test_pr_shows_age(self, tmp_path):
        ap = self._make(tmp_path)
        ap.repo_data = {}
        priorities = [
            {
                "type": "pr",
                "repo": "acme/api",
                "number": 7,
                "title": "My PR",
                "url": "http://example.com/pr/7",
                "labels": [],
                "age_days": 14,
            }
        ]
        summary = ap.generate_summary(priorities)
        assert "14 days" in summary

    def test_repos_grouped_by_priority(self, tmp_path):
        ap = self._make(tmp_path)

        mock_pr = MagicMock()
        mock_pr.number = 1
        mock_pr.title = "test pr"

        mock_issue = MagicMock()
        mock_issue.number = 2
        mock_issue.title = "test issue"
        lbl = MagicMock()
        lbl.name = "bug"
        mock_issue.labels = [lbl]

        ap.repo_data = {
            "acme/critical": {
                "priority": "critical",
                "issues": [mock_issue],
                "pulls": [mock_pr],
                "commits": [MagicMock(), MagicMock()],
                "config": {"notes": "important repo"},
            }
        }
        summary = ap.generate_summary([])
        assert "Critical Repos" in summary
        assert "acme/critical" in summary
        assert "2 commits in last 24h" in summary
        assert "important repo" in summary

    def test_urgent_issues_highlighted(self, tmp_path):
        ap = self._make(tmp_path)

        urgent_issue = MagicMock()
        urgent_issue.number = 5
        urgent_issue.title = "Urgent bug!"
        urgent_lbl = MagicMock()
        urgent_lbl.name = "urgent"
        urgent_issue.labels = [urgent_lbl]

        ap.repo_data = {
            "acme/repo": {
                "priority": "medium",
                "issues": [urgent_issue],
                "pulls": [],
                "commits": [],
                "config": {},
            }
        }
        summary = ap.generate_summary([])
        assert "Urgent" in summary


class TestRun:
    def _make(self, tmp_path):
        return _make_autopilot(tmp_path)

    def test_raises_if_no_repos_fetched(self, tmp_path):
        ap = self._make(tmp_path)
        ap.fetch_all_repos = MagicMock(return_value={})
        ap.repo_data = {}
        with pytest.raises(RuntimeError, match="repos_scanned=0"):
            ap.run()

    def test_writes_to_output_file(self, tmp_path):
        ap = self._make(tmp_path)
        ap.repo_data = {
            "acme/repo": {
                "priority": "medium",
                "issues": [],
                "pulls": [],
                "commits": [],
                "config": {},
            }
        }
        ap.fetch_all_repos = MagicMock(return_value=ap.repo_data)
        ap.analyze_priorities = MagicMock(return_value=[])
        ap.generate_summary = MagicMock(return_value="## Summary")

        out_file = tmp_path / "out.md"
        ap.run(output_file=str(out_file))
        assert out_file.read_text() == "## Summary"

    def test_returns_summary_string(self, tmp_path):
        ap = self._make(tmp_path)
        ap.repo_data = {
            "acme/repo": {
                "priority": "medium",
                "issues": [],
                "pulls": [],
                "commits": [],
                "config": {},
            }
        }
        ap.fetch_all_repos = MagicMock(return_value=ap.repo_data)
        ap.analyze_priorities = MagicMock(return_value=[])
        ap.generate_summary = MagicMock(return_value="## Generated")

        result = ap.run()
        assert result == "## Generated"
