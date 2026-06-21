"""Security scanning and vulnerability detection agent."""

import re
from typing import Any

from autonomous_agent.core.base_agent import BaseAgent


class SecurityScannerAgent(BaseAgent):
    """Agent for security scanning and vulnerability detection."""

    SECRET_PATTERNS = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "GitHub Token": r"ghp_[a-zA-Z0-9]{36}",
        "OpenAI API Key": r"sk-[a-zA-Z0-9]{48}",
        "Private Key": r"-----BEGIN (RSA |)PRIVATE KEY-----",
        "Generic Secret": r"""(secret|password|api_key)\s*=\s*['"][^'"]+['"]""",
    }

    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute security scan on repository."""
        repo = self.github.get_repository(repository)

        results = {
            "repository": repository,
            "secrets_found": [],
            "vulnerabilities": [],
            "recommendations": [],
        }

        # Scan recent commits for secrets
        commits = list(repo.get_commits())[:50]

        for commit in commits:
            try:
                for file in commit.files:
                    if file.patch:
                        secrets = self._scan_for_secrets(file.filename, file.patch)
                        if secrets:
                            results["secrets_found"].extend(secrets)
            except Exception:
                continue

        # Check for security best practices
        results["recommendations"] = await self._check_security_practices(repo)

        self.log_action(action="security_scan", repository=repository, details=results)

        return results

    def _scan_for_secrets(self, filename: str, content: str) -> list[dict[str, Any]]:
        """Scan content for potential secrets."""
        findings = []

        for secret_type, pattern in self.SECRET_PATTERNS.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                findings.append(
                    {
                        "type": secret_type,
                        "file": filename,
                        "match": match.group()[:20] + "...",  # Truncate
                        "severity": "HIGH",
                    }
                )

        return findings

    async def _check_security_practices(self, repo: Any) -> list[str]:
        """Check for security best practices."""
        recommendations = []

        try:
            # Check for SECURITY.md
            try:
                repo.get_contents("SECURITY.md")
            except Exception:
                recommendations.append(
                    "Add SECURITY.md with vulnerability reporting instructions"
                )

            # Check for dependabot
            try:
                repo.get_contents(".github/dependabot.yml")
            except Exception:
                recommendations.append(
                    "Enable Dependabot for automated dependency updates"
                )

            # Check branch protection
            default_branch = repo.get_branch(repo.default_branch)
            if not default_branch.protected:
                recommendations.append("Enable branch protection on default branch")

        except Exception:
            pass

        return recommendations
