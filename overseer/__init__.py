"""
Repository Overseer Module

Advanced full-stack repository management and improvement system.
"""

from .orchestrator import RepositoryOverseer
from .code_analyzer import CodeAnalyzer
from .doc_generator import DocumentationGenerator
from .dependency_manager import DependencyManager
from .cicd_optimizer import CICDOptimizer
from .issue_triager import IssueTriager
from .automation_engine import AutomationEngine
from .monitor import RepositoryMonitor

__version__ = "1.0.0"
__all__ = [
    "RepositoryOverseer",
    "CodeAnalyzer",
    "DocumentationGenerator",
    "DependencyManager",
    "CICDOptimizer",
    "IssueTriager",
    "AutomationEngine",
    "RepositoryMonitor",
]
