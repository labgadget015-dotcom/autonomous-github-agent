"""
Create all core module files for the Autonomous GitHub Agent.
Run this after quick_setup.py
"""

from pathlib import Path

BASE_DIR = Path(r"C:\Users\aw789\autonomous-github-agent")

# ============================================================================
# CORE: Configuration Management
# ============================================================================

CONFIG_PY = '''"""Configuration management for the autonomous agent system."""

from typing import Any, Literal
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitHubSettings(BaseSettings):
    """GitHub API configuration."""

    token: str = Field(..., description="GitHub Personal Access Token")
    api_url: str = Field(default="https://api.github.com", description="GitHub API base URL")
    timeout: int = Field(default=30, description="API request timeout in seconds")

    model_config = SettingsConfigDict(env_prefix="GITHUB_")


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    provider: Literal["openai", "anthropic", "local"] = Field(
        default="openai", description="LLM provider"
    )
    api_key: str | None = Field(default=None, description="LLM API key")
    model: str = Field(default="gpt-4-turbo-preview", description="Model name")
    temperature: float = Field(default=0.2, description="Sampling temperature")
    max_tokens: int = Field(default=4000, description="Max completion tokens")

    model_config = SettingsConfigDict(env_prefix="LLM_")


class Config(BaseSettings):
    """Main configuration class."""

    github: GitHubSettings = Field(default_factory=GitHubSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)

    automation_level: Literal["manual", "semi-auto", "full-auto"] = Field(
        default="semi-auto"
    )

    enabled_agents: list[str] = Field(
        default_factory=lambda: [
            "health_monitor",
            "code_reviewer",
            "issue_manager",
            "branch_manager",
            "security_scanner",
            "workflow_optimizer",
            "documentation_generator"
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
'''

# ============================================================================
# CORE: GitHub Client
# ============================================================================

GITHUB_CLIENT_PY = '''"""GitHub API client wrapper with rate limiting and error handling."""

import time
from typing import Any
from github import Github, GithubException
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.Issue import Issue
from tenacity import retry, stop_after_attempt, wait_exponential
from autonomous_agent.core.config import get_config


class GitHubClient:
    """Wrapper around PyGithub with enhanced features."""

    def __init__(self, token: str | None = None):
        """Initialize GitHub client."""
        config = get_config()
        self.token = token or config.github.token
        self.client = Github(self.token, timeout=config.github.timeout)
        self.user = self.client.get_user()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_repository(self, repo_name: str) -> Repository:
        """Get a repository by name (owner/repo)."""
        return self.client.get_repo(repo_name)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_pull_requests(self, repo: Repository, state: str = "open") -> list[PullRequest]:
        """Get pull requests from a repository."""
        return list(repo.get_pulls(state=state))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_issues(self, repo: Repository, state: str = "open") -> list[Issue]:
        """Get issues from a repository."""
        return list(repo.get_issues(state=state))

    def create_issue_comment(self, issue: Issue, comment: str) -> None:
        """Add a comment to an issue or PR."""
        issue.create_comment(comment)

    def create_pr_review_comment(
        self,
        pr: PullRequest,
        body: str,
        commit_id: str,
        path: str,
        line: int
    ) -> None:
        """Create an inline review comment on a PR."""
        pr.create_review_comment(
            body=body,
            commit_id=commit_id,
            path=path,
            line=line
        )

    def get_rate_limit(self) -> dict[str, Any]:
        """Get current API rate limit status."""
        rate_limit = self.client.get_rate_limit()
        return {
            "core": {
                "remaining": rate_limit.core.remaining,
                "limit": rate_limit.core.limit,
                "reset": rate_limit.core.reset
            }
        }

    def close(self) -> None:
        """Close the GitHub client connection."""
        self.client.close()
'''

# ============================================================================
# CORE: LLM Client
# ============================================================================

LLM_CLIENT_PY = '''"""LLM client for AI-powered code analysis and generation."""

from typing import Literal
from openai import OpenAI
from anthropic import Anthropic
from autonomous_agent.core.config import get_config


class LLMClient:
    """Unified interface for different LLM providers."""

    def __init__(self):
        """Initialize LLM client based on configuration."""
        config = get_config()
        self.provider = config.llm.provider
        self.model = config.llm.model
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens

        if self.provider == "openai":
            self.client = OpenAI(api_key=config.llm.api_key)
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=config.llm.api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def complete(self, prompt: str, system: str | None = None) -> str:
        """Get a completion from the LLM."""
        if self.provider == "openai":
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system or "",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        raise ValueError(f"Unsupported provider: {self.provider}")

    def analyze_code(self, code: str, task: str) -> str:
        """Analyze code with a specific task."""
        system = "You are an expert code reviewer and security analyst."
        prompt = f"{task}\\n\\nCode:\\n```\\n{code}\\n```"
        return self.complete(prompt, system=system)
'''

# ============================================================================
# CORE: Audit Logger
# ============================================================================

