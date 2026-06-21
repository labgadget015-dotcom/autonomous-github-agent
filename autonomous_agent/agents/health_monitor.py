"""Health monitoring agent for repository assessment."""

from datetime import datetime
from typing import Any

from github.Repository import Repository

from autonomous_agent.core.base_agent import BaseAgent


class HealthMonitorAgent(BaseAgent):
    """Agent for monitoring repository health and metrics."""

    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute health check on repository."""
        repo = self.github.get_repository(repository)

        health_report = {
            "repository": repository,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": await self._gather_metrics(repo),
            "issues": await self._identify_issues(repo),
            "recommendations": [],
        }

        # Generate recommendations
        health_report["recommendations"] = self._generate_recommendations(health_report)

        # Log the health check
        self.log_action(
            action="health_check", repository=repository, details=health_report
        )

        return health_report

    async def _gather_metrics(self, repo: Repository) -> dict[str, Any]:
        """Gather repository metrics."""
        return {
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "watchers": repo.watchers_count,
            "size_kb": repo.size,
            "default_branch": repo.default_branch,
            "is_archived": repo.archived,
            "is_private": repo.private,
            "has_issues": repo.has_issues,
            "has_wiki": repo.has_wiki,
            "has_pages": repo.has_pages,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
        }

    async def _identify_issues(self, repo: Repository) -> dict[str, Any]:
        """Identify potential issues in the repository."""
        issues = {
            "stale_branches": [],
            "old_pull_requests": [],
            "security_alerts": [],
            "missing_files": [],
            "outdated_dependencies": [],
        }

        # Check for stale branches
        branches = list(repo.get_branches())
        protected_branch = repo.default_branch

        for branch in branches:
            if branch.name == protected_branch:
                continue

            try:
                commit = branch.commit
                if commit.commit.author.date:
                    days_old = (
                        datetime.utcnow()
                        - commit.commit.author.date.replace(tzinfo=None)
                    ).days
                    if days_old > 90:
                        issues["stale_branches"].append(
                            {
                                "name": branch.name,
                                "days_old": days_old,
                                "last_commit": commit.commit.author.date.isoformat(),
                            }
                        )
            except Exception:
                pass

        # Check for old PRs
        prs = self.github.get_pull_requests(repo, state="open")
        for pr in prs:
            days_old = (datetime.utcnow() - pr.created_at.replace(tzinfo=None)).days
            if days_old > 30:
                issues["old_pull_requests"].append(
                    {
                        "number": pr.number,
                        "title": pr.title,
                        "days_old": days_old,
                        "author": pr.user.login,
                    }
                )

        # Check for missing essential files
        essential_files = ["README.md", "LICENSE", ".gitignore", "CONTRIBUTING.md"]
        try:
            contents = repo.get_contents("")
            existing_files = {item.name for item in contents if item.type == "file"}

            for essential in essential_files:
                if essential not in existing_files:
                    issues["missing_files"].append(essential)
        except Exception:
            pass

        return issues

    def _generate_recommendations(self, health_report: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []
        issues = health_report["issues"]

        if issues["stale_branches"]:
            count = len(issues["stale_branches"])
            recommendations.append(
                f"Delete {count} stale branch(es) not updated in 90+ days"
            )

        if issues["old_pull_requests"]:
            count = len(issues["old_pull_requests"])
            recommendations.append(
                f"Review or close {count} pull request(s) open for 30+ days"
            )

        if issues["missing_files"]:
            recommendations.append(
                f"Add missing files: {', '.join(issues['missing_files'])}"
            )

        if health_report["metrics"]["open_issues"] > 50:
            recommendations.append(
                "High number of open issues - consider triage and cleanup"
            )

        return recommendations
