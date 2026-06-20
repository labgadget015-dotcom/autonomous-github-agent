#!/usr/bin/env python3
"""Code Review Agent — reviews pull requests via LLM and posts findings."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agent_base import BaseAgent  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert code reviewer. Analyze the diff and provide concise, "
    "actionable feedback covering: correctness, security, performance, style, "
    "and test coverage. Format your response as markdown."
)


class CodeReviewAgent(BaseAgent):
    """Reviews pull requests using an LLM and posts the review as a PR comment."""

    def __init__(self, config: dict[str, Any]):
        super().__init__("code_review_agent", config)

    def get_supported_actions(self) -> list:
        return ["review_pr"]

    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action")
        if action == "review_pr":
            return await self._review_pr(task.get("params", {}))
        raise ValueError(f"Unsupported action: {action}")

    async def _review_pr(self, params: dict[str, Any]) -> dict[str, Any]:
        """Fetch a PR diff, send it to the LLM, and post the review."""
        repo_name = params["repo"]
        pr_number = int(params["pr_number"])

        repo = self.github.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Collect diff from files
        diff_parts = []
        for f in pr.get_files():
            patch = f.patch or ""
            diff_parts.append(f"### {f.filename}\n{patch}")
        raw_diff = "\n\n".join(diff_parts)
        diff = raw_diff[:8000]

        prompt = (
            f"Pull Request #{pr_number}: {pr.title}\n\n"
            f"Description:\n{pr.body or '(none)'}\n\n"
            f"Diff:\n```diff\n{diff}\n```"
        )

        llm_response = await self.llm.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=1500,
            temperature=0.3,
        )

        review_body = llm_response["content"]
        pr.create_review(body=review_body, event="COMMENT")

        logger.info("Posted review on %s#%d", repo_name, pr_number)
        return {
            "repo": repo_name,
            "pr_number": pr_number,
            "review_length": len(review_body),
            "tokens_used": llm_response.get("usage", {}).get("total_tokens", 0),
        }


def main():
    parser = argparse.ArgumentParser(description="Review a pull request via LLM.")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--pr", required=True, type=int, help="Pull request number")
    args = parser.parse_args()

    config = {
        "github_token": os.getenv("GITHUB_TOKEN"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "llm_provider": "anthropic",
    }
    agent = CodeReviewAgent(config)
    task = {
        "action": "review_pr",
        "params": {"repo": args.repo, "pr_number": args.pr},
    }
    result = asyncio.run(agent.execute(task))
    print(result)


if __name__ == "__main__":
    main()
