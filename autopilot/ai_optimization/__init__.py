"""AI Optimization Package for GitHub Autopilot

This package contains AI-powered optimization modules including:
- intelligent_cache: ML-based caching with predictive invalidation
- ml_priority_scorer: Machine learning priority scoring
- nlp_relevance_filter: NLP-based relevance filtering
- api_optimizer: Reinforcement learning API optimization
- performance_monitor: Performance tracking and benchmarking
"""

from .intelligent_cache import IntelligentCache, get_cache

__version__ = '0.1.0'
__all__ = ['IntelligentCache', 'get_cache']
