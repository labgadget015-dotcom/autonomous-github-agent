#!/usr/bin/env python3
"""
Automation Scripts Generator

Generates intelligent automation scripts for common repository tasks.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

# Script templates
SCRIPTS = {
    "format_python": {
        "name": "format-python.sh",
        "description": "Format Python code with black and isort",
        "content": """#!/bin/bash
# Auto-generated Python code formatter
set -e

echo "🎨 Formatting Python code..."

# Check if black is installed
if ! command -v black &> /dev/null; then
    echo "Installing black..."
    pip install black
fi

# Check if isort is installed
if ! command -v isort &> /dev/null; then
    echo "Installing isort..."
    pip install isort
fi

# Format with black
echo "Running black..."
black . --line-length 100 --exclude '/(\.git|\.venv|venv|__pycache__|\.tox|dist|build)/'

# Sort imports with isort
echo "Running isort..."
isort . --profile black --skip-gitignore

echo "✅ Python code formatting complete!"
""",
    },
    "format_javascript": {
        "name": "format-javascript.sh",
        "description": "Format JavaScript/TypeScript code with prettier",
        "content": """#!/bin/bash
# Auto-generated JavaScript code formatter
set -e

echo "🎨 Formatting JavaScript/TypeScript code..."

# Check if prettier is installed
if ! command -v prettier &> /dev/null; then
    echo "Installing prettier..."
    npm install -g prettier
fi

# Format with prettier
echo "Running prettier..."
prettier --write "**/*.{js,jsx,ts,tsx,json,css,scss,md}" \\
    --ignore-path .gitignore

echo "✅ JavaScript code formatting complete!"
""",
    },
    "release_tag": {
        "name": "create-release.sh",
        "description": "Create a new release with automatic versioning",
        "content": """#!/bin/bash
# Auto-generated release tagger
set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${GREEN}🚀 Release Creation Script${NC}"
echo ""

# Get current version from git tags
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "Current version: $CURRENT_VERSION"

# Parse version numbers
VERSION=${CURRENT_VERSION#v}
IFS='.' read -ra VERSION_PARTS <<< "$VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

# Ask for version bump type
echo ""
echo "Select version bump type:"
echo "1) Patch (v$MAJOR.$MINOR.$((PATCH+1)))"
echo "2) Minor (v$MAJOR.$((MINOR+1)).0)"
echo "3) Major (v$((MAJOR+1)).0.0)"
echo "4) Custom"
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        NEW_VERSION="v$MAJOR.$MINOR.$((PATCH+1))"
        ;;
    2)
        NEW_VERSION="v$MAJOR.$((MINOR+1)).0"
        ;;
    3)
        NEW_VERSION="v$((MAJOR+1)).0.0"
        ;;
    4)
        read -p "Enter custom version (e.g., v1.2.3): " NEW_VERSION
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}Creating release: $NEW_VERSION${NC}"

# Get commit messages since last tag
echo ""
echo "Recent changes:"
git log $CURRENT_VERSION..HEAD --oneline --decorate

# Confirm
echo ""
read -p "Proceed with release $NEW_VERSION? [y/N]: " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Release cancelled"
    exit 0
fi

# Create tag
git tag -a "$NEW_VERSION" -m "Release $NEW_VERSION"

# Push tag
git push origin "$NEW_VERSION"

echo ""
echo -e "${GREEN}✅ Release $NEW_VERSION created successfully!${NC}"
echo "View release: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\\(.*\\)\\.git/\\1/')/releases/tag/$NEW_VERSION"
""",
    },
    "setup_dev_env": {
        "name": "setup-dev-env.sh",
        "description": "Setup development environment",
        "content": """#!/bin/bash
# Auto-generated development environment setup
set -e

echo "🛠️  Setting up development environment..."

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo "Detected OS: $OS"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python $(python3 --version) found"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Install pre-commit hooks if available
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Installing pre-commit hooks..."
    pip install pre-commit
    pre-commit install
fi

# Check for Node.js dependencies
if [ -f "package.json" ]; then
    if command -v npm &> /dev/null; then
        echo "Installing Node.js dependencies..."
        npm install
    else
        echo "⚠️  package.json found but npm not installed"
    fi
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate  # Linux/macOS"
echo "  .venv\\Scripts\\activate     # Windows"
""",
    },
    "run_tests": {
        "name": "run-tests.sh",
        "description": "Run all tests with coverage",
        "content": """#!/bin/bash
