"""
Complete setup script for Autonomous GitHub Agent.
Run this after creating the directory structure.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(r"C:\Users\aw789\autonomous-github-agent")

# File contents
FILES = {
    "autonomous_agent/__init__.py": '''"""
Autonomous GitHub Agent - AI-powered repository management system.
"""

__version__ = "0.1.0"
__author__ = "Autonomous Agent Team"

from autonomous_agent.core.orchestrator import Orchestrator
from autonomous_agent.core.github_client import GitHubClient
from autonomous_agent.core.config import Config

__all__ = ["Orchestrator", "GitHubClient", "Config"]
''',
    "autonomous_agent/core/__init__.py": '''"""Core components for the autonomous agent system."""''',
    "autonomous_agent/agents/__init__.py": '''"""Specialized micro-agents for different GitHub operations."""''',
    "autonomous_agent/utils/__init__.py": '''"""Utility functions and helpers."""''',
}


def create_file(path: Path, content: str) -> None:
    """Create a file with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ Created: {path.relative_to(BASE_DIR)}")


def main():
    """Create all necessary files."""
    print("Setting up Autonomous GitHub Agent...\n")

    # Create directories
    dirs = [
        "autonomous_agent/core",
        "autonomous_agent/agents",
        "autonomous_agent/utils",
        "tests",
        "config",
        "workflows",
        "docs",
        "logs",
    ]

    for dir_path in dirs:
        (BASE_DIR / dir_path).mkdir(parents=True, exist_ok=True)

    print(f"✓ Created directory structure\n")

    # Create files
    for file_path, content in FILES.items():
        create_file(BASE_DIR / file_path, content)

    print("\n" + "=" * 50)
    print("Setup complete! 🎉")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Copy .env.example to .env and add your tokens")
    print("2. Run: pip install -e .")
    print("3. Run: python create_core_files.py")
    print("\nHappy automating!")


if __name__ == "__main__":
    main()
