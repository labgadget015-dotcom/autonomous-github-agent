"""Tests for autonomous_agent package — agents and CLI."""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from autonomous_agent.agents.branch_manager import BranchManagerAgent
from autonomous_agent.agents.code_reviewer import CodeReviewerAgent
from autonomous_agent.agents.documentation_generator import DocumentationGeneratorAgent
from autonomous_agent.agents.issue_manager import IssueManagerAgent
from autonomous_agent.agents.security_scanner import SecurityScannerAgent
from autonomous_agent.agents.workflow_optimizer import WorkflowOptimizerAgent
from autonomous_agent.cli import (
    config_check,
    list_agents,
    logs,
    main,
)

# ── helpers ───────────────────────────────────────────────────────────────────


def _make_deps():
    github = Mock()
    llm = Mock()
    audit = Mock()
    audit.log_action.return_value = 1
    audit.get_logs.return_value = []
    return github, llm, audit


# ── BranchManagerAgent ────────────────────────────────────────────────────────


class TestBranchManagerAgent:
    def setup_method(self):
        self.github, self.llm, self.audit = _make_deps()
        self.agent = BranchManagerAgent(self.github, self.llm, self.audit)

    @pytest.mark.asyncio
    async def test_execute_no_branches(self):
        repo = Mock()
        repo.default_branch = "main"
        repo.get_branches.return_value = []
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")

        assert result["repository"] == "owner/repo"
        assert result["branches_analyzed"] == 0
        assert result["stale_branches_deleted"] == 0

    @pytest.mark.asyncio
    async def test_execute_skips_default_branch(self):
        repo = Mock()
        repo.default_branch = "main"
        main_branch = Mock()
        main_branch.name = "main"
        repo.get_branches.return_value = [main_branch]
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")
        assert result["branches_analyzed"] == 0

    @pytest.mark.asyncio
    async def test_execute_stale_branch_requires_approval(self):
        repo = Mock()
        repo.default_branch = "main"

        branch = Mock()
        branch.name = "old-feature"
        old_date = datetime(2025, 1, 1, tzinfo=UTC)
        branch.commit.commit.author.date = old_date
        repo.get_branches.return_value = [branch]
        self.github.get_repository.return_value = repo

        with patch.object(self.agent, "requires_approval", return_value=True):
            result = await self.agent.execute("owner/repo")

        assert result["branches_analyzed"] == 1
        assert len(result["recommendations"]) == 1
        assert "old-feature" in result["recommendations"][0]

    @pytest.mark.asyncio
    async def test_execute_stale_branch_auto_delete(self):
        repo = Mock()
        repo.default_branch = "main"

        branch = Mock()
        branch.name = "old-feature"
        old_date = datetime(2025, 1, 1, tzinfo=UTC)
        branch.commit.commit.author.date = old_date
        branch.commit.sha = "abc123"

        mock_ref = Mock()
        repo.get_branches.return_value = [branch]
        repo.get_git_ref.return_value = mock_ref
        self.github.get_repository.return_value = repo

        self.agent.config = Mock()
        self.agent.config.automation_level = "full-auto"
        self.agent.config.requires_approval = Mock(return_value=False)

        with patch.object(self.agent, "requires_approval", return_value=False):
            result = await self.agent.execute("owner/repo")

        assert result["stale_branches_deleted"] == 1
        mock_ref.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_handles_commit_exception(self):
        repo = Mock()
        repo.default_branch = "main"
        branch = Mock()
        branch.name = "broken"
        branch.commit.commit.author.date = None
        repo.get_branches.return_value = [branch]
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")
        assert result["branches_analyzed"] == 1


# ── CodeReviewerAgent ─────────────────────────────────────────────────────────


