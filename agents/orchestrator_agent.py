#!/usr/bin/env python3
"""
Orchestrator Agent

Master orchestrator that manages task delegation, routing, and coordination
among specialized agents.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agent_base import BaseAgent  # noqa: E402
from core.message_queue import MessageQueue  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Master Orchestrator Agent for task delegation and coordination.

    Features:
    - Task routing to specialized agents
    - Policy-based escalation
    - Parallel and sequential execution modes
    - GitHub issue creation for approvals
    - Load balancing
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator agent.

        Args:
            config: Configuration dictionary
        """
        super().__init__("orchestrator", config)

        # Message queue for inter-agent communication
        self.message_queue = MessageQueue(config)

        # Registry of available agents
        self.agent_registry = {}

        # Task routing strategy
        self.routing_strategy = config.get("routing_strategy", "priority")

        # Execution mode
        self.max_parallel_tasks = config.get("max_parallel_tasks", 3)

        logger.info(
            f"Orchestrator initialized with routing strategy: {self.routing_strategy}"
        )

    def register_agent(self, agent_name: str, agent_instance: BaseAgent):
        """
        Register a specialized agent.

        Args:
            agent_name: Name of the agent
            agent_instance: Agent instance
        """
        self.agent_registry[agent_name] = agent_instance
        logger.info(f"Registered agent: {agent_name}")

    def get_supported_actions(self) -> List[str]:
        """
        Get list of actions this agent supports.

        Returns:
            List of supported action names
        """
        return [
            "delegate_task",
            "route_task",
            "execute_parallel",
            "execute_sequential",
            "create_approval_issue",
            "get_agent_status",
        ]

    async def _execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute orchestrator task.

        Args:
            task: Task dictionary

        Returns:
            Result dictionary
        """
        action = task.get("action")
        params = task.get("params", {})

        if action == "delegate_task":
            return await self._delegate_task(params)

        elif action == "route_task":
            return await self._route_task(params)

        elif action == "execute_parallel":
            return await self._execute_parallel(params)

        elif action == "execute_sequential":
            return await self._execute_sequential(params)

        elif action == "create_approval_issue":
            return await self._create_approval_issue(params)

        elif action == "get_agent_status":
            return await self._get_agent_status(params)

        else:
            raise ValueError(f"Unknown action: {action}")

    async def _delegate_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegate a task to the appropriate agent.

        Args:
            params: Task parameters with 'task_type' and 'task_data'

        Returns:
            Result from the delegated agent
        """
        task_type = params.get("task_type")
        task_data = params.get("task_data", {})

        # Determine which agent should handle this task
        agent_name = self._determine_agent(task_type)

        if not agent_name:
            logger.error(f"No agent found for task type: {task_type}")
            return {
                "status": "error",
                "error": f"No agent available for task type: {task_type}",
            }

        # Get the agent
        agent = self.agent_registry.get(agent_name)

        if not agent:
            logger.error(f"Agent not registered: {agent_name}")
            return {"status": "error", "error": f"Agent not found: {agent_name}"}

        # Delegate the task
        logger.info(f"Delegating {task_type} to {agent_name}")

        try:
            result = await agent.execute(task_data)

            # Handle approval requirements
            if result.get("status") == "pending_approval":
                approval_result = await self._create_approval_issue(
                    {
                        "action": task_type,
                        "agent": agent_name,
                        "task_data": task_data,
                        "reason": result.get("approval_reason"),
                    }
                )
                result["approval_issue"] = approval_result

            return result

        except Exception as e:
            logger.error(f"Error delegating task to {agent_name}: {str(e)}")
            return {"status": "error", "error": str(e), "agent": agent_name}

    def _determine_agent(self, task_type: str) -> Optional[str]:
        """
        Determine which agent should handle a task type.

        Args:
            task_type: Type of task

        Returns:
            Agent name or None
        """
        # Task type to agent mapping
        task_agent_map = {
            "pr_review": "pr_review_agent",
            "issue_triage": "issue_triager",
            "security_scan": "security_scanner",
            "documentation": "doc_generator",
            "dependency_update": "dependency_manager",
            "run_tests": "test_runner",
            "deploy": "deployment_agent",
            "monitor": "monitoring_agent",
        }

        return task_agent_map.get(task_type)

    async def _route_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a task to an agent using the configured routing strategy.

        Args:
            params: Task parameters

        Returns:
            Routing decision
        """
        task_type = params.get("task_type")
        priority = params.get("priority", 0)

        agent_name = self._determine_agent(task_type)

        if not agent_name:
            return {"status": "error", "error": f"No agent for task type: {task_type}"}

        # Add to message queue
        await self.message_queue.enqueue(
            queue_name=f"agent:{agent_name}", task=params, priority=priority
        )

        return {
            "status": "queued",
            "agent": agent_name,
            "queue": f"agent:{agent_name}",
            "priority": priority,
        }

    async def _execute_parallel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute multiple tasks in parallel.

        Args:
            params: Contains 'tasks' list

        Returns:
            Results from all tasks
        """
        tasks = params.get("tasks", [])

        if not tasks:
            return {"status": "error", "error": "No tasks provided"}

        # Limit parallel execution
        batch_size = min(len(tasks), self.max_parallel_tasks)

        logger.info(
            f"Executing {len(tasks)} tasks in parallel (batch size: {batch_size})"
        )

        results = []

        # Execute in batches
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i : i + batch_size]

            # Create coroutines for each task
            coroutines = [
                self._delegate_task(
                    {"task_type": t.get("type"), "task_data": t.get("data")}
                )
                for t in batch
            ]

            # Execute batch in parallel
            batch_results = await asyncio.gather(*coroutines, return_exceptions=True)
            results.extend(batch_results)

        return {"status": "completed", "total_tasks": len(tasks), "results": results}

    async def _execute_sequential(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute multiple tasks sequentially.

        Args:
            params: Contains 'tasks' list

        Returns:
            Results from all tasks
        """
        tasks = params.get("tasks", [])

        if not tasks:
            return {"status": "error", "error": "No tasks provided"}

        logger.info(f"Executing {len(tasks)} tasks sequentially")

        results = []

        for task in tasks:
            result = await self._delegate_task(
                {"task_type": task.get("type"), "task_data": task.get("data")}
            )
            results.append(result)

            # Stop on error if configured
            if result.get("status") == "error" and params.get("stop_on_error", False):
                logger.warning(
                    f"Stopping execution due to error in task: {task.get('type')}"
                )
                break

        return {
            "status": "completed",
            "total_tasks": len(tasks),
            "completed": len(results),
            "results": results,
        }

    async def _create_approval_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a GitHub issue for approval.

        Args:
            params: Contains action details requiring approval

        Returns:
            Created issue information
        """
        action = params.get("action")
        agent = params.get("agent")
        reason = params.get("reason", "Action requires approval")
        task_data = params.get("task_data", {})

        # Get repository info from config or task data
        repo_owner = task_data.get("repo_owner", self.config.get("default_repo_owner"))
        repo_name = task_data.get("repo_name", self.config.get("default_repo_name"))

        if not repo_owner or not repo_name:
            logger.error("Cannot create approval issue: repository information missing")
            return {"status": "error", "error": "Repository information not provided"}

        # Create issue title and body
        title = f"🔐 Approval Required: {action}"
        body = f"""
## Approval Request

**Action:** {action}  
**Agent:** {agent}  
**Reason:** {reason}  
**Requested:** {datetime.now().isoformat()}

### Task Details
```json
{task_data}
```

### Instructions
To approve this action, comment with: `/approve`  
To reject this action, comment with: `/reject`

**Note:** This issue was automatically created by the Orchestrator Agent.
"""

        try:
            issue = self.github.create_issue(
                owner=repo_owner,
                repo=repo_name,
                title=title,
                body=body,
                labels=["approval-required", "orchestrator"],
            )

            logger.info(f"Created approval issue #{issue.number}")

            return {
                "status": "success",
                "issue_number": issue.number,
                "issue_url": issue.html_url,
            }

        except Exception as e:
            logger.error(f"Error creating approval issue: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _get_agent_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get status of all registered agents.

        Args:
            params: Optional filters

        Returns:
            Status of all agents
        """
        agent_status = {}

        for agent_name, agent in self.agent_registry.items():
            try:
                capabilities = agent.get_capabilities()
                agent_status[agent_name] = {
                    "available": True,
                    "capabilities": capabilities,
                }
            except Exception as e:
                agent_status[agent_name] = {"available": False, "error": str(e)}

        return {
            "status": "success",
            "total_agents": len(self.agent_registry),
            "agents": agent_status,
        }
