"""CI/CD workflow optimization agent."""

from typing import Any

from autonomous_agent.core.base_agent import BaseAgent


class WorkflowOptimizerAgent(BaseAgent):
    """Agent for CI/CD workflow analysis and optimization."""

    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute workflow optimization."""
        repo = self.github.get_repository(repository)

        results = {
            "repository": repository,
            "workflows_analyzed": 0,
            "issues_found": [],
            "optimizations": [],
        }

        try:
            # Get workflow files
            workflows_path = ".github/workflows"
            contents = repo.get_contents(workflows_path)

            for content in contents:
                if content.name.endswith((".yml", ".yaml")):
                    results["workflows_analyzed"] += 1

                    workflow_content = content.decoded_content.decode()
                    analysis = await self._analyze_workflow(
                        content.name, workflow_content
                    )

                    if analysis["issues"]:
                        results["issues_found"].extend(analysis["issues"])
                    if analysis["optimizations"]:
                        results["optimizations"].extend(analysis["optimizations"])

        except Exception:
            results["note"] = "No workflows found or unable to access"

        return results

    async def _analyze_workflow(self, filename: str, content: str) -> dict[str, Any]:
        """Analyze a workflow file."""
        issues = []
        optimizations = []

        # Check for common issues
        if "actions/checkout@v1" in content:
            issues.append(f"{filename}: Using outdated checkout action (v1)")
            optimizations.append(f"{filename}: Update to actions/checkout@v4")

        if "runs-on: ubuntu-latest" not in content and "runs-on: ubuntu" in content:
            optimizations.append(f"{filename}: Consider pinning Ubuntu version")

        # Use LLM for deeper analysis
        try:
            prompt = f"""Analyze this GitHub Actions workflow for optimization opportunities:

{content}

Identify:
1. Security issues
2. Performance improvements
3. Best practice violations"""

            self.llm.complete(prompt)
            # Parse response for additional insights
        except Exception:
            pass

        return {"issues": issues, "optimizations": optimizations}