class TestCodeReviewerAgent:
    def setup_method(self):
        self.github, self.llm, self.audit = _make_deps()
        self.agent = CodeReviewerAgent(self.github, self.llm, self.audit)

    @pytest.mark.asyncio
    async def test_execute_specific_pr(self):
        repo = Mock()
        pr = Mock()
        pr.number = 42
        pr.title = "Add feature"
        pr.user.login = "dev"
        pr.get_files.return_value = []
        self.github.get_repository.return_value = repo
        repo.get_pull.return_value = pr
        self.github.create_issue_comment = Mock()

        result = await self.agent.execute("owner/repo", pr_number=42)

        assert result["reviewed_prs"] == 1
        assert result["results"][0]["pr_number"] == 42

    @pytest.mark.asyncio
    async def test_execute_all_prs(self):
        repo = Mock()
        pr = Mock()
        pr.number = 1
        pr.title = "Fix bug"
        pr.user.login = "dev"
        pr.get_files.return_value = []
        self.github.get_repository.return_value = repo
        self.github.get_pull_requests.return_value = [pr]
        self.github.create_issue_comment = Mock()

        result = await self.agent.execute("owner/repo")

        assert result["reviewed_prs"] == 1

    @pytest.mark.asyncio
    async def test_review_pr_with_files(self):
        repo = Mock()
        repo.owner.login = "owner"
        repo.name = "repo"

        pr = Mock()
        pr.number = 5
        pr.title = "Patch"
        pr.user.login = "dev"

        file = Mock()
        file.filename = "app.py"
        file.patch = "- old line\n+ new line"
        pr.get_files.return_value = [file]

        self.llm.complete.return_value = "No issues found."
        self.github.create_issue_comment = Mock()

        result = await self.agent._review_pr(repo, pr)

        assert result["pr_number"] == 5
        assert "score" in result

    @pytest.mark.asyncio
    async def test_review_pr_file_no_patch(self):
        repo = Mock()
        repo.owner.login = "owner"
        repo.name = "repo"

        pr = Mock()
        pr.number = 3
        pr.title = "Binary update"
        pr.user.login = "dev"

        file = Mock()
        file.filename = "image.png"
        file.patch = None
        pr.get_files.return_value = [file]

        self.github.create_issue_comment = Mock()

        result = await self.agent._review_pr(repo, pr)
        assert result["issues_found"] == []

    @pytest.mark.asyncio
    async def test_analyze_code_changes_llm_success(self):
        self.llm.complete.return_value = (
            "Issue: missing error handling\n"
            "Suggestion: recommend adding try/catch\n"
            "Security vulnerability: potential XSS"
        )

        result = await self.agent._analyze_code_changes("main.py", "+print(x)")

        assert isinstance(result["issues"], list)
        assert isinstance(result["suggestions"], list)
        assert isinstance(result["security_concerns"], list)

    @pytest.mark.asyncio
    async def test_analyze_code_changes_llm_error(self):
        self.llm.complete.side_effect = Exception("API error")

        result = await self.agent._analyze_code_changes("main.py", "+x=1")
        assert result == {"issues": [], "suggestions": [], "security_concerns": []}

    def test_extract_methods(self):
        response = (
            "There is a major issue here\n"
            "I suggest using a better approach\n"
            "Security: there is a vulnerability"
        )
        assert len(self.agent._extract_issues(response)) >= 1
        assert len(self.agent._extract_suggestions(response)) >= 1
        assert len(self.agent._extract_security(response)) >= 1

    def test_calculate_review_score_perfect(self):
        review = {"issues_found": [], "security_concerns": []}
        assert self.agent._calculate_review_score(review) == 100

    def test_calculate_review_score_deductions(self):
        review = {"issues_found": ["a", "b"], "security_concerns": ["c"]}
        score = self.agent._calculate_review_score(review)
        assert score == 75  # 100 - 2*5 - 1*15

    def test_calculate_review_score_floor_zero(self):
        review = {
            "issues_found": ["i"] * 20,
            "security_concerns": ["s"] * 10,
        }
        assert self.agent._calculate_review_score(review) == 0

    @pytest.mark.asyncio
    async def test_post_review_comment_with_all_sections(self):
        pr = Mock()
        review = {
            "security_concerns": ["XSS risk"],
            "issues_found": ["missing type hints"],
            "suggestions": ["use dataclass"],
            "score": 75,
        }
        self.github.create_issue_comment = Mock()

        await self.agent._post_review_comment(pr, review)
        self.github.create_issue_comment.assert_called_once()
        comment = self.github.create_issue_comment.call_args[0][1]
        assert "Security" in comment
        assert "Issues" in comment
        assert "Suggestions" in comment


# ── DocumentationGeneratorAgent ───────────────────────────────────────────────


