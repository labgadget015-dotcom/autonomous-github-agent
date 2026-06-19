# Architecture Overview

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
