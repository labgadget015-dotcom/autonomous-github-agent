"""
Core infrastructure for autonomous GitHub AI system.

This package provides the foundational classes and utilities for building
autonomous AI agents that operate on GitHub repositories.
"""

__version__ = "1.0.0"

from .agent_base import BaseAgent
from .github_client import GitHubClient
from .llm_provider import LLMProvider
from .audit_logger import AuditLogger
from .policy_engine import PolicyEngine
from .message_queue import MessageQueue

__all__ = [
    "BaseAgent",
    "GitHubClient",
    "LLMProvider",
    "AuditLogger",
    "PolicyEngine",
    "MessageQueue",
]