class TestDocumentationGeneratorAgent:
    def setup_method(self):
        self.github, self.llm, self.audit = _make_deps()
        self.agent = DocumentationGeneratorAgent(self.github, self.llm, self.audit)

    @pytest.mark.asyncio
    async def test_execute_with_readme(self):
        repo = Mock()
        readme = Mock()
        readme.decoded_content = (
            b"# Project\n## Installation\n## Usage\n## Contributing\n## License\n"
            b"```python\nprint('hello')\n```\n" + b"x" * 500
        )
        repo.get_readme.return_value = readme
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")
        assert result["repository"] == "owner/repo"

    @pytest.mark.asyncio
    async def test_execute_no_readme(self):
        repo = Mock()
        repo.get_readme.side_effect = Exception("Not found")
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")
        assert any("README" in s for s in result["suggestions"])

    @pytest.mark.asyncio
    async def test_analyze_readme_missing_sections(self):
        content = "# My Project\nJust a short description."
        suggestions = await self.agent._analyze_readme(content)
        assert any("Installation" in s for s in suggestions)
        assert any("too brief" in s for s in suggestions)
        assert any("code examples" in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_analyze_readme_complete(self):
        content = (
            "# Project\n## Installation\n## Usage\n## Contributing\n## License\n"
            "```python\nprint()\n```\n" + "detail " * 100
        )
        suggestions = await self.agent._analyze_readme(content)
        assert suggestions == []


# ── IssueManagerAgent ─────────────────────────────────────────────────────────


class TestIssueManagerAgent:
    def setup_method(self):
        self.github, self.llm, self.audit = _make_deps()
        self.agent = IssueManagerAgent(self.github, self.llm, self.audit)

    @pytest.mark.asyncio
    async def test_execute_skips_pull_requests(self):
        repo = Mock()
        pr_issue = Mock()
        pr_issue.pull_request = True
        self.github.get_repository.return_value = repo
        self.github.get_issues.return_value = [pr_issue]

        result = await self.agent.execute("owner/repo")
        assert result["processed"] == 0

    @pytest.mark.asyncio
    async def test_execute_labels_unlabeled_issue(self):
        repo = Mock()
        issue = Mock()
        issue.pull_request = None
        issue.labels = []
        issue.title = "App crashes on startup"
        issue.body = "There is a bug"
        self.github.get_repository.return_value = repo
        self.github.get_issues.return_value = [issue]
        self.llm.complete.return_value = "NOT_DUPLICATE"
        repo.get_issues.return_value = []

        result = await self.agent.execute("owner/repo")
        assert result["labeled"] == 1
        assert result["processed"] == 1

    @pytest.mark.asyncio
    async def test_auto_label_bug(self):
        issue = Mock()
        issue.title = "App crashes"
        issue.body = "There is an error"
        issue.add_to_labels = Mock()

        await self.agent._auto_label_issue(issue)
        issue.add_to_labels.assert_called()
        labels = issue.add_to_labels.call_args[0]
        assert "bug" in labels

    @pytest.mark.asyncio
    async def test_auto_label_no_match(self):
        issue = Mock()
        issue.title = "General update"
        issue.body = "Nothing specific"
        issue.add_to_labels = Mock()

        await self.agent._auto_label_issue(issue)
        issue.add_to_labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_label_exception_suppressed(self):
        issue = Mock()
        issue.title = "bug"
        issue.body = "crash"
        issue.add_to_labels = Mock(side_effect=Exception("API error"))

        # Should not raise
        await self.agent._auto_label_issue(issue)

    @pytest.mark.asyncio
    async def test_check_duplicate_not_duplicate(self):
        repo = Mock()
        issue = Mock()
        issue.title = "New issue"
        issue.body = "Description"
        repo.get_issues.return_value = []
        self.llm.complete.return_value = "NOT_DUPLICATE"

        result = await self.agent._check_duplicate(repo, issue)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_duplicate_found(self):
        repo = Mock()
        issue = Mock()
        issue.title = "Same crash as before"
        issue.body = "same error"

        closed = Mock()
        closed.number = 10
        closed.title = "Crash on start"
        repo.get_issues.return_value = [closed]

        self.llm.complete.return_value = "This is a duplicate of #10"
        self.github.create_issue_comment = Mock()
        issue.add_to_labels = Mock()

        result = await self.agent._check_duplicate(repo, issue)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_duplicate_llm_exception(self):
        repo = Mock()
        issue = Mock()
        issue.title = "Issue"
        issue.body = "Body"
        repo.get_issues.return_value = []
        self.llm.complete.side_effect = Exception("LLM down")

        result = await self.agent._check_duplicate(repo, issue)
        assert result is False


# ── SecurityScannerAgent ──────────────────────────────────────────────────────


class TestSecurityScannerAgent:
    def setup_method(self):
        self.github, self.llm, self.audit = _make_deps()
        self.agent = SecurityScannerAgent(self.github, self.llm, self.audit)

    @pytest.mark.asyncio
    async def test_execute_clean_repo(self):
        repo = Mock()
        commit = Mock()
        file = Mock()
        file.patch = "print('hello')"
        commit.files = [file]
        repo.get_commits.return_value = [commit]
        repo.get_readme = Mock(side_effect=Exception)
        repo.get_contents = Mock(side_effect=Exception)
        repo.default_branch = "main"
        branch = Mock()
        branch.protected = True
        repo.get_branch.return_value = branch
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")
        assert result["secrets_found"] == []

    @pytest.mark.asyncio
    async def test_execute_commit_exception_skipped(self):
        repo = Mock()
        commit = Mock()
        commit.files = Mock(side_effect=Exception("no access"))
        repo.get_commits.return_value = [commit]
        repo.get_contents = Mock(side_effect=Exception)
        repo.default_branch = "main"
        repo.get_branch.return_value = Mock(protected=True)
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")
        assert "secrets_found" in result

    def test_scan_for_secrets_aws_key(self):
        content = "key = AKIAIOSFODNN7EXAMPLE"
        findings = self.agent._scan_for_secrets("config.py", content)
        assert any(f["type"] == "AWS Access Key" for f in findings)
        assert findings[0]["severity"] == "HIGH"
        assert len(findings[0]["match"]) <= 23  # truncated to 20 + "..."

    def test_scan_for_secrets_github_token(self):
        token = "ghp_" + "a" * 36
        findings = self.agent._scan_for_secrets("script.py", token)
        assert any(f["type"] == "GitHub Token" for f in findings)

    def test_scan_for_secrets_generic_secret(self):
        content = "api_key = 'supersecret123'"
        findings = self.agent._scan_for_secrets("app.py", content)
        assert any(f["type"] == "Generic Secret" for f in findings)

    def test_scan_for_secrets_clean(self):
        content = "x = 42\nprint('hello')"
        findings = self.agent._scan_for_secrets("clean.py", content)
        assert findings == []

    @pytest.mark.asyncio
    async def test_check_security_practices_missing_all(self):
        repo = Mock()
        repo.default_branch = "main"
        repo.get_contents.side_effect = Exception("not found")
        branch = Mock()
        branch.protected = False
        repo.get_branch.return_value = branch

        recs = await self.agent._check_security_practices(repo)
        assert any("SECURITY.md" in r for r in recs)
        assert any("Dependabot" in r for r in recs)
        assert any("branch protection" in r for r in recs)

    @pytest.mark.asyncio
    async def test_check_security_practices_all_good(self):
        repo = Mock()
        repo.default_branch = "main"
        # get_contents succeeds for both SECURITY.md and dependabot.yml
        repo.get_contents.return_value = Mock()
        branch = Mock()
        branch.protected = True
        repo.get_branch.return_value = branch

        recs = await self.agent._check_security_practices(repo)
        assert recs == []

    @pytest.mark.asyncio
    async def test_check_security_practices_outer_exception(self):
        repo = Mock()
        repo.default_branch = "main"
        repo.get_contents.side_effect = Exception
        repo.get_branch.side_effect = Exception("network error")

        recs = await self.agent._check_security_practices(repo)
        assert isinstance(recs, list)


# ── WorkflowOptimizerAgent ────────────────────────────────────────────────────


class TestWorkflowOptimizerAgent:
    def setup_method(self):
        self.github, self.llm, self.audit = _make_deps()
        self.agent = WorkflowOptimizerAgent(self.github, self.llm, self.audit)

    @pytest.mark.asyncio
    async def test_execute_no_workflows_dir(self):
        repo = Mock()
        repo.get_contents.side_effect = Exception("not found")
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")
        assert result["workflows_analyzed"] == 0
        assert "note" in result

    @pytest.mark.asyncio
    async def test_execute_with_workflows(self):
        repo = Mock()
        wf_file = Mock()
        wf_file.name = "ci.yml"
        wf_file.decoded_content = b"runs-on: ubuntu-latest\nactions/checkout@v4"
        repo.get_contents.return_value = [wf_file]
        self.llm.complete.return_value = ""
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")
        assert result["workflows_analyzed"] == 1

    @pytest.mark.asyncio
    async def test_execute_skips_non_yaml(self):
        repo = Mock()
        readme = Mock()
        readme.name = "README.md"
        repo.get_contents.return_value = [readme]
        self.github.get_repository.return_value = repo

        result = await self.agent.execute("owner/repo")
        assert result["workflows_analyzed"] == 0

    @pytest.mark.asyncio
    async def test_analyze_workflow_outdated_checkout(self):
        content = "uses: actions/checkout@v1\nruns-on: ubuntu-latest"
        self.llm.complete.return_value = ""

        result = await self.agent._analyze_workflow("ci.yml", content)
        assert any("checkout" in i for i in result["issues"])
        assert any("checkout@v4" in o for o in result["optimizations"])

    @pytest.mark.asyncio
    async def test_analyze_workflow_clean(self):
        content = "uses: actions/checkout@v4\nruns-on: ubuntu-latest"
        self.llm.complete.return_value = ""

        result = await self.agent._analyze_workflow("ci.yml", content)
        assert result["issues"] == []

    @pytest.mark.asyncio
    async def test_analyze_workflow_llm_exception(self):
        content = "runs-on: ubuntu-latest"
        self.llm.complete.side_effect = Exception("LLM error")

        result = await self.agent._analyze_workflow("ci.yml", content)
        assert isinstance(result["issues"], list)


# ── CLI ───────────────────────────────────────────────────────────────────────


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_main_help(self):
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Autonomous GitHub Agent" in result.output

    def test_list_agents(self):
        result = self.runner.invoke(list_agents)
        assert result.exit_code == 0
        assert "health_monitor" in result.output
        assert "code_reviewer" in result.output
        assert "security_scanner" in result.output

    def test_config_check_no_token(self):
        with patch("autonomous_agent.cli.get_config") as mock_cfg:
            cfg = Mock()
            cfg.github.token = None
            cfg.llm.provider = "anthropic"
            cfg.llm.api_key = "key"
            cfg.automation_level = "semi-auto"
            cfg.enabled_agents = ["health"]
            mock_cfg.return_value = cfg

            result = self.runner.invoke(config_check)
            assert result.exit_code == 0
            assert "Missing" in result.output

    def test_config_check_with_token(self):
        with patch("autonomous_agent.cli.get_config") as mock_cfg:
            cfg = Mock()
            cfg.github.token = "ghp_test"
            cfg.llm.provider = "anthropic"
            cfg.llm.api_key = "sk-ant-test"
            cfg.automation_level = "semi-auto"
            cfg.enabled_agents = ["health", "security"]
            mock_cfg.return_value = cfg

            result = self.runner.invoke(config_check)
            assert result.exit_code == 0
            assert "Set" in result.output

    def test_logs_command_empty(self):
        with patch("autonomous_agent.core.audit_logger.AuditLogger") as MockAudit:
            MockAudit.return_value.get_logs.return_value = []
            result = self.runner.invoke(logs)
            assert result.exit_code == 0

    def test_logs_command_with_entries(self):
        with patch("autonomous_agent.core.audit_logger.AuditLogger") as MockAudit:
            log_entry = Mock()
            log_entry.timestamp = datetime(2026, 6, 29, 12, 0, 0)
            log_entry.agent_name = "TestAgent"
            log_entry.action = "test_action"
            log_entry.repository = "owner/repo"
            MockAudit.return_value.get_logs.return_value = [log_entry]

            result = self.runner.invoke(logs, ["--repo", "owner/repo", "--limit", "5"])
            assert result.exit_code == 0