# Auto-generated test runner
set -e

echo "🧪 Running tests..."

# Check if pytest is installed
if ! python -m pytest --version &> /dev/null; then
    echo "Installing pytest..."
    pip install pytest pytest-cov pytest-xdist
fi

# Run tests with coverage
echo "Running pytest with coverage..."
python -m pytest \\
    --verbose \\
    --cov=. \\
    --cov-report=html \\
    --cov-report=term \\
    --cov-report=xml \\
    -n auto \\
    tests/

# Check coverage threshold
COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
THRESHOLD=80

echo ""
if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
    echo "⚠️  Coverage ($COVERAGE%) is below threshold ($THRESHOLD%)"
    exit 1
else
    echo "✅ Coverage ($COVERAGE%) meets threshold ($THRESHOLD%)"
fi

echo ""
echo "Coverage report: htmlcov/index.html"
""",
    },
    "lint_code": {
        "name": "lint-code.sh",
        "description": "Run linters on codebase",
        "content": """#!/bin/bash
# Auto-generated code linter
set -e

echo "🔍 Running linters..."

EXIT_CODE=0

# Python linting
if ls *.py 2>/dev/null || [ -d "scripts" ] || [ -d "src" ]; then
    echo "Linting Python code..."
    
    # flake8
    if command -v flake8 &> /dev/null; then
        echo "Running flake8..."
        flake8 . --max-line-length=100 --exclude=.git,__pycache__,.venv,venv || EXIT_CODE=1
    fi
    
    # pylint
    if command -v pylint &> /dev/null; then
        echo "Running pylint..."
        find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*" | xargs pylint || EXIT_CODE=1
    fi
    
    # mypy
    if command -v mypy &> /dev/null; then
        echo "Running mypy..."
        mypy . --ignore-missing-imports || EXIT_CODE=1
    fi
fi

# JavaScript linting
if [ -f "package.json" ]; then
    if command -v npm &> /dev/null; then
        if grep -q "eslint" package.json; then
            echo "Running ESLint..."
            npm run lint || EXIT_CODE=1
        fi
    fi
fi

# Security linting
if command -v bandit &> /dev/null; then
    echo "Running security scan with bandit..."
    bandit -r . -x ./.venv,./venv,./tests || EXIT_CODE=1
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All linting checks passed!"
else
    echo "❌ Some linting checks failed"
fi

exit $EXIT_CODE
""",
    },
}


def generate_scripts(output_dir: Path = None) -> List[Path]:
    """
    Generate all automation scripts.

    Args:
        output_dir: Directory to save scripts (default: scripts/automation)

    Returns:
        List of generated script paths
    """
    if output_dir is None:
        output_dir = Path("scripts") / "automation"

    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    print(f"📁 Generating automation scripts in {output_dir}...")
    print()

    for script_id, script_data in SCRIPTS.items():
        script_path = output_dir / script_data["name"]

        # Write script
        with open(script_path, "w") as f:
            f.write(script_data["content"])

        # Make executable
        script_path.chmod(0o755)

        generated.append(script_path)
        print(f"✅ Generated: {script_data['name']}")
        print(f"   Description: {script_data['description']}")

    print()
    print(f"🎉 Generated {len(generated)} automation scripts!")

    # Create README
    readme_path = output_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write("# Automation Scripts\n\n")
        f.write("Auto-generated scripts for common repository tasks.\n\n")
        f.write("## Available Scripts\n\n")

        for script_id, script_data in SCRIPTS.items():
            f.write(f"### {script_data['name']}\n\n")
            f.write(f"{script_data['description']}\n\n")
            f.write(f"```bash\n")
            f.write(f"./{script_data['name']}\n")
            f.write(f"```\n\n")

    print(f"📝 Generated: {readme_path}")

    return generated


def main():
    """Main entry point"""
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    generated = generate_scripts(output_dir)

    print()
    print("💡 Usage:")
    print("  Make scripts executable: chmod +x scripts/automation/*.sh")
    print("  Run a script: ./scripts/automation/format-python.sh")

    return 0


if __name__ == "__main__":
    sys.exit(main())
