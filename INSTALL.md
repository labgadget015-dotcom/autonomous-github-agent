# Autonomous GitHub Agent - Complete Setup Guide

## 🚀 Quick Start (3 Steps)

This repository contains a complete autonomous GitHub agent framework with 7 specialized AI agents.

### Step 1: Create Directory Structure & Files

Run these Python scripts in order:

```bash
cd C:\Users\aw789\autonomous-github-agent

# 1. Create directories and initial files
python quick_setup.py

# 2. Create core modules (GitHub client, LLM client, config, etc.)
python create_core_files.py

# 3. Create all 7 specialized agents
python create_agents.py

# 4. Create CLI interface and tests
python create_cli.py
```

### Step 2: Install Dependencies

```bash
# Install the package in development mode
pip install -e .

# Or install specific dependencies
pip install -r requirements.txt
```

### Step 3: Configure

```bash
# Copy environment template
copy .env.example .env

# Edit .env and add your tokens:
# - GITHUB_TOKEN=ghp_your_token_here
# - OPENAI_API_KEY=sk-your_key_here (or Anthropic)
```

## ✅ Verify Installation

```bash
# Check configuration
autonomous-agent config-check

# List available agents
autonomous-agent list-agents

# Run health check on a repository
autonomous-agent health-check --repo owner/repo-name
```

## 📚 Usage Examples

### Analyze Repository Health
```bash
autonomous-agent analyze --repo owner/repo
autonomous-agent analyze --repo owner/repo --agent health
autonomous-agent analyze --repo owner/repo --agent security
```

### Review Pull Requests
```bash
# Review all open PRs
autonomous-agent review --repo owner/repo

# Review specific PR
autonomous-agent review --repo owner/repo --pr 123
```

### Continuous Monitoring
```bash
autonomous-agent monitor --repo owner/repo
```

### View Audit Logs
```bash
autonomous-agent logs
autonomous-agent logs --repo owner/repo --limit 50
```

## 🤖 Available Agents

1. **Health Monitor** - Repository health assessment and metrics tracking
2. **Code Reviewer** - Automated PR reviews with security and quality checks
3. **Issue Manager** - Auto-triage, label, and manage issues
4. **Branch Manager** - Automated branch cleanup and operations
5. **Security Scanner** - Secret detection and vulnerability scanning
6. **Workflow Optimizer** - CI/CD workflow analysis and optimization
7. **Documentation Generator** - Automated documentation updates

## 📖 Project Structure

```
autonomous-github-agent/
├── autonomous_agent/          # Main package
│   ├── core/                  # Core components
│   │   ├── config.py         # Configuration management
│   │   ├── github_client.py  # GitHub API wrapper
│   │   ├── llm_client.py     # LLM integration
│   │   ├── audit_logger.py   # Audit logging
│   │   ├── base_agent.py     # Base agent class
│   │   └── orchestrator.py   # Main orchestrator
│   ├── agents/               # Specialized agents
│   │   ├── health_monitor.py
│   │   ├── code_reviewer.py
│   │   ├── issue_manager.py
│   │   ├── branch_manager.py
│   │   ├── security_scanner.py
│   │   ├── workflow_optimizer.py
│   │   └── documentation_generator.py
│   └── cli.py                # CLI interface
├── tests/                    # Test suite
├── docs/                     # Documentation
├── config/                   # Configuration files
└── workflows/                # GitHub Actions templates
```

## 🔧 Configuration Options

Edit `.env` or set environment variables:

```bash
# Required
GITHUB_TOKEN=ghp_your_token_here

# LLM Provider (choose one)
LLM_PROVIDER=openai           # or 'anthropic' or 'local'
OPENAI_API_KEY=sk-...         # if using OpenAI
ANTHROPIC_API_KEY=sk-ant-...  # if using Anthropic

# Automation Level
AUTOMATION_LEVEL=semi-auto    # manual, semi-auto, or full-auto

# Optional
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./autonomous_agent.db
```

## 🛡️ Safety Features

- **Human-in-the-loop**: Destructive actions require approval
- **Audit logging**: All actions logged with rollback instructions
- **Configurable automation**: Choose your comfort level
- **Rate limiting**: Prevents API abuse

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=autonomous_agent

# Format code
black .
ruff check .

# Type checking
mypy .
```

## 📝 Next Steps

1. ✅ Set up the framework (run setup scripts above)
2. ✅ Configure your tokens in `.env`
3. ✅ Test with `autonomous-agent config-check`
4. ✅ Try it on a test repository
5. 🚀 Deploy to production with GitHub Actions
6. 📊 Monitor with `autonomous-agent logs`

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🆘 Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'autonomous_agent'`
**Solution**: Run `pip install -e .` from the project root

**Issue**: `GitHub token not configured`
**Solution**: Set `GITHUB_TOKEN` in `.env` file

**Issue**: `LLM API key missing`
**Solution**: Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env`

## 📞 Support

For issues and questions:
- Check documentation in `docs/`
- Review audit logs: `autonomous-agent logs`
- Open an issue on GitHub

---

Built with ❤️ using Python, PyGithub, and modern LLMs
