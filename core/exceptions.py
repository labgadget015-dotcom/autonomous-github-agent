#!/usr/bin/env python3
"""
Custom exception hierarchy for the autonomous GitHub agent.

Provides specific exception types that give callers fine-grained control
over error handling and avoids masking unexpected failures with broad
``except Exception`` clauses.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class AgentError(Exception):
    """Base class for all agent-related errors."""


# ---------------------------------------------------------------------------
# GitHub / API errors
# ---------------------------------------------------------------------------


class GitHubAPIError(AgentError):
    """Raised when a GitHub API call fails."""


class RateLimitError(GitHubAPIError):
    """Raised when the GitHub API rate limit is exhausted."""


# ---------------------------------------------------------------------------
# LLM errors
# ---------------------------------------------------------------------------


class LLMError(AgentError):
    """Raised when an LLM API call fails."""


class LLMConfigError(LLMError):
    """Raised when LLM configuration (e.g. missing API key) is invalid."""


# ---------------------------------------------------------------------------
# Policy errors
# ---------------------------------------------------------------------------


class PolicyError(AgentError):
    """Raised when a policy check fails or is misconfigured."""


class ApprovalRequiredError(PolicyError):
    """Raised when an action requires human approval before proceeding."""


# ---------------------------------------------------------------------------
# Cache errors
# ---------------------------------------------------------------------------


class CacheError(AgentError):
    """Raised when a caching operation fails."""


# ---------------------------------------------------------------------------
# Audit errors
# ---------------------------------------------------------------------------


class AuditError(AgentError):
    """Raised when an audit-logging operation fails."""
