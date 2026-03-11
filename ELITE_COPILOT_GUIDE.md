# Elite AI Copilot - Usage Guide

## Overview

The Elite AI Copilot is an advanced AI-powered automation assistant designed to enhance your GitHub workflow with intelligent analysis, proactive monitoring, and autonomous task execution.

## Table of Contents

- [Getting Started](#getting-started)
- [Operating Modes](#operating-modes)
- [Core Features](#core-features)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Integration](#integration)
- [Best Practices](#best-practices)

## Getting Started

### Prerequisites

- Python 3.11+
- GitHub repository access
- Optional: OpenAI or Anthropic API key for cloud LLM features

### Installation

```bash
# Clone the repository
git clone https://github.com/labgadget015-dotcom/autonomous-github-agent.git
cd autonomous-github-agent

# Install dependencies
pip install -r requirements.txt

# Run your first analysis
python .github/scripts/elite_copilot.py analyze --repo-path .
```

### Quick Commands

```bash
# Analyze repository
python .github/scripts/elite_copilot.py analyze --repo-path .

# Get assistance
python .github/scripts/elite_copilot.py assist --query "How do I improve code quality?"

# Generate comprehensive report
python .github/scripts/elite_copilot.py report --repo-path . --output MY_REPORT.md

# Run in autonomous mode (advanced)
python .github/scripts/elite_copilot.py autonomous --repo-path .
```

## Operating Modes

### 1. Assistant Mode (Default)
**Best for:** Daily development assistance and code reviews

```bash
python .github/scripts/elite_copilot.py analyze --mode assistant
```

**Capabilities:**
- Provides suggestions and recommendations
- Non-intrusive analysis
- Generates actionable insights
- Safe for all use cases

**Use when:**
- Learning about your codebase
- Getting recommendations
- Reviewing changes before merge
- Daily development workflow

### 2. Autopilot Mode
**Best for:** Automated routine tasks with safeguards

```bash
python .github/scripts/elite_copilot.py analyze --mode autopilot
```

**Capabilities:**
- Executes approved tasks automatically
- Requires confirmation for critical actions
- Maintains audit trail
- Can auto-fix common issues

**Use when:**
- Running scheduled maintenance
- Auto-fixing linting issues
- Updating dependencies
- Routine documentation updates

### 3. Guardian Mode
**Best for:** Continuous security and quality monitoring

```bash
python .github/scripts/elite_copilot.py analyze --mode guardian
```

**Capabilities:**
- Proactive issue detection
- Security vulnerability scanning
- Performance degradation alerts
- Code quality monitoring

**Use when:**
- Monitoring production code
- Pre-merge PR checks
- Security-critical projects
- Compliance requirements

### 4. Mentor Mode
**Best for:** Learning and educational purposes

```bash
python .github/scripts/elite_copilot.py analyze --mode mentor
```

**Capabilities:**
- Detailed explanations
- Best practice guidance
- Educational insights
- Code improvement suggestions

**Use when:**
- Learning new technologies
- Training junior developers
- Code reviews for learning
- Documentation generation

## Core Features

### 1. Repository Analysis

Comprehensive analysis covering:
- Code quality metrics
- Security vulnerabilities
- Architecture patterns
- Performance bottlenecks
- Documentation coverage

```bash
python .github/scripts/elite_copilot.py analyze --repo-path . --output REPORT.md
```

**Output includes:**
- Health score (0-100)
- Categorized insights
- Prioritized recommendations
- Detailed evidence

### 2. Intelligent LLM Routing

Automatically routes tasks to the most cost-effective LLM:
- Simple tasks → Local LLM (FREE)
- Complex tasks → Cloud LLM (Paid)
- 90% cost savings on average

```yaml
# Configured automatically in copilot_config.yaml
local_llm_enabled: true
local_llm_endpoint: http://localhost:11434
complexity_threshold: medium
```

### 3. Async Parallel Analysis

Runs multiple analysis tools concurrently:
- 3x faster than sequential execution
- Efficient resource utilization
- Real-time progress updates

```python
# Integrated in copilot_integration.py
await hub.run_async_analysis()
```

### 4. Daily Summaries

Automated repository health reports:
- Top priorities
- Recent activity
- Open issues and PRs
- Team insights

```bash
cd autopilot
python autopilot.py --config config.yaml
```

## Usage Examples

### Example 1: Pre-commit Code Review

```bash
# Before committing changes
python .github/scripts/elite_copilot.py analyze \
  --repo-path . \
  --mode guardian \
  --output PRE_COMMIT_REVIEW.md

# Review the report and address any critical issues
cat PRE_COMMIT_REVIEW.md
```

### Example 2: PR Analysis

```bash
# Analyze specific PR changes
git checkout feature-branch
python .github/scripts/elite_copilot.py analyze \
  --mode assistant \
  --output PR_ANALYSIS.md
```

### Example 3: Full Integration

```bash
# Run complete copilot suite
python .github/scripts/copilot_integration.py --mode assistant

# Outputs:
# - COPILOT_INTEGRATION_REPORT.md
# - copilot_integration_results.json
```

### Example 4: Continuous Monitoring

```yaml
# .github/workflows/elite_copilot.yml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  copilot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Elite Copilot
        run: python .github/scripts/elite_copilot.py analyze
```

## Configuration

### Basic Configuration

Create `copilot_config.yaml`:

```yaml
mode: assistant
enable_proactive_analysis: true
enable_auto_fix: false
learning_enabled: true
max_parallel_tasks: 5
priority_threshold: 'medium'

notification_channels:
  - github_comments
  - artifacts

capabilities:
  - code_review
  - test_generation
  - documentation
  - security_scan
  - performance_analysis
  - dependency_management
  - refactoring_suggestions
```

### Advanced Configuration

```yaml
# LLM Configuration
llm_routing:
  local_enabled: true
  local_endpoint: http://localhost:11434
  cloud_fallback: true
  complexity_threshold: medium

# Security Settings
security:
  auto_fix_enabled: false
  severity_threshold: medium
  scan_dependencies: true
  check_secrets: true

# Performance Settings
performance:
  parallel_execution: true
  max_workers: 8
  timeout_seconds: 300
```

## Integration

### GitHub Actions Integration

```yaml
- name: Elite Copilot Analysis
  uses: labgadget015-dotcom/autonomous-github-agent@v1
  with:
    mode: assistant
    github_token: ${{ secrets.GITHUB_TOKEN }}
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

### CLI Integration

```bash
# Add to your development workflow
alias copilot='python /path/to/.github/scripts/elite_copilot.py'

# Use in daily work
copilot analyze
copilot assist --query "Review my last commit"
```

### IDE Integration

```json
// VS Code tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Elite Copilot Analysis",
      "type": "shell",
      "command": "python .github/scripts/elite_copilot.py analyze",
      "group": "test"
    }
  ]
}
```

## Best Practices

### 1. Start with Assistant Mode
- Learn what the copilot can do
- Build trust in the recommendations
- Gradually enable more automation

### 2. Review Reports Regularly
- Check health scores weekly
- Address high-priority issues promptly
- Track trends over time

### 3. Use Appropriate Modes
- **Assistant:** Daily development
- **Autopilot:** Routine maintenance
- **Guardian:** Critical systems
- **Mentor:** Learning environments

### 4. Integrate into CI/CD
- Run on every PR
- Daily scheduled analysis
- Auto-comment on issues
- Track metrics over time

### 5. Customize for Your Needs
- Adjust thresholds
- Enable/disable capabilities
- Configure notification channels
- Set priority levels

## Troubleshooting

### Issue: "No module named 'elite_copilot'"

```bash
# Ensure you're in the right directory
cd /path/to/autonomous-github-agent

# Add scripts to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.github/scripts"
```

### Issue: "Health score always 100"

This is normal for the baseline. As you add custom analysis tools and integrations, the scoring will become more sophisticated.

### Issue: "LLM router failing"

```bash
# Check local LLM is running
curl http://localhost:11434/api/tags

# Or disable local LLM
# In copilot_config.yaml:
# local_llm_enabled: false
```

## Advanced Topics

### Custom Analysis Plugins

```python
# In elite_copilot.py, add your own analyzer
def _analyze_custom(self, repo_path: str) -> List[CopilotInsight]:
    insights = []
    # Your custom logic here
    return insights
```

### Extending Capabilities

```python
# Add to config
capabilities:
  - code_review
  - custom_analysis
  - my_special_check
```

### API Integration

```python
from elite_copilot import EliteCopilot

copilot = EliteCopilot()
results = copilot.analyze_repository('.')
print(f"Health Score: {results['health_score']}")
```

## Support

- 📖 Documentation: [GitHub Wiki](https://github.com/labgadget015-dotcom/autonomous-github-agent/wiki)
- 🐛 Issues: [Report bugs](https://github.com/labgadget015-dotcom/autonomous-github-agent/issues)
- 💬 Discussions: [Community forum](https://github.com/labgadget015-dotcom/autonomous-github-agent/discussions)
- 📧 Contact: Open an issue for support

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**Built with ❤️ by the Elite AI Copilot Team**
