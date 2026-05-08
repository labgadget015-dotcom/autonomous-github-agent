#!/usr/bin/env python3
"""
Automation Engine Module

Generates intelligent automation scripts for repetitive tasks like
code formatting, release tagging, and environment setup.
"""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AutomationEngine:
    """
    Intelligent automation script generator for common development tasks.
    """

    def __init__(self, repo_path: Path, config: dict):
        self.repo_path = repo_path
        self.config = config
        self.scripts_dir = repo_path / "scripts" / "automation"

    def generate(self) -> dict[str, Any]:
        """
        Generate automation scripts.

        Returns:
            Dictionary containing generated script information
        """
        logger.info("Generating automation scripts...")

        results = {"formatting": [], "release": [], "setup": []}

        # Ensure scripts directory exists
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

        # Generate formatting scripts
        if self.config.get("automation", {}).get("code_formatting"):
            formatting_scripts = self._generate_formatting_scripts()
            results["formatting"] = formatting_scripts

        # Generate release scripts
        if self.config.get("automation", {}).get("release_tagging"):
            release_scripts = self._generate_release_scripts()
            results["release"] = release_scripts

        # Generate setup scripts
        if self.config.get("automation", {}).get("environment_setup"):
            setup_scripts = self._generate_setup_scripts()
            results["setup"] = setup_scripts

        logger.info(
            f"Generated {len(results['formatting']) + len(results['release']) + len(results['setup'])} automation scripts"
        )

        return results

    def _generate_formatting_scripts(self) -> list[str]:
        """Generate code formatting automation scripts"""
        scripts = []

        # Check if Python project
        if list(self.repo_path.glob("**/*.py")):
            # Generate Python formatting script
            script_path = self.scripts_dir / "format_python.sh"

            content = """#!/bin/bash
# Auto-generated Python code formatting script

set -e

echo "Formatting Python code..."

# Format with black
if command -v black &> /dev/null; then
    black .
    echo "✓ Black formatting complete"
else
    echo "⚠ Black not installed. Install with: pip install black"
fi

# Sort imports with isort
if command -v isort &> /dev/null; then
    isort .
    echo "✓ Import sorting complete"
else
    echo "⚠ isort not installed. Install with: pip install isort"
fi

# Lint with flake8
if command -v flake8 &> /dev/null; then
    flake8 . --max-line-length=120
    echo "✓ Linting complete"
else
    echo "⚠ flake8 not installed. Install with: pip install flake8"
fi

echo "All formatting checks complete!"
"""

            with open(script_path, "w") as f:
                f.write(content)

            # Make executable
            os.chmod(script_path, 0o755)

            scripts.append(str(script_path.relative_to(self.repo_path)))

        # Check if JavaScript project
        if list(self.repo_path.glob("**/*.js")) or list(self.repo_path.glob("**/*.ts")):
            script_path = self.scripts_dir / "format_javascript.sh"

            content = """#!/bin/bash
# Auto-generated JavaScript code formatting script

set -e

echo "Formatting JavaScript/TypeScript code..."

# Format with prettier
if command -v prettier &> /dev/null; then
    prettier --write "**/*.{js,ts,jsx,tsx,json,css,md}"
    echo "✓ Prettier formatting complete"
else
    echo "⚠ Prettier not installed. Install with: npm install -g prettier"
fi

# Lint with eslint
if command -v eslint &> /dev/null; then
    eslint . --fix
    echo "✓ ESLint complete"
else
    echo "⚠ ESLint not installed. Install with: npm install -g eslint"
fi

echo "All formatting checks complete!"
"""

            with open(script_path, "w") as f:
                f.write(content)

            os.chmod(script_path, 0o755)
            scripts.append(str(script_path.relative_to(self.repo_path)))

        return scripts

    def _generate_release_scripts(self) -> list[str]:
        """Generate release automation scripts"""
        scripts = []

        script_path = self.scripts_dir / "create_release.sh"

        content = r"""#!/bin/bash
# Auto-generated release creation script

set -e

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.2.3"
    exit 1
fi

VERSION=$1

# Validate version format (semantic versioning)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format X.Y.Z (e.g., 1.2.3)"
    exit 1
fi

echo "Creating release v$VERSION..."

# Update version in files
echo "Updating version numbers..."
# Add version update commands here based on project type

# Create git tag
echo "Creating git tag..."
git tag -a "v$VERSION" -m "Release version $VERSION"

# Push tag
echo "Pushing tag to remote..."
git push origin "v$VERSION"

echo "✓ Release v$VERSION created successfully!"
echo "GitHub will automatically create a release from the tag."
"""

        with open(script_path, "w") as f:
            f.write(content)

        os.chmod(script_path, 0o755)
        scripts.append(str(script_path.relative_to(self.repo_path)))

        return scripts

    def _generate_setup_scripts(self) -> list[str]:
        """Generate environment setup scripts"""
        scripts = []

        # Check if Python project
        if (self.repo_path / "requirements.txt").exists():
            script_path = self.scripts_dir / "setup_python.sh"

            content = """#!/bin/bash
# Auto-generated Python environment setup script

set -e

echo "Setting up Python development environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
fi

# Install development dependencies
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
    echo "✓ Development dependencies installed"
fi

# Setup pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Setting up pre-commit hooks..."
    pip install pre-commit
    pre-commit install
    echo "✓ Pre-commit hooks installed"
fi

echo ""
echo "Setup complete! To activate the environment, run:"
echo "  source venv/bin/activate"
"""

            with open(script_path, "w") as f:
                f.write(content)

            os.chmod(script_path, 0o755)
            scripts.append(str(script_path.relative_to(self.repo_path)))

        # Check if Node.js project
        if (self.repo_path / "package.json").exists():
            script_path = self.scripts_dir / "setup_nodejs.sh"

            content = """#!/bin/bash
# Auto-generated Node.js environment setup script

set -e

echo "Setting up Node.js development environment..."

# Check Node version
NODE_VERSION=$(node --version)
echo "Node version: $NODE_VERSION"

# Check npm version
NPM_VERSION=$(npm --version)
echo "npm version: $NPM_VERSION"

# Install dependencies
echo "Installing dependencies..."
npm install
echo "✓ Dependencies installed"

# Install husky if configured
if [ -f ".husky/_/husky.sh" ]; then
    echo "Setting up Git hooks with Husky..."
    npm run prepare || true
    echo "✓ Git hooks installed"
fi

echo ""
echo "Setup complete!"
"""

            with open(script_path, "w") as f:
                f.write(content)

            os.chmod(script_path, 0o755)
            scripts.append(str(script_path.relative_to(self.repo_path)))

        return scripts
