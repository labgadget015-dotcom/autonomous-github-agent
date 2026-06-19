# Core API Documentation

This document provides detailed API documentation for the core infrastructure modules.

## Table of Contents

- [BaseAgent](#baseagent)
- [GitHubClient](#githubclient)
- [LLMClient](#llmclient)
- [AuditLogger](#auditlogger)
- [PolicyEngine](#policyengine)
- [MessageQueue](#messagequeue)

---

## BaseAgent

Base class for all autonomous agents providing lifecycle management.

### Class: `BaseAgent(ABC)`

**Location:** `core/agent_base.py`

#### Constructor

```python
def __init__(self, name: str, config: Dict[str, Any])
```

**Parameters:**
- `name` (str): Unique name for the agent
- `config` (Dict[str, Any]): Configuration dictionary

**Attributes:**
- `name`: Agent name
- `github`: GitHubClient instance
- `llm`: LLMClient instance
- `audit`: AuditLogger instance
- `policy`: PolicyEngine instance

#### Methods

##### execute

```python
async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]
```

Execute a task with full lifecycle management (validate → check policy → execute → log → return).

**Parameters:**
- `task` (Dict): Task dictionary with 'action' and optional 'params' and 'id'

**Returns:**
- Dict with 'status', 'result'/'error', 'task_id', and 'agent'

**Example:**
```python
task = {
    'id': 'task_123',
    'action': 'my_action',
    'params': {'key': 'value'}
}
result = await agent.execute(task)
```

##### validate

```python
def validate(self, task: Dict[str, Any]) -> bool
```

Validate task parameters. Can be overridden by subclasses.

**Parameters:**
- `task` (Dict): Task to validate

**Returns:**
- bool: True if valid

##### get_capabilities

```python
def get_capabilities(self) -> Dict[str, Any]
```

Get agent capabilities.

**Returns:**
- Dict with 'name', 'actions', 'version'

#### Abstract Methods (Must Implement)

##### _execute

```python
@abstractmethod
async def _execute(self, task: Dict[str, Any]) -> Dict[str, Any]
```

Execute the actual task logic. Must be implemented by subclasses.

##### get_supported_actions

```python
@abstractmethod
def get_supported_actions(self) -> list
```

Get list of actions this agent supports.

---

## GitHubClient

GitHub API client with rate limiting and retry logic.

### Class: `GitHubClient`

**Location:** `core/github_client.py`

#### Constructor

```python
def __init__(self, config: Dict[str, Any])
```

**Parameters:**
- `config` (Dict): Configuration with 'github_token' and optional 'github_base_url'

#### Methods

##### check_rate_limit

```python
def check_rate_limit() -> Dict[str, Any]
```

Check current rate limit status.

**Returns:**
- Dict with 'limit', 'remaining', 'reset_time', 'used'

##### get_repository

```python
def get_repository(owner: str, repo: str) -> Repository
```

Get a repository object.

**Parameters:**
- `owner` (str): Repository owner
- `repo` (str): Repository name

**Returns:**
- PyGithub Repository object

##### create_issue

```python
def create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None
) -> Issue
```

Create a new issue.

**Parameters:**
- `owner` (str): Repository owner
- `repo` (str): Repository name
- `title` (str): Issue title
- `body` (str): Issue body
- `labels` (List[str], optional): Label names
- `assignees` (List[str], optional): Assignee usernames

**Returns:**
- PyGithub Issue object

**Example:**
```python
issue = client.create_issue(
    'owner', 'repo',
    'Bug Report',
    'Description of bug',
    labels=['bug', 'high-priority']
)
```

##### get_issue

```python
def get_issue(owner: str, repo: str, issue_number: int) -> Issue
```

Get an issue by number.

##### get_pull_request

```python
def get_pull_request(owner: str, repo: str, pr_number: int) -> PullRequest
```

Get a pull request by number.

##### list_issues

```python
def list_issues(
    owner: str,
    repo: str,
    state: str = 'open',
    labels: Optional[List[str]] = None
) -> List[Issue]
```

List issues in a repository.

**Parameters:**
- `state` (str): 'open', 'closed', or 'all'
- `labels` (List[str], optional): Filter by labels

##### add_comment

```python
def add_comment(owner: str, repo: str, issue_number: int, body: str)
```

Add a comment to an issue or pull request.

---

## LLMClient

Unified LLM client supporting multiple providers.

### Class: `LLMClient`

**Location:** `core/llm_provider.py`

#### Constructor

```python
def __init__(self, config: Dict[str, Any])
```

**Parameters:**
- `config` (Dict): Configuration with 'llm_provider' ('openai' or 'anthropic'), API keys, and optional 'model'

#### Methods

##### generate

```python
async def generate(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> Dict[str, Any]
```

Generate text using the LLM.

**Parameters:**
- `prompt` (str): User prompt
- `system_prompt` (str, optional): System prompt
- `max_tokens` (int): Maximum tokens to generate
- `temperature` (float): Sampling temperature (0-1)

**Returns:**
- Dict with 'content' (str) and 'usage' (Dict)

**Example:**
```python
result = await llm.generate(
    "Explain Python decorators",
    system_prompt="You are a helpful coding assistant",
    max_tokens=500,
    temperature=0.5
)
print(result['content'])
print(f"Tokens used: {result['usage']['total_tokens']}")
```

##### get_token_usage

```python
def get_token_usage() -> int
```

Get total token usage across all requests.

##### reset_token_usage

```python
def reset_token_usage()
```

Reset token usage counter.

---

## AuditLogger

Immutable audit trail for all agent actions.

### Class: `AuditLogger`

**Location:** `core/audit_logger.py`

#### Constructor

```python
def __init__(self, config: Dict[str, Any])
```

**Parameters:**
- `config` (Dict): Configuration with:
  - `audit_log_path` (str): Path to log file
  - `postgres_config` (Dict, optional): PostgreSQL configuration
  - `s3_config` (Dict, optional): S3 configuration

#### Methods

##### log_action

```python
async def log_action(
    agent: str,
    action: str,
    params: Dict[str, Any],
    result: Dict[str, Any],
    task_id: str,
    status: str = 'success'
)
```

Log an agent action.

**Parameters:**
- `agent` (str): Agent name
- `action` (str): Action type
- `params` (Dict): Action parameters
- `result` (Dict): Action result
- `task_id` (str): Unique task ID
- `status` (str): 'success', 'error', or 'pending'

**Example:**
```python
await audit.log_action(
    agent='pr_reviewer',
    action='review_pr',
    params={'pr_number': 123},
    result={'approved': True},
    task_id='task_456',
    status='success'
)
```

##### get_logs

```python
def get_logs(
    agent: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100
) -> list
```

Retrieve audit logs with optional filtering.

**Parameters:**
- `agent` (str, optional): Filter by agent name
- `action` (str, optional): Filter by action type
- `limit` (int): Maximum logs to return

**Returns:**
- List of log entry dictionaries

##### archive_logs

```python
async def archive_logs(older_than_days: int = 90)
```

Archive logs older than specified days to S3.

---

## PolicyEngine

Governance rules and escalation logic.

### Class: `PolicyEngine`

**Location:** `core/policy_engine.py`

#### Constructor

```python
def __init__(self, config: Dict[str, Any])
```

**Parameters:**
- `config` (Dict): Configuration with:
  - `policy_file` (str): Path to policies YAML file
  - `auto_approved` (List[str], optional): Override auto-approved actions
  - `requires_approval` (List[str], optional): Override approval requirements

#### Methods

##### check_action

```python
async def check_action(action: str, params: Dict[str, Any]) -> Dict[str, Any]
```

Check if an action requires approval.

**Parameters:**
- `action` (str): Action name
- `params` (Dict): Action parameters

**Returns:**
- Dict with:
  - `requires_approval` (bool)
  - `reason` (str)
  - `escalation_users` (List[str], optional)

**Example:**
```python
result = await policy.check_action('delete_branch', {'branch': 'main'})
if result['requires_approval']:
    print(f"Approval required: {result['reason']}")
    print(f"Escalate to: {result['escalation_users']}")
```

##### add_approval_rule

```python
def add_approval_rule(action: str)
```

Add an action to the requires_approval list.

##### remove_approval_rule

```python
def remove_approval_rule(action: str)
```

Remove an action from the requires_approval list.

##### get_policies

```python
def get_policies() -> Dict[str, Any]
```

Get current policies.

##### save_policies

```python
def save_policies(policy_file: Optional[str] = None)
```

Save policies to file.

---

## MessageQueue

Redis-based message queue for inter-agent communication.

### Class: `MessageQueue`

**Location:** `core/message_queue.py`

#### Constructor

```python
def __init__(self, config: Dict[str, Any])
```

**Parameters:**
- `config` (Dict): Configuration with:
  - `redis_host` (str): Redis host
  - `redis_port` (int): Redis port
  - `redis_db` (int): Redis database number
  - `redis_password` (str, optional): Redis password

**Note:** Falls back to in-memory queue if Redis is unavailable.

#### Methods

##### publish

```python
async def publish(channel: str, message: Dict[str, Any])
```

Publish a message to a channel.

**Parameters:**
- `channel` (str): Channel name
- `message` (Dict): Message dictionary

##### subscribe

```python
async def subscribe(channel: str, callback: Callable)
```

Subscribe to a channel with a callback.

**Parameters:**
- `channel` (str): Channel name
- `callback` (Callable): Async callback function

##### enqueue

```python
async def enqueue(queue_name: str, task: Dict[str, Any], priority: int = 0)
```

Add a task to a queue.

**Parameters:**
- `queue_name` (str): Queue name
- `task` (Dict): Task dictionary
- `priority` (int): Task priority (higher = more urgent)

**Example:**
```python
await queue.enqueue(
    'agent_tasks',
    {'action': 'review_pr', 'pr_number': 123},
    priority=5
)
```

##### dequeue

```python
async def dequeue(queue_name: str) -> Optional[Dict[str, Any]]
```

Get the next task from a queue (highest priority first).

**Returns:**
- Task dictionary or None if empty

##### get_queue_size

```python
async def get_queue_size(queue_name: str) -> int
```

Get the number of items in a queue.

##### listen

```python
async def listen()
```

Start listening for messages on subscribed channels. Long-running coroutine.

---

## Error Handling

All methods raise appropriate exceptions:

- `ValueError`: Invalid parameters
- `GithubException`: GitHub API errors
- `ConnectionError`: Network/Redis connection issues
- `FileNotFoundError`: Missing configuration files

## Environment Variables

Required environment variables:

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# LLM Provider (choose one or both)
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Optional: Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=audit_logs
POSTGRES_USER=agent_user
POSTGRES_PASSWORD=xxxxxxxxxxxxx

# Optional: Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=xxxxxxxxxxxxx

# Optional: S3
AWS_ACCESS_KEY_ID=xxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxx
S3_AUDIT_BUCKET=agent-audit-logs
```

## Common Patterns

### Creating a Custom Agent

```python
from core.agent_base import BaseAgent

class MyAgent(BaseAgent):
    def get_supported_actions(self):
        return ['my_action', 'another_action']

    async def _execute(self, task):
        action = task['action']
        params = task['params']

        if action == 'my_action':
            # Use self.github, self.llm, etc.
            result = await self.do_something(params)
            return {'status': 'completed', 'result': result}

        raise ValueError(f"Unknown action: {action}")

    async def do_something(self, params):
        # Your logic here
        return {'data': 'result'}
```

### Using the Audit Logger

```python
# In your agent's execute method
await self.audit.log_action(
    agent=self.name,
    action='my_action',
    params=task_params,
    result=task_result,
    task_id=task_id,
    status='success' if no_error else 'error'
)
```

### Checking Policies

```python
# Before executing sensitive operations
policy_check = await self.policy.check_action('delete_branch', {'branch': 'main'})
if policy_check['requires_approval']:
    return {
        'status': 'pending_approval',
        'reason': policy_check['reason']
    }
```

## See Also

- [Architecture Documentation](ARCHITECTURE.md)
- [Policy Configuration](../config/policies.yaml)
- [Agent Configuration](../config/agent_config.yaml)
