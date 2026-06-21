"""Configuration management for the autonomous agent system."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitHubSettings(BaseSettings):
    """GitHub API configuration."""

    token: str = Field(..., description="GitHub Personal Access Token")
    api_url: str = Field(
        default="https://api.github.com", description="GitHub API base URL"
    )
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
            "documentation_generator",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
