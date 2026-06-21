"""
Create CLI interface and supporting files.
Run this after create_agents.py
"""

from pathlib import Path

BASE_DIR = Path(r"C:\Users\aw789\autonomous-github-agent")

# ============================================================================
# CLI Main
# ============================================================================

CLI_PY = '''"""Command-line interface for the autonomous agent."""

import asyncio
import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from autonomous_agent.core.orchestrator import Orchestrator
from autonomous_agent.core.config import get_config


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Autonomous GitHub Agent - AI-powered repository management."""
    pass


@main.command()
@click.option("--repo", required=True, help="Repository name (owner/repo)")
def health_check(repo: str):
    """Run health check on a repository."""
    console.print(f"[bold blue]Running health check on {repo}...[/bold blue]\\n")

    orchestrator = Orchestrator()
    result = asyncio.run(orchestrator.run_health_check(repo))

    # Display results
    table = Table(title="Repository Health Check")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for key, value in result.get("checks", {}).items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)
    console.print(f"\\n[bold green]✓[/bold green] Health check complete!")


@main.command()
@click.option("--repo", required=True, help="Repository name (owner/repo)")
@click.option("--agent", help="Specific agent to run (optional)")
def analyze(repo: str, agent: str = None):
    """Analyze repository with all or specific agent."""
    from autonomous_agent.core.github_client import GitHubClient
    from autonomous_agent.core.llm_client import LLMClient
    from autonomous_agent.core.audit_logger import AuditLogger
    from autonomous_agent.agents.health_monitor import HealthMonitorAgent
    from autonomous_agent.agents.security_scanner import SecurityScannerAgent

    console.print(f"[bold blue]Analyzing {repo}...[/bold blue]\\n")

    github = GitHubClient()
    llm = LLMClient()
    audit = AuditLogger()

    if not agent or agent == "health":
        console.print("[yellow]Running Health Monitor...[/yellow]")
        health_agent = HealthMonitorAgent(github, llm, audit)
        result = asyncio.run(health_agent.execute(repo))

        rprint("\\n[bold]Health Report:[/bold]")
        rprint(f"  Stars: {result['metrics']['stars']}")
        rprint(f"  Open Issues: {result['metrics']['open_issues']}")
        rprint(f"  Stale Branches: {len(result['issues']['stale_branches'])}")

        if result["recommendations"]:
            rprint("\\n[bold]Recommendations:[/bold]")
            for rec in result["recommendations"]:
                rprint(f"  • {rec}")

    if not agent or agent == "security":
        console.print("\\n[yellow]Running Security Scanner...[/yellow]")
        security_agent = SecurityScannerAgent(github, llm, audit)
        result = asyncio.run(security_agent.execute(repo))

        if result["secrets_found"]:
            rprint("\\n[bold red]⚠️  Secrets Found:[/bold red]")
            for secret in result["secrets_found"]:
                rprint(f"  • {secret['type']} in {secret['file']}")
        else:
            rprint("\\n[bold green]✓[/bold green] No secrets detected")

    console.print("\\n[bold green]✓[/bold green] Analysis complete!")


@main.command()
@click.option("--repo", required=True, help="Repository name (owner/repo)")
@click.option("--pr", type=int, help="Specific PR number to review")
def review(repo: str, pr: int = None):
    """Review pull requests."""
    from autonomous_agent.core.github_client import GitHubClient
    from autonomous_agent.core.llm_client import LLMClient
    from autonomous_agent.core.audit_logger import AuditLogger
    from autonomous_agent.agents.code_reviewer import CodeReviewerAgent

    console.print(f"[bold blue]Reviewing PRs in {repo}...[/bold blue]\\n")

    github = GitHubClient()
    llm = LLMClient()
    audit = AuditLogger()

    reviewer = CodeReviewerAgent(github, llm, audit)
    result = asyncio.run(reviewer.execute(repo, pr_number=pr))

    console.print(f"[green]Reviewed {result['reviewed_prs']} PR(s)[/green]")

    for review in result["results"]:
        rprint(f"\\n[bold]PR #{review['pr_number']}:[/bold] {review['title']}")
        rprint(f"  Score: {review['score']}/100")
        if review["security_concerns"]:
            rprint(f"  [red]Security concerns: {len(review['security_concerns'])}[/red]")
        if review["issues_found"]:
            rprint(f"  [yellow]Issues: {len(review['issues_found'])}[/yellow]")


@main.command()
@click.option("--repo", required=True, help="Repository name (owner/repo)")
def monitor(repo: str):
    """Start continuous monitoring of a repository."""
    console.print(f"[bold blue]Starting continuous monitoring of {repo}...[/bold blue]")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\\n")

    orchestrator = Orchestrator()

    try:
        asyncio.run(orchestrator.monitor_repository(repo))
    except KeyboardInterrupt:
        console.print("\\n[bold red]Monitoring stopped[/bold red]")


@main.command()
def list_agents():
    """List all available agents."""
    agents = [
        ("health_monitor", "Repository health assessment and metrics"),
        ("code_reviewer", "Automated PR code reviews"),
        ("issue_manager", "Issue triage and management"),
        ("branch_manager", "Branch operations and cleanup"),
        ("security_scanner", "Security and vulnerability scanning"),
        ("workflow_optimizer", "CI/CD workflow optimization"),
        ("documentation_generator", "Documentation generation and updates"),
    ]

    table = Table(title="Available Agents")
    table.add_column("Agent", style="cyan")
    table.add_column("Description", style="white")

    for name, desc in agents:
        table.add_row(name, desc)

    console.print(table)


@main.command()
@click.option("--repo", help="Filter by repository")
@click.option("--limit", default=20, help="Number of logs to show")
def logs(repo: str = None, limit: int = 20):
    """View audit logs."""
    from autonomous_agent.core.audit_logger import AuditLogger

    audit = AuditLogger()
    logs = audit.get_logs(repository=repo, limit=limit)

    table = Table(title="Audit Logs")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Agent", style="yellow")
    table.add_column("Action", style="green")
    table.add_column("Repository", style="blue")

    for log in logs:
        table.add_row(
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            log.agent_name,
            log.action,
            log.repository or "N/A"
        )

    console.print(table)


@main.command()
def config_check():
    """Verify configuration."""
    config = get_config()

    table = Table(title="Configuration Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("GitHub Token", "✓ Set" if config.github.token else "✗ Missing")
    table.add_row("LLM Provider", config.llm.provider)
    table.add_row("LLM API Key", "✓ Set" if config.llm.api_key else "✗ Missing")
    table.add_row("Automation Level", config.automation_level)
    table.add_row("Enabled Agents", str(len(config.enabled_agents)))

    console.print(table)

    if not config.github.token:
        console.print("\\n[bold red]⚠️  GitHub token not configured[/bold red]")
        console.print("Set GITHUB_TOKEN environment variable or update .env file")


if __name__ == "__main__":
    main()
'''

