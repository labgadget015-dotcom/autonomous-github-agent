"""Unit tests for agents/code_review_agent.py"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


def run(coro):
    return asyncio.run(coro)


def _make_agent(config=None):
    from agents.code_review_agent import CodeReviewAgent

    with (
        patch("core.agent_base.GitHubClient"),
        patch("core.agent_base.LLMClient"),
        patch("core.agent_base.AuditLogger"),
        patch("core.agent_base.PolicyEngine"),
    ):
        agent = CodeReviewAgent(config or {"github_token": "x"})
        agent.policy.check_action = AsyncMock(return_value={"requires_approval": False})
        agent.audit.log_action = AsyncMock()
    return agent


class TestCodeReviewAgentInit:
    def test_name(self):
        assert _make_agent().name == "code_review_agent"

    def test_supported_actions(self):
        assert _make_agent().get_supported_actions() == ["review_pr"]


class TestExecuteDispatch:
    def setup_method(self):
        self.agent = _make_agent()

    def test_unsupported_action_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Unsupported action"):
            run(self.agent._execute({"action": "bad_action"}))

    def test_review_pr_dispatches(self):
        self.agent._review_pr = AsyncMock(return_value={"pr_number": 7, "review_length": 100})
        result = run(self.agent._execute({"action": "review_pr", "params": {"repo": "o/r", "pr_number": 7}}))
        self.agent._review_pr.assert_called_once_with({"repo": "o/r", "pr_number": 7})
        assert result["pr_number"] == 7


class TestReviewPr:
    def setup_method(self):
        self.agent = _make_agent()

    def test_review_pr_posts_comment(self):
        mock_file = MagicMock()
        mock_file.filename = "src/main.py"
        mock_file.patch = "@@ -1 +1 @@\n+print('hi')"

        mock_pr = MagicMock()
        mock_pr.title = "Add feature"
        mock_pr.body = "desc"
        mock_pr.get_files.return_value = [mock_file]
        mock_pr.create_review = MagicMock()

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        self.agent.github.client.get_repo.return_value = mock_repo

        self.agent.llm.generate = AsyncMock(return_value={
            "content": "Looks good!",
            "usage": {"total_tokens": 42},
        })

        result = run(self.agent._review_pr({"repo": "o/r", "pr_number": 3}))
        mock_pr.create_review.assert_called_once()
        assert result["pr_number"] == 3
        assert result["review_length"] == len("Looks good!")
        assert result["tokens_used"] == 42

    def test_review_pr_truncates_long_diff(self):
        mock_file = MagicMock()
        mock_file.filename = "big.py"
        mock_file.patch = "x" * 20000

        mock_pr = MagicMock()
        mock_pr.title = "Big PR"
        mock_pr.body = None
        mock_pr.get_files.return_value = [mock_file]
        mock_pr.create_review = MagicMock()

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        self.agent.github.client.get_repo.return_value = mock_repo

        captured_prompt = {}

        async def capture_generate(prompt, **kwargs):
            captured_prompt["prompt"] = prompt
            return {"content": "ok", "usage": {}}

        self.agent.llm.generate = capture_generate
        run(self.agent._review_pr({"repo": "o/r", "pr_number": 1}))
        assert len(captured_prompt["prompt"]) < 20000

    def test_review_pr_handles_file_with_no_patch(self):
        mock_file = MagicMock()
        mock_file.filename = "binary.png"
        mock_file.patch = None

        mock_pr = MagicMock()
        mock_pr.title = "Binary"
        mock_pr.body = None
        mock_pr.get_files.return_value = [mock_file]
        mock_pr.create_review = MagicMock()

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        self.agent.github.client.get_repo.return_value = mock_repo
        self.agent.llm.generate = AsyncMock(return_value={"content": "ok", "usage": {}})

        result = run(self.agent._review_pr({"repo": "o/r", "pr_number": 2}))
        assert result["repo"] == "o/r"
