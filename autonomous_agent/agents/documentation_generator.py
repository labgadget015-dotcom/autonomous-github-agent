"""Documentation generation and maintenance agent."""

from typing import Any

from autonomous_agent.core.base_agent import BaseAgent


class DocumentationGeneratorAgent(BaseAgent):
    """Agent for automated documentation generation."""

    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute documentation tasks."""
        repo = self.github.get_repository(repository)

        results = {"repository": repository, "docs_updated": [], "suggestions": []}

        # Check README quality
        try:
            readme = repo.get_readme()
            content = readme.decoded_content.decode()

            analysis = await self._analyze_readme(content)
            results["suggestions"].extend(analysis)
        except Exception:
            results["suggestions"].append("No README.md found - create one")

        return results

    async def _analyze_readme(self, content: str) -> list[str]:
        """Analyze README quality."""
        suggestions = []

        required_sections = ["Installation", "Usage", "Contributing", "License"]

        for section in required_sections:
            if section.lower() not in content.lower():
                suggestions.append(f"Add '{section}' section to README")

        if len(content) < 500:
            suggestions.append("README is too brief - add more details")

        if "```" not in content:
            suggestions.append("Add code examples to README")

        return suggestions
