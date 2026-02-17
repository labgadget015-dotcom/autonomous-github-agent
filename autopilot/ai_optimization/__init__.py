"""AI Optimization Package for GitHub Autopilot

This package contains AI-powered optimization modules including:
- intelligent_cache: ML-based caching with predictive invalidation
- ml_priority_scorer: Machine learning priority scoring
- nlp_relevance_filter: NLP-based relevance filtering
- api_optimizer: Reinforcement learning API optimization
- performance_monitor: Performance tracking and benchmarking
"""

from .intelligent_cache import IntelligentCache, get_cache
from .ml_priority_scorer import MLPriorityScorer, get_scorer
from .nlp_relevance_filter import NLPRelevanceFilter, get_filter
from .api_optimizer import APIOptimizationAgent, get_optimizer
from .performance_monitor import PerformanceMonitor, get_monitor

__version__ = '0.1.0'
__all__ = [
    'IntelligentCache', 'get_cache',
    'MLPriorityScorer', 'get_scorer',
    'NLPRelevanceFilter', 'get_filter',
    'APIOptimizationAgent', 'get_optimizer',
    'PerformanceMonitor', 'get_monitor'
]
