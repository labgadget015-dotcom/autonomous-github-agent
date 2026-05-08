"""
Repository Overseer Module

Advanced full-stack repository management and improvement system.
"""

from .automation_engine import AutomationEngine
from .cicd_optimizer import CICDOptimizer
from .code_analyzer import CodeAnalyzer
from .dependency_manager import DependencyManager
from .doc_generator import DocumentationGenerator
from .issue_triager import IssueTriager
from .monitor import RepositoryMonitor
from .orchestrator import RepositoryOverseer

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
