# Architecture Documentation

## Phase 1: Core Infrastructure & Orchestrator

This document describes the architecture of the Autonomous GitHub AI System's Phase 1 implementation.

## Overview

The system is built on a modular, agent-based architecture where specialized agents perform specific tasks under the coordination of a master Orchestrator Agent. The core infrastructure provides common functionality for all agents including GitHub integration, LLM access, audit logging, and policy enforcement.

## System Components

### 1. Core Infrastructure (`core/`)

The core package provides foundational classes and utilities used by all agents:

#### BaseAgent (`core/agent_base.py`)
- Abstract base class for all agents
- Implements lifecycle management (validate → execute → log → return)
- Integrates GitHub client, LLM provider, audit logger, and policy engine
- Provides standardized task execution interface

#### GitHubClient (`core/github_client.py`)
- Wrapper around PyGithub with rate limiting
- Automatic retry logic with exponential backoff
- Methods for issues, PRs, comments, and repository operations
- Rate limit monitoring and tracking

#### LLMProvider (`core/llm_provider.py`)
- Unified interface for multiple LLM providers (OpenAI, Anthropic)
- Automatic provider detection and initialization
- Token usage tracking
- Temperature and max_tokens configuration per task type

#### AuditLogger (`core/audit_logger.py`)
- Immutable audit trail for all agent actions
- JSON-based local file logging
- Optional PostgreSQL integration for structured storage
- Optional S3 archival for 90-day retention
- Automatic rollback instruction generation

#### PolicyEngine (`core/policy_engine.py`)
- Governance rules and escalation logic
- Configurable action approval requirements
- Destructive operation detection
- Human-in-the-loop for sensitive actions

#### MessageQueue (`core/message_queue.py`)
- Redis-based inter-agent messaging
- Priority-based task queuing
- Pub/Sub for event broadcasting
- In-memory fallback when Redis unavailable

### 2. Agents (`agents/`)

Specialized agents that perform specific tasks:

#### OrchestratorAgent (`agents/orchestrator_agent.py`)
- Master coordinator for all agents
- Task routing and delegation
- Parallel and sequential execution modes
- Approval issue creation on GitHub
- Load balancing across agents
- Agent status monitoring

### 3. Configuration (`config/`)

YAML-based configuration files:

#### policies.yaml
- Lists of actions requiring approval vs auto-approved
- Escalation user assignments
- Protected paths and branches
- Rate limiting settings

#### code_standards.yaml
- Linting and formatting rules per language
- Code review standards
- Testing requirements
- Documentation standards
- Commit message conventions

#### agent_config.yaml
- Global agent settings
- LLM configuration per task type
- GitHub API settings
- Per-agent configuration
- Message queue settings

#### audit_schema.sql
- PostgreSQL schema for audit logs
- Indexes for performance
- Views for common queries
- Archive function for old logs

## Architecture Diagrams

### Agent Lifecycle

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  1. Validate Task   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Check Policy     │
└──────────┬──────────┘
           │
      ┌────┴────┐
      │         │
   No │         │ Yes
      ▼         ▼
┌──────────┐  ┌─────────────────┐
│ Execute  │  │ Create Approval │
└────┬─────┘  │     Issue       │
     │        └─────────────────┘
     ▼
┌─────────────────────┐
│  3. Execute Task    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  4. Log Action      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  5. Return Result   │
└─────────────────────┘
```

### Task Delegation Flow

```
┌─────────────┐
│   GitHub    │
│   Event     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Orchestrator      │
│   Agent             │
└──────────┬──────────┘
           │
    ┌──────┴──────┬──────────┬─────────┐
    │             │          │         │
    ▼             ▼          ▼         ▼
┌─────────┐  ┌─────────┐ ┌──────┐  ┌──────┐
│ PR      │  │ Issue   │ │Security│ │ Doc  │
│ Review  │  │ Triager │ │Scanner │ │ Gen  │
│ Agent   │  │ Agent   │ │ Agent  │ │ Agent│
└─────────┘  └─────────┘ └────────┘ └──────┘
```

### Data Flow

```
┌──────────────┐
│   GitHub     │
│   API        │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌──────────────┐
│   GitHub     │◄────►│     LLM      │
│   Client     │      │   Provider   │
└──────┬───────┘      └──────────────┘
       │
       ▼
┌──────────────┐      ┌──────────────┐
│  BaseAgent   │◄────►│   Policy     │
│              │      │   Engine     │
└──────┬───────┘      └──────────────┘
       │
       ▼
