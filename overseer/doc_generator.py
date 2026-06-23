#!/usr/bin/env python3
"""
Documentation Generator Module

Auto-generates and enhances README files, contributing guidelines,
and relevant documentation.
"""

import ast
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """
    Intelligent documentation generator that creates README, CONTRIBUTING,
    and API documentation from code analysis.
    """

    def __init__(self, repo_path: Path, config: dict):
        self.repo_path = repo_path
        self.config = config
        self.repo_info = self._detect_repository_info()

    def generate(self) -> dict[str, Any]:
        """Generate all documentation"""
        results: dict[str, Any] = {"readme": None, "contributing": None, "api_docs": []}

        return results

    def generate_readme(self) -> Path | None:
        """
        Generate or enhance README.md file.

        Returns:
            Path to generated README
        """
        logger.info("Generating README.md...")

        readme_path = self.repo_path / "README_ENHANCED.md"

        content = self._build_readme_content()

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Enhanced README generated at {readme_path}")
        return readme_path

    def generate_contributing(self) -> Path | None:
        """
        Generate CONTRIBUTING.md file.

        Returns:
            Path to generated CONTRIBUTING.md
        """
        logger.info("Generating CONTRIBUTING.md...")

        contrib_path = self.repo_path / "CONTRIBUTING_ENHANCED.md"

        content = self._build_contributing_content()

        with open(contrib_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"CONTRIBUTING guide generated at {contrib_path}")
        return contrib_path

    def generate_api_docs(self) -> list[Path]:
        """
        Generate API documentation from code.

        Returns:
            List of paths to generated documentation files
        """
        logger.info("Generating API documentation...")

        docs_dir = self.repo_path / "docs" / "api"
        docs_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Find all Python modules
        python_files = list(self.repo_path.glob("**/*.py"))

        for py_file in python_files:
            if self._should_document(py_file):
                doc_file = self._generate_module_docs(py_file, docs_dir)
                if doc_file:
                    generated_files.append(doc_file)

        logger.info(f"Generated {len(generated_files)} API documentation files")
        return generated_files

    def _detect_repository_info(self) -> dict[str, Any]:
        """Detect repository information"""
        info: dict[str, Any] = {
            "name": self.repo_path.name,
            "has_python": False,
            "has_javascript": False,
            "has_tests": False,
            "has_ci": False,
            "frameworks": [],
        }

        # Check for Python
        if list(self.repo_path.glob("**/*.py")):
            info["has_python"] = True

            # Check for common Python frameworks
            requirements = self.repo_path / "requirements.txt"
            if requirements.exists():
                with open(requirements, encoding="utf-8") as f:
                    content = f.read().lower()
                    if "django" in content:
                        info["frameworks"].append("Django")
                    if "flask" in content:
                        info["frameworks"].append("Flask")
                    if "fastapi" in content:
                        info["frameworks"].append("FastAPI")
                    if "pytest" in content:
                        info["has_tests"] = True

        # Check for JavaScript/TypeScript
        if list(self.repo_path.glob("**/*.js")) or list(self.repo_path.glob("**/*.ts")):
            info["has_javascript"] = True

        # Check for CI/CD
        github_workflows = self.repo_path / ".github" / "workflows"
        if github_workflows.exists():
            info["has_ci"] = True

        return info

    def _build_readme_content(self) -> str:
        """Build README.md content"""
        sections = []

        # Title
        sections.append(f"# {self.repo_info['name'].replace('-', ' ').title()}")
        sections.append("")

        # Description
        sections.append("## Overview")
        sections.append("")
        sections.append(
            f"This repository provides {', '.join(self.repo_info['frameworks']) if self.repo_info['frameworks'] else 'a software solution'}."
        )
        sections.append("")

        # Features
        sections.append("## Features")
        sections.append("")
        features = []

        if self.repo_info["has_python"]:
            features.append("✅ Python-based implementation")
        if self.repo_info["has_javascript"]:
            features.append("✅ JavaScript/TypeScript support")
        if self.repo_info["has_tests"]:
            features.append("✅ Comprehensive test coverage")
        if self.repo_info["has_ci"]:
            features.append("✅ Automated CI/CD pipelines")

        for feature in features:
            sections.append(feature)
        sections.append("")

        # Installation
        sections.append("## Installation")
        sections.append("")
        sections.append("```bash")
        sections.append(
            f"git clone https://github.com/your-org/{self.repo_info['name']}.git"
        )
        sections.append(f"cd {self.repo_info['name']}")

        if self.repo_info["has_python"]:
            sections.append("pip install -r requirements.txt")

        sections.append("```")
        sections.append("")

        # Usage
        sections.append("## Usage")
        sections.append("")
        sections.append("See documentation for detailed usage instructions.")
        sections.append("")

        # Contributing
        sections.append("## Contributing")
        sections.append("")
        sections.append(
            "See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute."
        )
        sections.append("")

        # License
        sections.append("## License")
        sections.append("")
        sections.append("See [LICENSE](LICENSE) for license information.")
        sections.append("")

        return "\n".join(sections)

    def _build_contributing_content(self) -> str:
        """Build CONTRIBUTING.md content"""
        sections = []

        sections.append("# Contributing Guidelines")
        sections.append("")
        sections.append("Thank you for your interest in contributing to this project!")
        sections.append("")

        # Getting Started
        sections.append("## Getting Started")
        sections.append("")
        sections.append("1. Fork the repository")
        sections.append(
            "2. Clone your fork: `git clone https://github.com/your-username/repo-name.git`"
        )
        sections.append(
            "3. Create a feature branch: `git checkout -b feature/amazing-feature`"
        )
        sections.append("")

        # Development Setup
        sections.append("## Development Setup")
        sections.append("")

        if self.repo_info["has_python"]:
            sections.append("### Python Environment")
            sections.append("```bash")
            sections.append("python -m venv venv")
            sections.append(
                "source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
            )
            sections.append("pip install -r requirements.txt")
            sections.append("```")
            sections.append("")

        # Code Style
        sections.append("## Code Style")
        sections.append("")

        if self.repo_info["has_python"]:
            sections.append("- Follow PEP 8 guidelines")
            sections.append("- Use type hints where appropriate")
            sections.append("- Write docstrings for all functions and classes")

        sections.append("")

        # Testing
        if self.repo_info["has_tests"]:
            sections.append("## Testing")
            sections.append("")
            sections.append("Run tests before submitting:")
            sections.append("```bash")
            sections.append("pytest")
            sections.append("```")
            sections.append("")

        # Pull Request Process
        sections.append("## Pull Request Process")
        sections.append("")
        sections.append("1. Update documentation as needed")
        sections.append("2. Add tests for new features")
        sections.append("3. Ensure all tests pass")
        sections.append("4. Update CHANGELOG.md")
        sections.append("5. Submit pull request with clear description")
        sections.append("")

        # Code of Conduct
        sections.append("## Code of Conduct")
        sections.append("")
        sections.append("Be respectful and inclusive in all interactions.")
        sections.append("")

        return "\n".join(sections)

    def _should_document(self, file_path: Path) -> bool:
        """Check if file should be documented"""
        # Skip test files, __pycache__, etc.
        parts = file_path.parts
        skip_patterns = ["test_", "__pycache__", ".git", "venv", ".venv"]

        for pattern in skip_patterns:
            if any(pattern in str(part) for part in parts):
                return False

        return True

    def _generate_module_docs(self, py_file: Path, docs_dir: Path) -> Path | None:
        """Generate documentation for a Python module"""
        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Create doc filename
            rel_path = py_file.relative_to(self.repo_path)
            doc_name = str(rel_path).replace("/", "_").replace(".py", ".md")
            doc_path = docs_dir / doc_name

            # Generate documentation
            doc_content = self._extract_module_docs(tree, py_file)

            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(doc_content)

            return doc_path

        except Exception as e:
            logger.warning(f"Error generating docs for {py_file}: {e}")
            return None

    def _extract_module_docs(self, tree: ast.AST, file_path: Path) -> str:
        """Extract documentation from AST"""
        sections = []

        if not isinstance(tree, ast.Module):
            return ""

        # Module docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            sections.append(f"# {file_path.stem}")
            sections.append("")
            sections.append(module_doc)
            sections.append("")

        # Classes and functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                sections.append(f"## Class: {node.name}")
                sections.append("")

                doc = ast.get_docstring(node)
                if doc:
                    sections.append(doc)
                    sections.append("")

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sections.append(f"## Function: {node.name}")
                sections.append("")

                doc = ast.get_docstring(node)
                if doc:
                    sections.append(doc)
                    sections.append("")

        return "\n".join(sections)
