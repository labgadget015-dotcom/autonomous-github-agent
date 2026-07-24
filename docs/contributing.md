# Contributing to Autonomous GitHub Agent

Thank you for your interest in contributing! This guide will help you get started.

## 🚀 Quick Start for Contributors

### 1. Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-username/autonomous-github-agent.git
cd autonomous-github-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# At minimum, set GITHUB_TOKEN and OPENAI_API_KEY
```

### 3. Run Local Tests

Before committing, always run local tests:

```bash
# Full test suite
python scripts/test-local.py

# Fast checks only (recommended during development)
python scripts/test-local.py --fast

# Auto-fix formatting issues
python scripts/test-local.py --fix

# Verbose output for debugging
python scripts/test-local.py -v
```

## 📋 Development Workflow

### Creating a New Feature

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, well-documented code
   - Follow PEP 8 style guidelines
   - Add docstrings to all functions and classes
   - Keep functions focused and under 50 lines

3. **Write tests**
   - Add unit tests for new functionality
   - Aim for 80%+ code coverage
   - Test edge cases and error conditions

4. **Run quality checks**
   ```bash
   # Auto-fix formatting
   black .
   isort .

   # Run linters
   flake8 .
   pylint .github/scripts

   # Run security scan
   bandit -r .github/scripts

   # Run tests with coverage
   pytest --cov=.github/scripts --cov-report=html
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add awesome new feature"
   ```

   **Commit Message Format:**
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Adding tests
   - `refactor:` Code refactoring
   - `perf:` Performance improvements
   - `chore:` Maintenance tasks

6. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 🔍 Code Quality Standards

### Required Standards

- ✅ **Test Coverage:** Minimum 80%
- ✅ **Pylint Score:** Minimum 8.0/10
- ✅ **Complexity:** Maximum cyclomatic complexity of 10
- ✅ **Security:** No medium or high severity issues
- ✅ **Formatting:** Black and isort compliant
- ✅ **Type Hints:** All functions should have type annotations

### Code Style

```python
# Good example
def process_data(input_data: List[Dict], threshold: float = 0.8) -> Dict[str, Any]:
    """
    Process input data and return aggregated results.

    Args:
        input_data: List of data dictionaries to process
        threshold: Minimum confidence threshold (default: 0.8)

    Returns:
        Dictionary containing processed results

    Raises:
        ValueError: If input_data is empty
    """
    if not input_data:
        raise ValueError("Input data cannot be empty")

    results = {}
    # ... processing logic ...
    return results
```

## 🧪 Testing Guidelines

### Writing Tests

```python
# tests/test_my_feature.py
import pytest
from my_module import my_function

class TestMyFunction:
    """Test suite for my_function"""

    def test_basic_functionality(self):
        """Test basic use case"""
        result = my_function(input_data="test")
        assert result == "expected_output"

    def test_edge_case(self):
        """Test edge case handling"""
        result = my_function(input_data="")
        assert result is None

    def test_error_handling(self):
        """Test error conditions"""
        with pytest.raises(ValueError):
            my_function(input_data=None)
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_my_feature.py

# Run with coverage
pytest --cov=.github/scripts --cov-report=html

# Run only fast tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

## 📚 Documentation

### Docstring Format

We use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Short description of function.

    Longer description with more details about what the function does,
    its behavior, and any important notes.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is negative

    Example:
        >>> example_function("test", 42)
        True
    """
```

### Adding Documentation

- Update README.md for user-facing changes
- Add technical details to docs/ folder
- Include code examples in docstrings
- Create diagrams for complex workflows

## 🐛 Bug Reports

### Before Submitting

1. Check existing issues
2. Verify bug in latest version
3. Try to reproduce in clean environment

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. With config '...'
3. See error

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- Package version: [e.g., 1.2.3]

**Additional context**
Any other relevant information.
```

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if feature already requested
2. Describe the use case
3. Explain the expected behavior
4. Provide examples if possible

## 🔒 Security

Found a security vulnerability? Please **do not** open a public issue. Instead:

1. Email security concerns privately
2. Include detailed description
3. Wait for acknowledgment before disclosure

## 📞 Getting Help

- **GitHub Discussions:** Ask questions and discuss ideas
- **Discord:** Join our community server
- **Documentation:** Check docs/ folder
- **Issues:** Search existing issues

## 🎯 Good First Issues

Look for issues labeled `good-first-issue` - these are great for new contributors!

## 📜 Code of Conduct

Be respectful, inclusive, and professional. We're all here to build something great together.

## 🙏 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing! 🚀
