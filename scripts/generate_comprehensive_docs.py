#!/usr/bin/env python3
"""
Comprehensive Documentation Generator

Generates detailed, professional documentation for repositories.
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ComprehensiveDocGenerator:
    """Generate comprehensive documentation from code analysis"""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.project_info = self._analyze_project()

    def _analyze_project(self) -> Dict:
        """Analyze project structure and metadata"""
        info = {
            "name": self.repo_path.name,
            "has_python": (self.repo_path / "requirements.txt").exists()
            or (self.repo_path / "setup.py").exists()
            or (self.repo_path / "pyproject.toml").exists(),
            "has_javascript": (self.repo_path / "package.json").exists(),
            "has_docker": (self.repo_path / "Dockerfile").exists(),
            "has_tests": (self.repo_path / "tests").exists()
            or (self.repo_path / "test").exists(),
            "has_ci": (self.repo_path / ".github" / "workflows").exists(),
            "modules": self._find_modules(),
            "scripts": self._find_scripts(),
        }
        return info

    def _find_modules(self) -> List[str]:
        """Find Python modules in the project"""
        modules = []
        for item in self.repo_path.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                modules.append(item.name)
        return modules

    def _find_scripts(self) -> List[str]:
        """Find executable scripts"""
        scripts = []
        scripts_dir = self.repo_path / "scripts"
        if scripts_dir.exists():
            for item in scripts_dir.iterdir():
                if item.is_file() and os.access(item, os.X_OK):
                    scripts.append(item.name)
        return scripts

    def generate_api_reference(self) -> str:
        """Generate API reference documentation"""
        content = []
        content.append("# API Reference\n")
        content.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")

        # Document modules
        for module in self.project_info["modules"]:
            module_path = self.repo_path / module
            content.append(f"## Module: `{module}`\n\n")

            # Find Python files in module
            for py_file in module_path.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue

                try:
                    with open(py_file) as f:
                        tree = ast.parse(f.read())

                    # Document classes
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            content.append(f"### Class: `{node.name}`\n\n")
                            docstring = ast.get_docstring(node)
                            if docstring:
                                content.append(f"{docstring}\n\n")

                            # Document methods
                            methods = [
                                n
                                for n in node.body
                                if isinstance(
                                    n, (ast.FunctionDef, ast.AsyncFunctionDef)
                                )
                            ]
                            if methods:
                                content.append("#### Methods\n\n")
                                for method in methods:
                                    if method.name.startswith("_"):
                                        continue  # Skip private methods

                                    args = [
                                        a.arg
                                        for a in method.args.args
                                        if a.arg != "self"
                                    ]
                                    content.append(
                                        f"##### `{method.name}({', '.join(args)})`\n\n"
                                    )

                                    method_doc = ast.get_docstring(method)
                                    if method_doc:
                                        content.append(f"{method_doc}\n\n")

                        # Document module-level functions
                        elif isinstance(node, ast.FunctionDef):
                            if not node.name.startswith("_"):
                                args = [a.arg for a in node.args.args]
                                content.append(
                                    f"### Function: `{node.name}({', '.join(args)})`\n\n"
                                )

                                func_doc = ast.get_docstring(node)
                                if func_doc:
                                    content.append(f"{func_doc}\n\n")

                except Exception as e:
                    print(f"Warning: Could not parse {py_file}: {e}")

        return "".join(content)

    def generate_user_guide(self) -> str:
        """Generate user guide"""
        content = []
        content.append("# User Guide\n\n")
        content.append(f"*For {self.project_info['name']}*\n\n")

        # Installation
        content.append("## Installation\n\n")

        if self.project_info["has_python"]:
            content.append("### Python Setup\n\n")
            content.append("```bash\n")
            content.append("# Clone the repository\n")
            content.append(f"git clone <repository-url>\n")
            content.append(f"cd {self.project_info['name']}\n\n")
            content.append("# Create virtual environment\n")
            content.append("python -m venv .venv\n")
            content.append(
                "source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate\n\n"
            )
            content.append("# Install dependencies\n")
            content.append("pip install -r requirements.txt\n")
            content.append("```\n\n")

        if self.project_info["has_javascript"]:
            content.append("### JavaScript Setup\n\n")
            content.append("```bash\n")
            content.append("# Install dependencies\n")
            content.append("npm install\n")
            content.append("```\n\n")

        # Usage
        content.append("## Usage\n\n")

        # Scripts
        if self.project_info["scripts"]:
            content.append("### Available Scripts\n\n")
            for script in self.project_info["scripts"]:
                content.append(f"- `{script}`: Description needed\n")
            content.append("\n")

        # Testing
        if self.project_info["has_tests"]:
            content.append("## Testing\n\n")
            content.append("Run tests with:\n\n")
            content.append("```bash\n")
            if self.project_info["has_python"]:
                content.append("pytest\n")
            content.append("```\n\n")

        # Development
        content.append("## Development\n\n")
        content.append("### Code Style\n\n")
        content.append("This project follows standard coding conventions.\n\n")

        if self.project_info["has_ci"]:
            content.append("### Continuous Integration\n\n")
            content.append("This project uses GitHub Actions for CI/CD.\n\n")

        return "".join(content)

    def generate_architecture_doc(self) -> str:
        """Generate architecture documentation"""
        content = []
        content.append("# Architecture\n\n")
        content.append(f"*System architecture for {self.project_info['name']}*\n\n")

        content.append("## Overview\n\n")
        content.append(
            "This document describes the high-level architecture of the system.\n\n"
        )

        # Components
        content.append("## Components\n\n")

        for module in self.project_info["modules"]:
            content.append(f"### {module.title()}\n\n")

            # Try to get module docstring
            init_file = self.repo_path / module / "__init__.py"
            if init_file.exists():
                try:
                    with open(init_file) as f:
                        tree = ast.parse(f.read())
                    docstring = ast.get_docstring(tree)
                    if docstring:
                        content.append(f"{docstring}\n\n")
                except:
                    pass

        # Data Flow
        content.append("## Data Flow\n\n")
        content.append("Describe how data flows through the system.\n\n")

        # Dependencies
        content.append("## External Dependencies\n\n")

        if (
            self.project_info["has_python"]
            and (self.repo_path / "requirements.txt").exists()
        ):
            content.append("### Python Dependencies\n\n")
            content.append("See `requirements.txt` for the full list.\n\n")

        if (
            self.project_info["has_javascript"]
            and (self.repo_path / "package.json").exists()
        ):
            content.append("### JavaScript Dependencies\n\n")
            content.append("See `package.json` for the full list.\n\n")

        return "".join(content)

    def generate_contributing_guide(self) -> str:
        """Generate contributing guide"""
        content = []
        content.append("# Contributing Guide\n\n")
        content.append(
            f"Thank you for your interest in contributing to {self.project_info['name']}!\n\n"
        )

        content.append("## Getting Started\n\n")
        content.append("1. Fork the repository\n")
        content.append("2. Clone your fork\n")
        content.append("3. Create a new branch for your feature\n")
        content.append("4. Make your changes\n")
        content.append("5. Run tests\n")
        content.append("6. Submit a pull request\n\n")

        content.append("## Development Setup\n\n")
        content.append(
            "See the [User Guide](USER_GUIDE.md) for setup instructions.\n\n"
        )

        content.append("## Code Style\n\n")

        if self.project_info["has_python"]:
            content.append("### Python\n\n")
            content.append("- Follow PEP 8 style guide\n")
            content.append("- Use type hints where appropriate\n")
            content.append("- Write docstrings for all public functions and classes\n")
            content.append("- Maximum line length: 100 characters\n\n")

        if self.project_info["has_javascript"]:
            content.append("### JavaScript\n\n")
            content.append("- Follow ESLint configuration\n")
            content.append("- Use modern ES6+ syntax\n")
            content.append("- Write JSDoc comments for functions\n\n")

        content.append("## Testing\n\n")
        content.append("All new features must include tests.\n\n")

        if self.project_info["has_tests"]:
            content.append("Run tests with:\n\n")
            content.append("```bash\n")
            if self.project_info["has_python"]:
                content.append("pytest\n")
            content.append("```\n\n")

        content.append("## Pull Request Process\n\n")
        content.append("1. Update documentation as needed\n")
        content.append("2. Add tests for new functionality\n")
        content.append("3. Ensure all tests pass\n")
        content.append("4. Update CHANGELOG.md\n")
        content.append("5. Request review from maintainers\n\n")

        content.append("## Code of Conduct\n\n")
        content.append("Please be respectful and constructive in all interactions.\n\n")

        return "".join(content)

    def generate_all_docs(self, output_dir: Path = None) -> Dict[str, Path]:
        """Generate all documentation"""
        if output_dir is None:
            output_dir = self.repo_path / "docs"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated = {}

        # API Reference
        api_ref = self.generate_api_reference()
        api_path = output_dir / "API_REFERENCE.md"
        with open(api_path, "w") as f:
            f.write(api_ref)
        generated["api_reference"] = api_path
        print(f"✅ Generated: {api_path}")

        # User Guide
        user_guide = self.generate_user_guide()
        guide_path = output_dir / "USER_GUIDE.md"
        with open(guide_path, "w") as f:
            f.write(user_guide)
        generated["user_guide"] = guide_path
        print(f"✅ Generated: {guide_path}")

        # Architecture
        arch = self.generate_architecture_doc()
        arch_path = output_dir / "ARCHITECTURE.md"
        with open(arch_path, "w") as f:
            f.write(arch)
        generated["architecture"] = arch_path
        print(f"✅ Generated: {arch_path}")

        # Contributing
        contrib = self.generate_contributing_guide()
        contrib_path = self.repo_path / "CONTRIBUTING_GENERATED.md"
        with open(contrib_path, "w") as f:
            f.write(contrib)
        generated["contributing"] = contrib_path
        print(f"✅ Generated: {contrib_path}")

        return generated


def main():
    """Main entry point"""
    import sys

    repo_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    print(f"📚 Generating comprehensive documentation for: {repo_path}")
    print()

    generator = ComprehensiveDocGenerator(repo_path)
    generated = generator.generate_all_docs()

    print()
    print(f"🎉 Generated {len(generated)} documentation files!")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