┌──────────────┐      ┌──────────────┐
│    Audit     │─────►│  PostgreSQL  │
│   Logger     │      │  / S3        │
└──────────────┘      └──────────────┘
```

## Key Features

### 1. Policy-Driven Governance

All agent actions pass through the PolicyEngine which:
- Checks if action is auto-approved
- Identifies destructive operations
- Enforces human-in-the-loop for sensitive actions
- Creates GitHub issues for approval requests

### 2. Immutable Audit Trail

Every action is logged with:
- Timestamp and unique task ID
- Agent name and action type
- Input parameters and output results
- Success/error status
- Rollback instructions

### 3. Flexible Task Execution

The Orchestrator supports:
- **Sequential execution**: Tasks run one after another
- **Parallel execution**: Multiple tasks run concurrently
- **Priority queuing**: High-priority tasks execute first
- **Load balancing**: Distributes work across agents

### 4. Human-in-the-Loop

For actions requiring approval:
1. Policy engine identifies requirement
2. Orchestrator creates GitHub issue
3. Human reviews and comments `/approve` or `/reject`
4. Orchestrator monitors issue and proceeds accordingly

### 5. Multi-LLM Support

The system supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Configurable per task type
- Token usage tracking

## Configuration

### Environment Variables

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# LLM Provider
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Database (optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=audit_logs
POSTGRES_USER=agent_user
POSTGRES_PASSWORD=xxxxxxxxxxxxx

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=xxxxxxxxxxxxx

# S3 (optional)
AWS_ACCESS_KEY_ID=xxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxx
AWS_REGION=us-east-1
S3_AUDIT_BUCKET=agent-audit-logs
```

### Config Files

Place configuration files in the `config/` directory:
- `policies.yaml` - Approval rules and escalation
- `code_standards.yaml` - Code quality standards
- `agent_config.yaml` - Agent-specific settings

## Usage Examples

### 1. Initialize Core Components

```python
from core import GitHubClient, LLMProvider, AuditLogger, PolicyEngine

config = {
    'github_token': 'ghp_xxxxx',
    'openai_api_key': 'sk-xxxxx',
    'llm_provider': 'openai',
    'model': 'gpt-4'
}

github = GitHubClient(config)
llm = LLMProvider(config)
audit = AuditLogger(config)
policy = PolicyEngine(config)
```

### 2. Create a Custom Agent

```python
from core.agent_base import BaseAgent

class MyAgent(BaseAgent):
    def get_supported_actions(self):
        return ['my_action']

    async def _execute(self, task):
        action = task['action']
        params = task['params']

        # Perform action
        result = await self.perform_action(params)

        return {'status': 'success', 'result': result}
```

### 3. Use the Orchestrator

```python
from agents import OrchestratorAgent

orchestrator = OrchestratorAgent(config)
orchestrator.register_agent('my_agent', my_agent_instance)

# Delegate a task
result = await orchestrator.execute({
    'action': 'delegate_task',
    'params': {
        'task_type': 'my_task',
        'task_data': {'key': 'value'}
    }
})
```

### 4. Execute Tasks in Parallel

```python
result = await orchestrator.execute({
    'action': 'execute_parallel',
    'params': {
        'tasks': [
            {'type': 'pr_review', 'data': {'pr_number': 123}},
            {'type': 'security_scan', 'data': {'branch': 'main'}},
            {'type': 'run_tests', 'data': {}}
        ]
    }
})
```

## Security Considerations

1. **Secrets Management**: Use environment variables or secret managers
2. **API Rate Limits**: Built-in rate limiting in GitHubClient
3. **Audit Logging**: All actions are logged immutably
4. **Policy Enforcement**: Destructive operations require approval
5. **Least Privilege**: Configure GitHub App with minimal permissions

## Performance

- **Rate Limiting**: 100ms minimum between GitHub API calls
- **Parallel Execution**: Up to 3 tasks concurrently (configurable)
- **Connection Pooling**: Reuses GitHub API connections
- **Caching**: Redis for inter-agent communication
- **Async Operations**: All I/O operations are async

## Testing

Run the test suite with:

```bash
# All tests
pytest tests/

# With coverage
pytest --cov=core --cov=agents tests/

# Specific test file
pytest tests/test_core.py
```

Target: >= 80% code coverage

## Future Enhancements (Phase 2+)

- Additional specialized agents (PR Review, Security Scanner, etc.)
- Advanced analytics and reporting
- Multi-repository coordination
- Workflow template library
- Self-healing capabilities
- Machine learning for improved routing

## Support

For issues or questions:
- GitHub Issues: https://github.com/labgadget015-dotcom/autonomous-github-agent/issues
- Documentation: https://github.com/labgadget015-dotcom/autonomous-github-agent/tree/main/docs
