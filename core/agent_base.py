#!/usr/bin/env python3
"""
Base Agent Class

Provides the foundational class for all specialized agents with lifecycle management,
GitHub integration, LLM integration, audit logging, and policy enforcement.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from .audit_logger import AuditLogger
from .github_client import GitHubClient
from .llm_provider import LLMClient
from .policy_engine import PolicyEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all autonomous agents.

    Provides:
    - Lifecycle management (validate -> execute -> log -> return)
    - GitHub API integration
    - LLM integration
    - Audit logging
    - Policy enforcement
    """

    def __init__(self, name: str, config: dict[str, Any]):
        """
        Initialize the base agent.

        Args:
            name: Unique name for this agent
            config: Configuration dictionary containing API keys and settings
        """
        self.name = name
        self.config = config
        self.github = GitHubClient(config)
        self.llm = LLMClient(config)
        self.audit = AuditLogger(config)
        self.policy = PolicyEngine(config)

        self._initialized = True
        logger.info(f"Initialized agent: {self.name}")

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a task with full lifecycle management.

        Lifecycle:
        1. Validate the task
        2. Check policy requirements
        3. Execute the task
        4. Log the action
        5. Return result

        Args:
            task: Task dictionary with action and parameters

        Returns:
            Result dictionary with status and output
        """
        task_id = task.get("id", datetime.now().isoformat())
        action = task.get("action", "unknown")

        logger.info(f"[{self.name}] Starting task {task_id}: {action}")

        try:
            # Step 1: Validate
            if not self.validate(task):
                return {
                    "status": "error",
                    "error": "Task validation failed",
                    "task_id": task_id,
                }

            # Step 2: Check policy
            policy_check = await self.policy.check_action(
                action, task.get("params", {})
            )
            if policy_check["requires_approval"]:
                logger.warning(f"[{self.name}] Action {action} requires approval")
                return {
                    "status": "pending_approval",
                    "message": "Action requires human approval",
                    "approval_reason": policy_check.get("reason", "Policy requirement"),
                    "task_id": task_id,
                }

            # Step 3: Execute
            result = await self._execute(task)

            # Step 4: Log
            await self.audit.log_action(
                agent=self.name,
                action=action,
                params=task.get("params", {}),
                result=result,
                task_id=task_id,
            )

            logger.info(f"[{self.name}] Completed task {task_id}")

            # Step 5: Return
            return {
                "status": "success",
                "result": result,
                "task_id": task_id,
                "agent": self.name,
            }

        except Exception as e:
            logger.error(f"[{self.name}] Error executing task {task_id}: {str(e)}")

            # Log the error
            await self.audit.log_action(
                agent=self.name,
                action=action,
                params=task.get("params", {}),
                result={"error": str(e)},
                task_id=task_id,
                status="error",
            )

            return {
                "status": "error",
                "error": str(e),
                "task_id": task_id,
                "agent": self.name,
            }

    def validate(self, task: dict[str, Any]) -> bool:
        """
        Validate task parameters.

        Args:
            task: Task dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["action"]
        return all(field in task for field in required_fields)

    @abstractmethod
    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the actual task logic. Must be implemented by subclasses.

        Args:
            task: Task dictionary with action and parameters

        Returns:
            Result dictionary
        """
        pass

    def get_capabilities(self) -> dict[str, Any]:
        """
        Get agent capabilities.

        Returns:
            Dictionary describing agent capabilities
        """
        return {
            "name": self.name,
            "actions": self.get_supported_actions(),
            "version": "1.0.0",
        }

    @abstractmethod
    def get_supported_actions(self) -> list:
        """
        Get list of actions this agent supports.

        Returns:
            List of supported action names
        """
        pass
