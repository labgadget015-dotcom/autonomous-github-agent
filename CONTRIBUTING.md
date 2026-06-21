# Contributing Guide

Thank you for your interest in contributing to the Autonomous GitHub Agent!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/autonomous-github-agent.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit: `git commit -m "Add your feature"`
7. Push: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=autonomous_agent

# Format code
black .
ruff check .

# Type checking
mypy .
```

## Adding a New Agent

1. Create `autonomous_agent/agents/your_agent.py`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Add tests in `tests/test_your_agent.py`
5. Update documentation

Example:

```python
from autonomous_agent.core.base_agent import BaseAgent

class YourAgent(BaseAgent):
    async def execute(self, repository: str, **kwargs):
        # Your logic here
        return {"status": "success"}
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public methods
- Keep functions focused and small
- Add comments for complex logic

## Testing

- Write tests for all new features
- Maintain >80% code coverage
- Use pytest fixtures for common setups
- Mock external API calls

## Pull Request Guidelines

- Clear description of changes
- Link related issues
- Include tests
- Update documentation
- Pass all CI checks
