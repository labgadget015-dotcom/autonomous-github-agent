#!/usr/bin/env python3
"""
Policy Engine

Provides governance rules and escalation logic for agent actions.
"""

import logging
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Policy engine for governance and escalation.

    Features:
    - Action approval requirements
    - Human-in-the-loop for destructive operations
    - Configurable policy rules
    - Escalation logic
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize policy engine.

        Args:
            config: Configuration dictionary containing:
                - policy_file: Path to policy YAML file
                - auto_approve: List of actions that are auto-approved
                - requires_approval: List of actions requiring approval
        """
        self.config = config

        # Load policies from file if specified
        policy_file = config.get("policy_file", "config/policies.yaml")
        self.policies = self._load_policies(policy_file)

        # Override with config if provided
        if "auto_approved" in config:
            self.policies["auto_approved"] = config["auto_approved"]
        if "requires_approval" in config:
            self.policies["requires_approval"] = config["requires_approval"]

        logger.info(
            f"Policy engine initialized with {len(self.policies.get('requires_approval', []))} approval rules"
        )

    def _load_policies(self, policy_file: str) -> Dict[str, Any]:
        """
        Load policies from YAML file.

        Args:
            policy_file: Path to policy file

        Returns:
            Dictionary of policies
        """
        try:
            path = Path(policy_file)
            if path.exists():
                with open(path, "r") as f:
                    policies = yaml.safe_load(f)
                    logger.info(f"Loaded policies from {policy_file}")
                    return policies
            else:
                logger.warning(f"Policy file not found: {policy_file}. Using defaults.")
                return self._get_default_policies()
        except Exception as e:
            logger.error(f"Error loading policies: {str(e)}. Using defaults.")
            return self._get_default_policies()

    def _get_default_policies(self) -> Dict[str, Any]:
        """
        Get default policies.

        Returns:
            Default policy dictionary
        """
        return {
            "requires_approval": [
                "delete_main_branch",
                "force_push_protected",
                "modify_repo_settings",
                "deploy_production",
                "delete_repository",
                "change_permissions",
                "modify_secrets",
                "delete_workflow",
            ],
            "auto_approved": [
                "delete_stale_branch",
                "update_dependencies",
                "fix_linting",
                "label_issue",
                "add_comment",
                "create_branch",
                "run_tests",
                "update_documentation",
            ],
            "escalation_users": [],
            "approval_timeout_hours": 24,
        }

    async def check_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if an action requires approval.

        Args:
            action: Action name
            params: Action parameters

        Returns:
            Dictionary with 'requires_approval' boolean and optional 'reason'
        """
        requires_approval_list = self.policies.get("requires_approval", [])
        auto_approved_list = self.policies.get("auto_approved", [])

        # Check if action is in auto-approved list
        if action in auto_approved_list:
            logger.info(f"Action '{action}' is auto-approved")
            return {"requires_approval": False, "reason": "Auto-approved action"}

        # Check if action requires approval
        if action in requires_approval_list:
            logger.warning(f"Action '{action}' requires approval")
            return {
                "requires_approval": True,
                "reason": f'Action "{action}" requires human approval per policy',
                "escalation_users": self.policies.get("escalation_users", []),
            }

        # Check for destructive patterns
        if self._is_destructive_action(action, params):
            logger.warning(f"Action '{action}' detected as potentially destructive")
            return {
                "requires_approval": True,
                "reason": "Potentially destructive action requires approval",
                "escalation_users": self.policies.get("escalation_users", []),
            }

        # Default: allow action
        logger.info(f"Action '{action}' approved by default policy")
        return {"requires_approval": False, "reason": "Default approval"}

    def _is_destructive_action(self, action: str, params: Dict[str, Any]) -> bool:
        """
        Check if action appears destructive based on name or parameters.

        Args:
            action: Action name
            params: Action parameters

        Returns:
            True if action appears destructive
        """
        destructive_keywords = ["delete", "remove", "destroy", "drop", "force"]

        # Check action name
        action_lower = action.lower()
        if any(keyword in action_lower for keyword in destructive_keywords):
            return True

        # Check for protected branch operations
        if params.get("branch") in ["main", "master", "production"]:
            if action_lower in ["merge", "delete", "force_push"]:
                return True

        return False

    def add_approval_rule(self, action: str):
        """
        Add an action to the requires_approval list.

        Args:
            action: Action name to require approval for
        """
        if "requires_approval" not in self.policies:
            self.policies["requires_approval"] = []

        if action not in self.policies["requires_approval"]:
            self.policies["requires_approval"].append(action)
            logger.info(f"Added approval rule for action: {action}")

    def remove_approval_rule(self, action: str):
        """
        Remove an action from the requires_approval list.

        Args:
            action: Action name to remove from approval requirements
        """
        if "requires_approval" in self.policies:
            if action in self.policies["requires_approval"]:
                self.policies["requires_approval"].remove(action)
                logger.info(f"Removed approval rule for action: {action}")

    def get_policies(self) -> Dict[str, Any]:
        """
        Get current policies.

        Returns:
            Policy dictionary
        """
        return self.policies.copy()

    def save_policies(self, policy_file: Optional[str] = None):
        """
        Save policies to file.

        Args:
            policy_file: Optional path to save policies (uses config default if not provided)
        """
        if not policy_file:
            policy_file = self.config.get("policy_file", "config/policies.yaml")

        try:
            path = Path(policy_file)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w") as f:
                yaml.dump(self.policies, f, default_flow_style=False)

            logger.info(f"Saved policies to {policy_file}")
        except Exception as e:
            logger.error(f"Error saving policies: {str(e)}")
