"""
Autonomous GitHub Agent - AI-powered repository management system.
"""

__version__ = "0.1.0"
__author__ = "Autonomous Agent Team"

from autonomous_agent.core.orchestrator import Orchestrator
from autonomous_agent.core.github_client import GitHubClient
from autonomous_agent.core.config import Config

__all__ = ["Orchestrator", "GitHubClient", "Config"]
