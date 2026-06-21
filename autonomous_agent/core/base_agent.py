"""Base agent class for all specialized agents."""

from abc import ABC, abstractmethod
from typing import Any

from autonomous_agent.core.audit_logger import AuditLogger
from autonomous_agent.core.config import get_config
from autonomous_agent.core.github_client import GitHubClient
from autonomous_agent.core.llm_client import LLMClient


class BaseAgent(ABC):
    """Base class for all specialized agents."""

    def __init__(
        self,
        github_client: GitHubClient,
        llm_client: LLMClient,
        audit_logger: AuditLogger,
    ):
        """Initialize base agent."""
        self.github = github_client
        self.llm = llm_client
        self.audit = audit_logger
        self.config = get_config()
        self.name = self.__class__.__name__

    @abstractmethod
    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent's main task."""
        pass

    def log_action(
        self,
        action: str,
        repository: str,
        details: dict[str, Any] | None = None,
        rollback: dict[str, Any] | None = None,
    ) -> int:
        """Log an action to the audit system."""
        return self.audit.log_action(
            agent_name=self.name,
            action=action,
            repository=repository,
            details=details,
            rollback_instructions=rollback,
        )

    def requires_approval(self, action: str) -> bool:
        """Check if an action requires human approval."""
        return (
            self.config.requires_approval(action)
            if hasattr(self.config, "requires_approval")
            else False
        )