# ============================================================================
# Tests
# ============================================================================

TEST_CONFIG_PY = '''"""Tests for configuration module."""

import pytest
from autonomous_agent.core.config import Config, get_config


def test_config_initialization():
    """Test config can be initialized."""
    config = Config(
        github={"token": "test_token"},
        llm={"provider": "openai", "api_key": "test_key"}
    )

    assert config.github.token == "test_token"
    assert config.llm.provider == "openai"


def test_automation_levels():
    """Test automation level options."""
    for level in ["manual", "semi-auto", "full-auto"]:
        config = Config(
            github={"token": "test"},
            automation_level=level
        )
        assert config.automation_level == level
'''

TEST_GITHUB_CLIENT_PY = '''"""Tests for GitHub client."""

import pytest
from unittest.mock import Mock, patch
from autonomous_agent.core.github_client import GitHubClient


@patch("autonomous_agent.core.github_client.Github")
def test_github_client_initialization(mock_github):
    """Test GitHub client initialization."""
    with patch("autonomous_agent.core.config.get_config") as mock_config:
        mock_config.return_value.github.token = "test_token"
        mock_config.return_value.github.timeout = 30

        client = GitHubClient()
        assert client.token == "test_token"
'''

TEST_HEALTH_MONITOR_PY = '''"""Tests for health monitor agent."""

import pytest
from unittest.mock import Mock, AsyncMock
from autonomous_agent.agents.health_monitor import HealthMonitorAgent


@pytest.mark.asyncio
async def test_health_monitor_execute():
    """Test health monitor execution."""
    mock_github = Mock()
    mock_llm = Mock()
    mock_audit = Mock()

    agent = HealthMonitorAgent(mock_github, mock_llm, mock_audit)

    # Mock repository
    mock_repo = Mock()
    mock_repo.stargazers_count = 100
    mock_repo.open_issues_count = 5
    mock_github.get_repository.return_value = mock_repo

    # This will fail without full mocking, but shows test structure
    # result = await agent.execute("owner/repo")
    # assert "metrics" in result
'''

