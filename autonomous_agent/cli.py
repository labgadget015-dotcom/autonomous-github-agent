"""Command-line interface for the autonomous agent."""

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
    console.print(f"[bold blue]Running health check on {repo}...[/bold blue]\n")
    
    orchestrator = Orchestrator()
    result = asyncio.run(orchestrator.run_health_check(repo))
    
    # Display results
    table = Table(title="Repository Health Check")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in result.get("checks", {}).items():
        table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(table)
    console.print(f"\n[bold green]✓[/bold green] Health check complete!")


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
    
    console.print(f"[bold blue]Analyzing {repo}...[/bold blue]\n")
    
    github = GitHubClient()
    llm = LLMClient()
    audit = AuditLogger()
    
    if not agent or agent == "health":
        console.print("[yellow]Running Health Monitor...[/yellow]")
        health_agent = HealthMonitorAgent(github, llm, audit)
        result = asyncio.run(health_agent.execute(repo))
        
        rprint("\n[bold]Health Report:[/bold]")
        rprint(f"  Stars: {result['metrics']['stars']}")
        rprint(f"  Open Issues: {result['metrics']['open_issues']}")
        rprint(f"  Stale Branches: {len(result['issues']['stale_branches'])}")
        
        if result["recommendations"]:
            rprint("\n[bold]Recommendations:[/bold]")
            for rec in result["recommendations"]:
                rprint(f"  • {rec}")
    
    if not agent or agent == "security":
        console.print("\n[yellow]Running Security Scanner...[/yellow]")
        security_agent = SecurityScannerAgent(github, llm, audit)
        result = asyncio.run(security_agent.execute(repo))
        
        if result["secrets_found"]:
            rprint("\n[bold red]⚠️  Secrets Found:[/bold red]")
            for secret in result["secrets_found"]:
                rprint(f"  • {secret['type']} in {secret['file']}")
        else:
            rprint("\n[bold green]✓[/bold green] No secrets detected")
    
    console.print("\n[bold green]✓[/bold green] Analysis complete!")


@main.command()
@click.option("--repo", required=True, help="Repository name (owner/repo)")
@click.option("--pr", type=int, help="Specific PR number to review")
def review(repo: str, pr: int = None):
    """Review pull requests."""
    from autonomous_agent.core.github_client import GitHubClient
    from autonomous_agent.core.llm_client import LLMClient
    from autonomous_agent.core.audit_logger import AuditLogger
    from autonomous_agent.agents.code_reviewer import CodeReviewerAgent
    
    console.print(f"[bold blue]Reviewing PRs in {repo}...[/bold blue]\n")
    
    github = GitHubClient()
    llm = LLMClient()
    audit = AuditLogger()
    
    reviewer = CodeReviewerAgent(github, llm, audit)
    result = asyncio.run(reviewer.execute(repo, pr_number=pr))
    
    console.print(f"[green]Reviewed {result['reviewed_prs']} PR(s)[/green]")
    
    for review in result["results"]:
        rprint(f"\n[bold]PR #{review['pr_number']}:[/bold] {review['title']}")
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
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")
    
    orchestrator = Orchestrator()
    
    try:
        asyncio.run(orchestrator.monitor_repository(repo))
    except KeyboardInterrupt:
        console.print("\n[bold red]Monitoring stopped[/bold red]")


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
        console.print("\n[bold red]⚠️  GitHub token not configured[/bold red]")
        console.print("Set GITHUB_TOKEN environment variable or update .env file")


if __name__ == "__main__":
    main()
