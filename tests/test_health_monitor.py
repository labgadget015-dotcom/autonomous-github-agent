"""Tests for health monitor agent."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from autonomous_agent.agents.health_monitor import HealthMonitorAgent


def _make_agent(monkeypatch):
    """Build a HealthMonitorAgent with all collaborators mocked."""
    mock_github = MagicMock()
    mock_llm = MagicMock()
    mock_audit = MagicMock()

    agent = HealthMonitorAgent(mock_github, mock_llm, mock_audit)
    return agent, mock_github, mock_llm, mock_audit


def _branch(name, days_old=10, commit_date=None):
    """Build a fake repo branch with an author date `days_old` days ago."""
    if commit_date is None:
        commit_date = datetime.utcnow() - timedelta(days=days_old)
    author = MagicMock()
    author.date = commit_date
    inner_commit = MagicMock()
    inner_commit.author = author
    commit = MagicMock()
    commit.commit = inner_commit
    branch = MagicMock()
    branch.name = name
    branch.commit = commit
    return branch


def _pr(number, age_days):
    created = datetime.utcnow() - timedelta(days=age_days)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    pr = MagicMock()
    pr.number = number
    pr.title = f"PR {number}"
    pr.created_at = created
    pr.user.login = "someuser"
    return pr


@pytest.mark.asyncio
async def test_health_monitor_execute_full(monkeypatch):
    """Exercise the full execute path incl. both sides of every branch."""
    agent, mock_github, _, mock_audit = _make_agent(monkeypatch)

    repo = MagicMock()
    repo.stargazers_count = 100
    repo.forks_count = 10
    repo.open_issues_count = 60  # > 50 -> recommendation branch
    repo.watchers_count = 5
    repo.size = 1234
    repo.default_branch = "main"
    repo.archived = False
    repo.private = False
    repo.has_issues = True
    repo.has_wiki = True
    repo.has_pages = False
    repo.created_at = datetime(2024, 1, 1)
    repo.updated_at = datetime(2025, 1, 1)
    repo.pushed_at = datetime(2025, 6, 1)  # not None branch

    # One stale branch (>90 days) and one fresh branch; default branch skipped
    stale = _branch("old-feature", days_old=120)
    fresh = _branch("new-feature", days_old=5)
    main_branch = _branch("main", days_old=1)
    repo.get_branches.return_value = [stale, fresh, main_branch]

    # Old PR (>30 days)
    old_pr = _pr(7, age_days=40)
    recent_pr = _pr(8, age_days=2)
    mock_github.get_pull_requests.return_value = [old_pr, recent_pr]

    # Missing files: README present, LICENSE/others missing
    readme = MagicMock()
    readme.type = "file"
    readme.name = "README.md"
    repo.get_contents.return_value = [readme]

    mock_github.get_repository.return_value = repo

    result = await agent.execute("owner/repo")

    assert result["repository"] == "owner/repo"
    assert result["metrics"]["stars"] == 100
    assert result["metrics"]["open_issues"] == 60
    assert result["metrics"]["pushed_at"] is not None

    # Stale branch detected
    assert any(b["name"] == "old-feature" for b in result["issues"]["stale_branches"])
    # Fresh + default branch NOT flagged as stale
    assert all(b["name"] != "new-feature" for b in result["issues"]["stale_branches"])
    assert all(b["name"] != "main" for b in result["issues"]["stale_branches"])

    # Old PR detected, recent PR not
    assert any(p["number"] == 7 for p in result["issues"]["old_pull_requests"])
    assert all(p["number"] != 8 for p in result["issues"]["old_pull_requests"])

    # Missing files branch: LICENSE/.gitignore/CONTRIBUTING missing
    assert "LICENSE" in result["issues"]["missing_files"]
    assert "README.md" not in result["issues"]["missing_files"]

    recs = result["recommendations"]
    assert any("stale branch" in r for r in recs)
    assert any("pull request" in r for r in recs)
    assert any("Add missing files" in r for r in recs)
    assert any("High number of open issues" in r for r in recs)

    mock_audit.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_health_monitor_no_issues_paths(monkeypatch):
    """Exercise the 'no issues' branches (nothing stale/old/missing, <=50 issues)."""
    agent, mock_github, _, mock_audit = _make_agent(monkeypatch)

    repo = MagicMock()
    repo.stargazers_count = 1
    repo.forks_count = 0
    repo.open_issues_count = 3  # <= 50 -> no 'high issues' recommendation
    repo.watchers_count = 0
    repo.size = 10
    repo.default_branch = "main"
    repo.archived = False
    repo.private = False
    repo.has_issues = True
    repo.has_wiki = False
    repo.has_pages = False
    repo.created_at = datetime(2024, 1, 1)
    repo.updated_at = datetime(2025, 1, 1)
    repo.pushed_at = None  # None branch

    # Only the default branch, fresh
    repo.get_branches.return_value = [_branch("main", days_old=1)]
    mock_github.get_pull_requests.return_value = []  # no PRs

    # All essential files present
    names = ["README.md", "LICENSE", ".gitignore", "CONTRIBUTING.md"]
    files = []
    for n in names:
        f = MagicMock()
        f.type = "file"
        f.name = n
        files.append(f)
    repo.get_contents.return_value = files

    mock_github.get_repository.return_value = repo

    result = await agent.execute("owner/repo")

    assert result["issues"]["stale_branches"] == []
    assert result["issues"]["old_pull_requests"] == []
    assert result["issues"]["missing_files"] == []
    assert result["metrics"]["pushed_at"] is None
    # No recommendations triggered
    assert result["recommendations"] == []
    mock_audit.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_health_monitor_branch_exception_is_swallowed(monkeypatch):
    """The per-branch try/except must swallow errors and keep going."""
    agent, mock_github, _, _ = _make_agent(monkeypatch)

    repo = MagicMock()
    for attr in [
        "stargazers_count",
        "forks_count",
        "open_issues_count",
        "watchers_count",
        "size",
    ]:
        setattr(repo, attr, 0)
    repo.default_branch = "main"
    repo.archived = False
    repo.private = False
    repo.has_issues = True
    repo.has_wiki = False
    repo.has_pages = False
    repo.created_at = datetime(2024, 1, 1)
    repo.updated_at = datetime(2025, 1, 1)
    repo.pushed_at = datetime(2025, 1, 1)
    repo.get_pull_requests.return_value = []

    # Branch whose author date access raises -> exception branch is swallowed.
    # The code computes days_old from commit.commit.author.date inside try/except.
    author = MagicMock()
    author.date = MagicMock(side_effect=RuntimeError("boom"))
    inner_commit = MagicMock()
    inner_commit.author = author
    commit = MagicMock()
    commit.commit = inner_commit
    bad = MagicMock()
    bad.name = "broken"
    bad.commit = commit
    repo.get_branches.return_value = [bad]

    readme = MagicMock()
    readme.type = "file"
    readme.name = "README.md"
    repo.get_contents.return_value = [readme]

    mock_github.get_repository.return_value = repo

    result = await agent.execute("owner/repo")
    # No crash; stale_branches empty because the exception was swallowed
    assert result["issues"]["stale_branches"] == []


@pytest.mark.asyncio
async def test_health_monitor_contents_exception_is_swallowed(monkeypatch):
    """The get_contents try/except must swallow errors and keep going."""
    agent, mock_github, _, _ = _make_agent(monkeypatch)

    repo = MagicMock()
    for attr in [
        "stargazers_count",
        "forks_count",
        "open_issues_count",
        "watchers_count",
        "size",
    ]:
        setattr(repo, attr, 0)
    repo.default_branch = "main"
    repo.archived = False
    repo.private = False
    repo.has_issues = True
    repo.has_wiki = False
    repo.has_pages = False
    repo.created_at = datetime(2024, 1, 1)
    repo.updated_at = datetime(2025, 1, 1)
    repo.pushed_at = datetime(2025, 1, 1)
    repo.get_pull_requests.return_value = []
    repo.get_branches.return_value = []

    # get_contents raises -> exception branch for missing-files check
    repo.get_contents.side_effect = RuntimeError("no contents")

    mock_github.get_repository.return_value = repo

    result = await agent.execute("owner/repo")
    assert result["issues"]["missing_files"] == []
