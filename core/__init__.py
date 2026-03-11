"""
Core infrastructure for autonomous GitHub AI system.

This package provides the foundational classes and utilities for building
autonomous AI agents that operate on GitHub repositories.
"""

__version__ = "1.0.0"

from .agent_base import BaseAgent
from .audit_logger import AuditLogger
from .exceptions import (
    AgentError,
    AuditError,
    ApprovalRequiredError,
    CacheError,
    GitHubAPIError,
    LLMConfigError,
    LLMError,
    PolicyError,
    RateLimitError,
)
from .github_client import GitHubClient
from .llm_provider import LLMClient
from .message_queue import MessageQueue
from .policy_engine import PolicyEngine

__all__ = [
    "AgentError",
    "ApprovalRequiredError",
    "AuditError",
    "AuditLogger",
    "BaseAgent",
    "CacheError",
    "GitHubAPIError",
    "GitHubClient",
    "LLMClient",
    "LLMConfigError",
    "LLMError",
    "MessageQueue",
    "PolicyEngine",
    "PolicyError",
    "RateLimitError",
]
