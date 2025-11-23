# Autonomous GitHub Agent

> Universal AI agent workflow with chain-of-thought prompting templates, CI/CD integration, and modular orchestration for autonomous GitHub automation

## Overview

This repository provides a comprehensive starter kit for building autonomous AI agents that can operate on GitHub repositories with advanced reasoning capabilities. It combines:

- **Chain-of-Thought (CoT) Prompting Templates** - Multiple reasoning approaches for AI agents
- **CI/CD Integration** - GitHub Actions workflows for automated agent execution
- **Modular Architecture** - Separate, testable components for each workflow stage
- **Policy Enforcement** - Built-in compliance and security checks
- **Artifact-Driven Collaboration** - Complete audit trails and documentation

## Features

✅ **9 Chain-of-Thought Template Types** for flexible reasoning
✅ **GitHub Actions Workflow** pre-configured for autonomous operation
✅ **Modular Python Scripts** for context gathering, reasoning, policy, testing, and docs
✅ **Requirements Management** with all necessary dependencies
✅ **MIT Licensed** for open collaboration

## Chain-of-Thought Prompt Templates

This repository includes comprehensive CoT templates for advanced AI reasoning:

### 1. Zero-shot Chain-of-Thought
Prompts the model to reason step-by-step with no examples.

**Template:**
```
"Let's think step by step."
"Let's work this out in a step-by-step way to be sure we have the right answer."
```

### 2. Few-shot and One-shot Prompting
Guide reasoning by showing example tasks with solutions.

**Template:**
```
Example:
Q: Lucy has 12 colorful marbles, and she wants to share them equally with her 4 friends.
A: Let's think step by step.
Lucy has 12 marbles. She wants to distribute them to 4 friends.
Divide 12 by 4 to get 3 marbles per friend.

Now your problem:
Q: {{New Problem Statement}}
A: Let's think step by step.
```

### 3. Contrastive Chain-of-Thought
Provides both correct and incorrect reasoning paths for comparison.

### 4. Analogical Chain-of-Thought
Guides the model to provide analogies before solving.

### 5. Step-Back Prompting
Generates high-level concepts before detailed reasoning.

### 6. Interactive / Human-in-the-Loop
Enables dialogue and iterative reasoning with feedback loops.

### 7. Multimodal Chain-of-Thought
Integrates text, images, and audio for cross-modal reasoning.

### 8. Compositional Prompting
Breaks complex problems into sequential reasoning sub-tasks.

### 9. Custom Structured Templates
Explicitly outlines expected steps for consistent reasoning.

## Repository Structure

```
autonomous-github-agent/
├── .github/
│   ├── workflows/
│   │   └── ai_agent_workflow.yml    # Main CI/CD pipeline
│   └── scripts/
│       ├── gather_context.py        # Context collection
│       ├── ai_agent_main.py         # Core CoT reasoning
│       ├── check_policy.py          # Policy enforcement
│       ├── test_runner.py           # Automated testing
│       ├── docgen.py                # Documentation generation
│       └── error_handler.py         # Error recovery
├── examples/
│   └── context.json                 # Example context data
├── docs/
│   └── architecture.md              # Architecture documentation
├── tests/
│   └── test_dummy.py                # Test examples
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── LICENSE                          # MIT License
└── .gitignore                       # Python gitignore
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/labgadget015-dotcom/autonomous-github-agent.git
cd autonomous-github-agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Your Agent

Edit `.github/scripts/ai_agent_main.py` to customize your agent's reasoning logic.

### 4. Test Locally

```bash
python .github/scripts/gather_context.py
python .github/scripts/ai_agent_main.py --context examples/context.json
```

### 5. Deploy to GitHub Actions

Push to your repository, and the workflow will automatically run on:
- Pull requests (opened, synchronized, ready for review)
- Pushes to main branch

## Workflow Pipeline

The GitHub Actions workflow executes these stages:

1. **Checkout Code** - Get latest repository state
2. **Setup Python** - Install Python 3.11 environment
3. **Install Dependencies** - Install all required packages
4. **Gather Context** - Collect repo, issue, and PR context
5. **Run AI Agent** - Execute chain-of-thought reasoning
6. **Enforce Policy** - Validate compliance and security
7. **Run Tests** - Execute automated test suite
8. **Generate Documentation** - Auto-update docs
9. **Handle Errors** - Manage failures and retries
10. **Upload Artifacts** - Save results, logs, and diagrams

## Recommended Use Cases

### AI Agent Design & Orchestration
- Use **Compositional + Multimodal CoT** for breaking down agent tasks
- Leverage modular scripts for perception → reasoning → action loops

### Prompt Engineering & Debugging
- Use **Zero-shot** for rapid prototyping
- Use **Few-shot** for high-precision tasks
- Use **Contrastive** for validating agent outputs

### Technical Documentation & Auditing
- Use **Custom Structured Templates** for explicit workflows
- Auto-generate documentation with docgen.py

### IoT & Smart Automation
- Use **Step-Back + Interactive CoT** for safety-critical systems
- Deploy with policy enforcement for compliance

## Advanced Configuration

### Multi-Agent Orchestration

Integrate with Prefect, Airflow, or Temporal for DAG-based orchestration:

```python
from prefect import flow, task

@task
def gather_context():
    # Implementation

@task
def ai_agent_decision(context):
    # Implementation

@flow
def full_github_agent_workflow():
    context = gather_context()
    result = ai_agent_decision(context)
    return result
```

### Docker Deployment

Create a Dockerfile for containerized execution:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", ".github/scripts/ai_agent_main.py"]
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Resources

- [Chain-of-Thought Prompting Guide](https://www.promptingguide.ai/techniques/cot)
- [Multimodal CoT](https://www.promptingguide.ai/techniques/multimodalcot)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Prefect Workflow Orchestration](https://www.prefect.io/)

## Support

For questions, issues, or feature requests, please [open an issue](https://github.com/labgadget015-dotcom/autonomous-github-agent/issues).

---

**Built with ❤️ for autonomous AI automation**