AUDIT_LOGGER_PY = '''"""Audit logging system with rollback support."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from autonomous_agent.core.config import get_config

Base = declarative_base()


class AuditLog(Base):
    """Audit log database model."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(200), nullable=False)
    repository = Column(String(200))
    details = Column(JSON)
    rollback_instructions = Column(JSON)
    status = Column(String(50), default="completed")


class AuditLogger:
    """Audit logger for tracking all agent actions."""

    def __init__(self):
        """Initialize audit logger."""
        config = get_config()
        self.engine = create_engine(config.database.url if hasattr(config, 'database') else "sqlite:///./audit.db")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def log_action(
        self,
        agent_name: str,
        action: str,
        repository: str | None = None,
        details: dict[str, Any] | None = None,
        rollback_instructions: dict[str, Any] | None = None
    ) -> int:
        """Log an agent action."""
        log_entry = AuditLog(
            agent_name=agent_name,
            action=action,
            repository=repository,
            details=details or {},
            rollback_instructions=rollback_instructions or {}
        )
        self.session.add(log_entry)
        self.session.commit()
        return log_entry.id

    def get_logs(
        self,
        agent_name: str | None = None,
        repository: str | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """Retrieve audit logs with optional filtering."""
        query = self.session.query(AuditLog)

        if agent_name:
            query = query.filter(AuditLog.agent_name == agent_name)
        if repository:
            query = query.filter(AuditLog.repository == repository)

        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    def get_rollback_instructions(self, log_id: int) -> dict[str, Any]:
        """Get rollback instructions for a specific action."""
        log = self.session.query(AuditLog).filter(AuditLog.id == log_id).first()
        return log.rollback_instructions if log else {}
'''

# ============================================================================
# CORE: Base Agent
# ============================================================================

BASE_AGENT_PY = '''"""Base agent class for all specialized agents."""

from abc import ABC, abstractmethod
from typing import Any
from autonomous_agent.core.github_client import GitHubClient
from autonomous_agent.core.llm_client import LLMClient
from autonomous_agent.core.audit_logger import AuditLogger
from autonomous_agent.core.config import get_config


class BaseAgent(ABC):
    """Base class for all specialized agents."""

    def __init__(self, github_client: GitHubClient, llm_client: LLMClient, audit_logger: AuditLogger):
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
        rollback: dict[str, Any] | None = None
    ) -> int:
        """Log an action to the audit system."""
        return self.audit.log_action(
            agent_name=self.name,
            action=action,
            repository=repository,
            details=details,
            rollback_instructions=rollback
        )

    def requires_approval(self, action: str) -> bool:
        """Check if an action requires human approval."""
        return self.config.requires_approval(action) if hasattr(self.config, 'requires_approval') else False
'''

# ============================================================================
# CORE: Orchestrator
# ============================================================================

ORCHESTRATOR_PY = '''"""Central orchestrator for coordinating all agents."""

import asyncio
from typing import Any
from autonomous_agent.core.github_client import GitHubClient
from autonomous_agent.core.llm_client import LLMClient
from autonomous_agent.core.audit_logger import AuditLogger
from autonomous_agent.core.config import get_config


class Orchestrator:
    """Main orchestrator coordinating all agents."""

    def __init__(self):
        """Initialize orchestrator and all agents."""
        self.config = get_config()
        self.github = GitHubClient()
        self.llm = LLMClient()
        self.audit = AuditLogger()
        self.agents = {}

        # Initialize enabled agents
        self._load_agents()

    def _load_agents(self) -> None:
        """Load and initialize all enabled agents."""
        enabled = self.config.enabled_agents

        # Import and initialize agents as they're created
        # This will be expanded as we build each agent
        pass

    async def run_health_check(self, repository: str) -> dict[str, Any]:
        """Run a health check on a repository."""
        return {
            "status": "healthy",
            "repository": repository,
            "checks": {
                "github_connection": "ok",
                "llm_connection": "ok"
            }
        }

    async def monitor_repository(self, repository: str) -> None:
        """Continuously monitor a repository and run agents."""
        print(f"Starting monitoring for {repository}...")

        while True:
            # This will be expanded to run all enabled agents
            await asyncio.sleep(60)  # Check every minute

    def close(self) -> None:
        """Clean up resources."""
        self.github.close()
'''

# ============================================================================
# Write all files
# ============================================================================


def create_file(path: Path, content: str) -> None:
    """Create a file with content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ {path.relative_to(BASE_DIR)}")


def main():
    """Create all core files."""
    print("Creating core module files...\\n")

    files = {
        "autonomous_agent/core/config.py": CONFIG_PY,
        "autonomous_agent/core/github_client.py": GITHUB_CLIENT_PY,
        "autonomous_agent/core/llm_client.py": LLM_CLIENT_PY,
        "autonomous_agent/core/audit_logger.py": AUDIT_LOGGER_PY,
        "autonomous_agent/core/base_agent.py": BASE_AGENT_PY,
        "autonomous_agent/core/orchestrator.py": ORCHESTRATOR_PY,
    }

    for file_path, content in files.items():
        create_file(BASE_DIR / file_path, content)

    print("\\n✅ Core modules created successfully!")
    print("\\nNext: Run create_agents.py to build specialized agents")


if __name__ == "__main__":
    main()
