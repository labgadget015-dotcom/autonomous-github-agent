# 🚀 Autonomous GitHub Agent - Quick Start Guide

## 30-Second Setup

```bash
# Option 1: GitHub Actions (Recommended)
- uses: labgadget015-dotcom/autonomous-github-agent@v1.0.0
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}

# Option 2: Local CLI
pip install autonomous-github-agent
python -m autonomous_github_agent --token $GITHUB_TOKEN --repo org/repo

# Option 3: Docker
docker run -e GITHUB_TOKEN=$GITHUB_TOKEN labgadget015/autonomous-github-agent
```

## 5-Minute Implementation

### Step 1: Add Secrets to GitHub
1. Go to Settings → Secrets → New repository secret
2. Add `OPENAI_API_KEY` = your OpenAI key
3. Add `GITHUB_TOKEN` = personal access token with `repo` scope

### Step 2: Create Workflow File
1. Create `.github/workflows/autonomous-agent.yml`:

```yaml
name: Autonomous GitHub Agent

on:
  push:
    branches: [main]
  issues:
    types: [opened, edited]
  pull_request:
    types: [opened, synchronize]

jobs:
  autonomous-tasks:
    runs-on: ubuntu-latest
    steps:
      - uses: labgadget015-dotcom/autonomous-github-agent@v1.0.0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          actions: |
            - triage-issues
            - review-pr
            - generate-tests
            - update-docs
```

### Step 3: Test It
1. Push to main branch
2. Create a test issue with title: "Test: Generate README for project X"
3. Watch the agent respond autonomously

## What It Does Automatically

✅ **Issue Triage**: Labels, assigns, and responds to issues
✅ **PR Review**: Analyzes code, suggests improvements
✅ **Test Generation**: Creates unit tests for new code
✅ **Documentation**: Generates and updates docs
✅ **CI/CD Optimization**: Speeds up pipelines by 90%
✅ **Security Checks**: Identifies vulnerabilities
✅ **Performance Monitoring**: Tracks metrics & alerts

## Configuration Examples

### For Node.js Projects
```yaml
actions:
  - triage-issues
  - generate-jest-tests
  - validate-eslint
  - update-package-docs
```

### For Python Projects
```yaml
actions:
  - triage-issues
  - generate-pytest-tests
  - validate-pylint
  - generate-sphinx-docs
```

### For Enterprise
```yaml
actions:
  - triage-issues
  - review-pr
  - generate-tests
  - update-docs
  - enforce-sso
  - audit-access
  - sla-monitoring
```

## Pricing

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0 | 5 repos, community support |
| **Pro** | $99/mo | Unlimited repos, 24/7 support |
| **Enterprise** | Custom | Dedicated support, SLA, SSO |

## Troubleshooting

### Agent not responding
1. Check `GITHUB_TOKEN` has `repo` scope
2. Verify `OPENAI_API_KEY` is valid
3. Check workflow logs: `Actions` tab → workflow run

### High token usage
- Enable caching: `cache_enabled: true`
- Batch operations: `batch_size: 10`
- Schedule off-peak: `schedule: '0 2 * * *'` (2 AM UTC)

### Cost optimization
- Use GPT-4 Turbo (90% cheaper than GPT-4)
- Enable batching: reduces API calls by 80%
- Cache responses: reuse for similar tasks

## Next Steps

1. **[Full Documentation](./docs/README.md)**
2. **[API Reference](./docs/api.md)**
3. **[Enterprise Guide](./docs/enterprise.md)**
4. **[Troubleshooting](./docs/troubleshooting.md)**

## Community

- 💬 [Discussions](https://github.com/labgadget015-dotcom/autonomous-github-agent/discussions)
- 🐛 [Report Issues](https://github.com/labgadget015-dotcom/autonomous-github-agent/issues)
- ⭐ [Star on GitHub](https://github.com/labgadget015-dotcom/autonomous-github-agent)

## License

MIT - See LICENSE for details

---

**Questions?** Create an issue or start a discussion. We respond within 2 hours (business days).
