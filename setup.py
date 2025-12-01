#!/usr/bin/env python3
"""
Setup configuration for Autonomous GitHub Agent
PyPI package for direct Python installation and CLI usage
"""

from setuptools import setup, find_packages
import os

# Read version from __init__.py
version = "1.0.0"
try:
    with open(os.path.join(os.path.dirname(__file__), "src", "__init__.py")) as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split('"')[1]
                break
except Exception:
    pass

# Read long description from README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="autonomous-github-agent",
    version=version,
    author="labgadget015-dotcom",
    author_email="support@autonomous-github-agent.com",
    description="AI-powered GitHub automation with 90% token cost reduction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/labgadget015-dotcom/autonomous-github-agent",
    project_urls={
        "Bug Tracker": "https://github.com/labgadget015-dotcom/autonomous-github-agent/issues",
        "Documentation": "https://github.com/labgadget015-dotcom/autonomous-github-agent/tree/main/docs",
        "Changelog": "https://github.com/labgadget015-dotcom/autonomous-github-agent/releases",
        "Marketplace": "https://github.com/marketplace/actions/autonomous-github-agent",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.9",
    install_requires=[
        "aiohttp>=3.9.0",
        "anthropic>=0.28.0",
        "openai>=1.0.0",
        "PyGithub>=2.1.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "click>=8.0.0",
        "loguru>=0.7.0",
        "tenacity>=8.0.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pylint>=3.0.0",
            "flake8>=6.0.0",
        ],
        "local-llm": [
            "ollama>=0.1.0",
        ],
        "monitoring": [
            "prometheus-client>=0.19.0",
            "opentelemetry-api>=1.0.0",
            "opentelemetry-sdk>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "autonomous-agent=autonomous_agent.cli:main",
            "aga=autonomous_agent.cli:main",  # Short alias
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="github automation ai llm code-review ci-cd github-actions",
    download_url="https://github.com/labgadget015-dotcom/autonomous-github-agent/archive/refs/heads/main.zip",
)
