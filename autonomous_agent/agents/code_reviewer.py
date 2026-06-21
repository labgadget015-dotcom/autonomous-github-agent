"""Automated code review agent for pull requests."""

from typing import Any

from github.PullRequest import PullRequest

from autonomous_agent.core.base_agent import BaseAgent


class CodeReviewerAgent(BaseAgent):
    """Agent for automated PR code reviews."""

    async def execute(
        self, repository: str, pr_number: int | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute code review on PRs."""
        repo = self.github.get_repository(repository)

        if pr_number:
            prs = [repo.get_pull(pr_number)]
        else:
            prs = self.github.get_pull_requests(repo, state="open")

        results = []
        for pr in prs:
            review_result = await self._review_pr(repo, pr)
            results.append(review_result)

        return {
            "repository": repository,
            "reviewed_prs": len(results),
            "results": results,
        }

    async def _review_pr(self, repo: Any, pr: PullRequest) -> dict[str, Any]:
        """Review a single pull request."""
        review = {
            "pr_number": pr.number,
            "title": pr.title,
            "author": pr.user.login,
            "issues_found": [],
            "suggestions": [],
            "security_concerns": [],
            "score": 0,
        }

        # Get PR files
        files = list(pr.get_files())

        for file in files:
            if file.patch is None:
                continue

            # Analyze with LLM
            analysis = await self._analyze_code_changes(file.filename, file.patch)

            if analysis.get("issues"):
                review["issues_found"].extend(analysis["issues"])

            if analysis.get("suggestions"):
                review["suggestions"].extend(analysis["suggestions"])

            if analysis.get("security_concerns"):
                review["security_concerns"].extend(analysis["security_concerns"])

        # Calculate score
        review["score"] = self._calculate_review_score(review)

        # Post review comment if issues found
        if review["issues_found"] or review["security_concerns"]:
            await self._post_review_comment(pr, review)

        # Log the review
        self.log_action(
            action="code_review",
            repository=f"{repo.owner.login}/{repo.name}",
            details=review,
        )

        return review

    async def _analyze_code_changes(self, filename: str, patch: str) -> dict[str, Any]:
        """Analyze code changes using LLM."""
        prompt = f"""Review the following code changes in {filename}:

{patch}

Provide analysis in the following areas:
1. Code quality issues (syntax, style, best practices)
2. Security concerns (XSS, CSRF, SQL injection, secrets)
3. Performance issues
4. Suggestions for improvement

Return your analysis as structured feedback."""

        try:
            response = self.llm.complete(
                prompt=prompt,
                system="You are an expert code reviewer. Focus on actionable feedback.",
            )

            # Parse LLM response (simplified - in production, use structured output)
            return {
                "issues": self._extract_issues(response),
                "suggestions": self._extract_suggestions(response),
                "security_concerns": self._extract_security(response),
            }
        except Exception:
            return {"issues": [], "suggestions": [], "security_concerns": []}

    def _extract_issues(self, response: str) -> list[str]:
        """Extract issues from LLM response."""
        # Simplified extraction - in production, use structured parsing
        issues = []
        for line in response.split("\n"):
            if "issue" in line.lower() or "problem" in line.lower():
                issues.append(line.strip())
        return issues[:5]  # Limit to top 5

    def _extract_suggestions(self, response: str) -> list[str]:
        """Extract suggestions from LLM response."""
        suggestions = []
        for line in response.split("\n"):
            if "suggest" in line.lower() or "recommend" in line.lower():
                suggestions.append(line.strip())
        return suggestions[:5]

    def _extract_security(self, response: str) -> list[str]:
        """Extract security concerns from LLM response."""
        concerns = []
        for line in response.split("\n"):
            if "security" in line.lower() or "vulnerability" in line.lower():
                concerns.append(line.strip())
        return concerns

    def _calculate_review_score(self, review: dict[str, Any]) -> int:
        """Calculate a review score (0-100)."""
        score = 100
        score -= len(review["issues_found"]) * 5
        score -= len(review["security_concerns"]) * 15
        return max(0, score)

    async def _post_review_comment(
        self, pr: PullRequest, review: dict[str, Any]
    ) -> None:
        """Post review comment on PR."""
        comment_parts = ["## 🤖 Automated Code Review\n"]

        if review["security_concerns"]:
            comment_parts.append("### ⚠️ Security Concerns\n")
            for concern in review["security_concerns"]:
                comment_parts.append(f"- {concern}\n")
            comment_parts.append("\n")

        if review["issues_found"]:
            comment_parts.append("### 🔍 Issues Found\n")
            for issue in review["issues_found"][:5]:
                comment_parts.append(f"- {issue}\n")
            comment_parts.append("\n")

        if review["suggestions"]:
            comment_parts.append("### 💡 Suggestions\n")
            for suggestion in review["suggestions"][:5]:
                comment_parts.append(f"- {suggestion}\n")

        comment_parts.append(f"\n**Review Score:** {review['score']}/100\n")

        comment = "".join(comment_parts)
        self.github.create_issue_comment(pr, comment)
