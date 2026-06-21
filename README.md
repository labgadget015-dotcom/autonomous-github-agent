# Autonomous GitHub Agent 🤖

![CI](https://github.com/labgadget015-dotcom/autonomous-github-agent/workflows/code-quality-optimized.yml/badge.svg) ![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue) ![License](https://img.shields.io/badge/license-MIT-blue.svg) [![Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-Autonomous%20Agent-purple?logo=github)](https://github.com/marketplace/actions/autonomous-github-agent)

A state-of-the-art, autonomous AI system for end-to-end GitHub repository and project management. Deploy specialized micro-agents to handle code reviews, issue management, CI/CD, security scanning, and documentation—all with minimal human intervention.

## 🌟 Key Features

- **Multi-Agent Architecture**: 7 specialized agents working in concert
- **Intelligent Code Review**: Automated PR reviews with security, quality, and performance checks
- **Issue Management**: Auto-triage, label, assign, and link related issues
- **Branch Operations**: Automated merge, rebase, conflict resolution
- **Security First**: Dependency scanning, secret detection, OWASP compliance
- **CI/CD Optimization**: Workflow analysis and auto-healing
- **Documentation Generation**: Always up-to-date README, API docs, changelogs
- **Audit Logging**: Full traceability with rollback support

## ⚡ Use as a GitHub Action

Add autonomous AI code review, issue triage, and security scanning to any repository in seconds:

```yaml
# .github/workflows/agent.yml
name: Autonomous Agent
on: [push, pull_request, issues]

jobs:
  agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: labgadget015-dotcom/autonomous-github-agent@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          analysis_mode: auto
          local_llm_enabled: "true"    # route simple tasks to Ollama at $0
          severity_threshold: high
```

| Input | Default | Description |
|-------|---------|-------------|
| `github_token` | — | **Required.** GitHub token for API access |
| `anthropic_api_key` | — | Anthropic API key (recommended) |
| `openai_api_key` | — | OpenAI API key (alternative) |
| `analysis_mode` | `auto` | `parallel` / `sequential` / `auto` |
| `local_llm_enabled` | `true` | Route low-complexity tasks to local Ollama at zero cost |
| `local_llm_endpoint` | `http://localhost:11434` | Local LLM base URL |
| `complexity_threshold` | `medium` | LLM routing cutoff: `low` / `medium` / `high` |
| `issue_creation_enabled` | `true` | Auto-open GitHub issues for critical findings |
| `severity_threshold` | `high` | Minimum severity to trigger issue creation |

**Outputs:** `analysis_summary` · `issues_created` · `cost_savings` · `execution_time`

---

## 📊 Track Your Repo Health

Embed a live GadgetLab score badge in your README — updates every 5 minutes:

```markdown
[![GadgetLab Score](https://img.shields.io/endpoint?url=https://gadgetlab.uk/api/badge/YOUR_ORG/YOUR_REPO)](https://gadgetlab.uk)
```

Replace `YOUR_ORG/YOUR_REPO` with your GitHub repo path. The score reflects CI status, open issue count, and commit recency.

---

## 🚀 Quick Start

```bash
# Install
pip install -e .

# Configure
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your GitHub token and preferences

# Run health check on a repository
python -m autonomous_agent health-check --repo owner/repo-name

# Start autonomous monitoring
python -m autonomous_agent monitor --repo owner/repo-name
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Orchestrator (Central Brain)        │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┐
       │   Event Bus   │
       └───────┬───────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌──────────┐
│ Health │ │ Code   │ │ Security │
│Monitor │ │Reviewer│ │ Scanner  │
└────────┘ └────────┘ └──────────┘
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌──────────┐
│ Issue  │ │ Branch │ │Workflow  │
│Manager │ │Manager │ │Optimizer │
└────────┘ └────────┘ └──────────┘
               │
               ▼
         ┌──────────┐
         │   Docs   │
         │Generator │
         └──────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.11+
- GitHub Personal Access Token with repo, workflow, and admin permissions
- Optional: OpenAI/Anthropic API key for enhanced AI features

### From Source
```bash
git clone https://github.com/yourusername/autonomous-github-agent.git
cd autonomous-github-agent
pip install -e .
```

## 🔧 Configuration

Create `config/config.yaml`:

```yaml
github:
  token: ${GITHUB_TOKEN}

llm:
  provider: openai  # openai, anthropic, or local
  api_key: ${OPENAI_API_KEY}
  model: gpt-4

agents:
  enabled:
    - health_monitor
    - code_reviewer
    - issue_manager
    - branch_manager
    - security_scanner
    - workflow_optimizer
    - documentation_generator

automation_level: semi-auto  # manual, semi-auto, or full-auto

safety:
  require_approval_for:
    - branch_deletion
    - force_push
    - workflow_modification
  audit_log_retention_days: 90
```

## 🤖 Available Agents

| Agent | Purpose | Key Actions |
|-------|---------|-------------|
| **Health Monitor** | Repository health assessment | Metrics tracking, debt identification, cleanup recommendations |
| **Code Reviewer** | Automated PR reviews | Quality checks, security scans, inline suggestions, auto-merge |
| **Issue Manager** | Issue triage & organization | Auto-label, assign, link, close resolved issues |
| **Branch Manager** | Branch operations | Merge, rebase, conflict resolution, cleanup |
| **Security Scanner** | Security & compliance | Dependency scanning, secret detection, OWASP checks |
| **Workflow Optimizer** | CI/CD management | Workflow analysis, failure recovery, optimization |
| **Documentation Generator** | Documentation updates | README, API docs, changelogs, release notes |

## 📖 Documentation

- [Architecture Overview](docs/architecture.md)
- [Agent Reference](docs/agents.md)
- [Configuration Guide](docs/configuration.md)
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)

## 🛡️ Safety & Governance

- **Human-in-the-Loop**: Destructive operations require explicit approval
- **Audit Logging**: Every action is logged with rollback instructions
- **Configurable Automation**: Choose your comfort level (manual → full-auto)
- **Rate Limiting**: Protects against API abuse and cost overruns

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=autonomous_agent

# Lint
ruff check .
black .
mypy .
```

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with [PyGithub](https://github.com/PyGithub/PyGithub), modern LLMs, and a passion for automation.
