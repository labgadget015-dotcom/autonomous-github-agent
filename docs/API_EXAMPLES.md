# 📚 Autonomous GitHub Agent - API Examples

## REST API Reference

### Authentication
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.autonomous-agent.dev/v1/tasks
```

### Create Autonomous Task
```bash
curl -X POST https://api.autonomous-agent.dev/v1/tasks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "org/repo",
    "action": "triage-issues",
    "config": {
      "labels_enable": true,
      "auto_assign": true,
      "response_template": "default"
    }
  }'
```

### List Active Tasks
```bash
curl https://api.autonomous-agent.dev/v1/tasks?repo=org/repo \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:
```json
{
  "tasks": [
    {
      "id": "task_123abc",
      "repo": "org/repo",
      "action": "triage-issues",
      "status": "active",
      "processed": 42,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Python SDK

### Installation
```bash
pip install autonomous-github-agent
```

### Basic Usage
```python
from autonomous_agent import Agent

agent = Agent(token="your_github_token")

# Triage all issues
agent.triage_issues(
    repo="org/repo",
    labels={"bug": "priority:high", "feature": "priority:low"},
    auto_assign=True
)

# Review pull requests
agent.review_prs(
    repo="org/repo",
    check_tests=True,
    check_coverage=True,
    suggest_improvements=True
)

# Generate documentation
agent.generate_docs(
    repo="org/repo",
    output_format="markdown",
    include_examples=True
)
```

### Advanced Configuration
```python
from autonomous_agent import Agent
from autonomous_agent.config import AgentConfig

config = AgentConfig(
    model="gpt-4-turbo",
    temperature=0.7,
    max_tokens=2000,
    timeout=300,
    retry_attempts=3,
    cache_enabled=True,
    batch_size=10
)

agent = Agent(
    token="your_github_token",
    config=config
)
```

## JavaScript/TypeScript SDK

### Installation
```bash
npm install autonomous-github-agent
```

### Usage
```typescript
import { AutonomousAgent } from 'autonomous-github-agent';

const agent = new AutonomousAgent({
  token: process.env.GITHUB_TOKEN,
  apiKey: process.env.OPENAI_API_KEY
});

// Triage issues
await agent.triageIssues({
  repo: 'org/repo',
  labels: {
    bug: 'priority:high',
    feature: 'priority:low'
  },
  autoAssign: true
});

// Review PRs with custom rules
await agent.reviewPRs({
  repo: 'org/repo',
  rules: {
    requireTests: true,
    minCoverage: 80,
    checkSecurity: true
  }
});

// Listen to events
agent.on('issue:triaged', (issue) => {
  console.log(`Triaged: ${issue.title}`);
});
```

## Webhook Integration

### Setup Webhook
```bash
curl -X POST https://api.autonomous-agent.dev/v1/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhook",
    "events": ["issue.opened", "pull_request.opened"],
    "secret": "your_webhook_secret"
  }'
```

### Handle Webhook Payload
```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_secret"

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Verify signature
    signature = request.headers.get('X-Signature')
    payload = request.get_data()
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return {'error': 'Invalid signature'}, 401

    data = request.json
    event_type = data['event']

    if event_type == 'issue.opened':
        # Auto-triage new issue
        agent.triage_issue(data['issue'])

    return {'status': 'ok'}, 200
```

## Rate Limiting

| Tier | Requests/Hour | Concurrent Tasks |
|------|---------------|------------------|
| Free | 100 | 1 |
| Pro | 10,000 | 10 |
| Enterprise | Unlimited | 100 |

## Error Handling

```python
from autonomous_agent import Agent
from autonomous_agent.errors import AuthError, RateLimitError, APIError

agent = Agent(token="your_token")

try:
    agent.triage_issues(repo="org/repo")
except AuthError:
    print("Invalid token")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except APIError as e:
    print(f"API error: {e.message}")
```

## Batch Operations

```python
# Process 100 repos efficiently
repos = [
    "org/repo1",
    "org/repo2",
    # ... 98 more repos
]

# Enable batching for 80% reduction in API calls
agent.batch_triage_issues(
    repos=repos,
    batch_size=10,
    parallel=True
)
```

## Caching Strategy

```python
from autonomous_agent import Agent
from autonomous_agent.cache import RedisCache

cache = RedisCache(
    host="localhost",
    port=6379,
    ttl=3600  # 1 hour
)

agent = Agent(
    token="your_token",
    cache=cache
)

# All responses cached for 1 hour
result = agent.triage_issues(repo="org/repo")
```

## Support

- Documentation: https://docs.autonomous-agent.dev
- Issues: https://github.com/labgadget015-dotcom/autonomous-github-agent/issues
- Email: support@autonomous-agent.dev