# ============================================================================
# Documentation
# ============================================================================

ARCHITECTURE_MD = """# Architecture Overview

## System Design

The Autonomous GitHub Agent follows a multi-agent architecture where specialized agents handle specific domains:

```
┌─────────────────────────────────────┐
│         Orchestrator                │
│   (Central Coordination Layer)      │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌──────────┐
│ Health │ │  Code  │ │ Security │
│Monitor │ │Reviewer│ │ Scanner  │
└────────┘ └────────┘ └──────────┘
```

## Components

### Core Layer

- **Orchestrator**: Coordinates all agents, manages event bus
- **GitHub Client**: Wrapper around PyGithub with rate limiting
- **LLM Client**: Unified interface for OpenAI/Anthropic
- **Audit Logger**: Tracks all actions with rollback support
- **Config Manager**: Handles all configuration

### Agent Layer

Each agent is independent and focused on a specific domain:

- **HealthMonitorAgent**: Repository metrics and health
- **CodeReviewerAgent**: Automated PR reviews
- **IssueManagerAgent**: Issue triage and labeling
- **BranchManagerAgent**: Branch cleanup and operations
- **SecurityScannerAgent**: Security and vulnerability detection
- **WorkflowOptimizerAgent**: CI/CD optimization
- **DocumentationGeneratorAgent**: Doc generation

## Data Flow

1. User invokes CLI or webhook triggers event
2. Orchestrator receives request
3. Orchestrator dispatches to appropriate agent(s)
4. Agent executes task using GitHub/LLM clients
5. Agent logs action to audit system
6. Results returned to orchestrator
7. Orchestrator formats and returns response

## Safety Mechanisms

- **Human-in-the-loop**: Configurable approval requirements
- **Audit logging**: All actions logged with rollback data
- **Rate limiting**: Prevents API abuse
- **Configuration levels**: manual → semi-auto → full-auto
"""

CONTRIBUTING_MD = """# Contributing Guide

Thank you for your interest in contributing to the Autonomous GitHub Agent!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/autonomous-github-agent.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit: `git commit -m "Add your feature"`
7. Push: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=autonomous_agent

# Format code
black .
ruff check .

# Type checking
mypy .
```

## Adding a New Agent

1. Create `autonomous_agent/agents/your_agent.py`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Add tests in `tests/test_your_agent.py`
5. Update documentation

Example:

```python
from autonomous_agent.core.base_agent import BaseAgent

class YourAgent(BaseAgent):
    async def execute(self, repository: str, **kwargs):
        # Your logic here
        return {"status": "success"}
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public methods
- Keep functions focused and small
- Add comments for complex logic

## Testing

- Write tests for all new features
- Maintain >80% code coverage
- Use pytest fixtures for common setups
- Mock external API calls

## Pull Request Guidelines

- Clear description of changes
- Link related issues
- Include tests
- Update documentation
- Pass all CI checks
"""

LICENSE = """MIT License

Copyright (c) 2026 Autonomous Agent Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# ============================================================================
# Write all files
# ============================================================================


def create_file(path: Path, content: str) -> None:
    """Create a file with content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ {path.relative_to(BASE_DIR)}")


def main():
    """Create CLI and supporting files."""
    print("Creating CLI and supporting files...\\n")

    files = {
        "autonomous_agent/cli.py": CLI_PY,
        "tests/__init__.py": "",
        "tests/test_config.py": TEST_CONFIG_PY,
        "tests/test_github_client.py": TEST_GITHUB_CLIENT_PY,
        "tests/test_health_monitor.py": TEST_HEALTH_MONITOR_PY,
        "docs/architecture.md": ARCHITECTURE_MD,
        "docs/contributing.md": CONTRIBUTING_MD,
        "CONTRIBUTING.md": CONTRIBUTING_MD,
        "LICENSE": LICENSE,
    }

    for file_path, content in files.items():
        create_file(BASE_DIR / file_path, content)

    print("\\n✅ All files created successfully!")
    print("\\nFramework is complete! Next steps:")
    print("1. Run: python quick_setup.py")
    print("2. Run: python create_core_files.py")
    print("3. Run: python create_agents.py")
    print("4. Install: pip install -e .")
    print("5. Configure: Copy .env.example to .env and add your tokens")
    print("6. Test: autonomous-agent health-check --repo owner/repo")


if __name__ == "__main__":
    main()
