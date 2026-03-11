"""Tests for AI Optimization Modules

This module contains comprehensive tests for all AI optimization components.
"""

import pytest
import time
from datetime import datetime, timedelta
from autopilot.ai_optimization import (
    IntelligentCache, get_cache,
    MLPriorityScorer, get_scorer,
    NLPRelevanceFilter, get_filter,
    APIOptimizationAgent, get_optimizer,
    PerformanceMonitor, get_monitor,
    AnomalyDetector, get_detector,
    CommitSummarizer, get_summarizer
)


# Mock GitHub objects for testing
class MockIssue:
    """Mock GitHub issue object."""
    
    def __init__(self, created_days_ago=10, comments=5, reactions_total=3,
                 labels=None, milestone=None, assignees=None, body="Test issue"):
        self.created_at = datetime.now() - timedelta(days=created_days_ago)
        self.updated_at = datetime.now() - timedelta(days=1)
        self.comments = comments
        self.reactions = type('Reactions', (), {'total_count': reactions_total})
        self.labels = labels or []
        self.milestone = milestone
        self.assignees = assignees or []
        self.body = body
        self.pull_request = None


class MockLabel:
    """Mock GitHub label object."""
    
    def __init__(self, name):
        self.name = name


class MockCommit:
    """Mock GitHub commit object."""
    
    def __init__(self, message="Test commit", additions=10, deletions=5,
                 files=None, author_name="TestAuthor"):
        self.sha = "abc123def456"
        self.commit = type('CommitData', (), {
            'message': message,
            'author': type('Author', (), {'name': author_name})
        })
        self.stats = type('Stats', (), {
            'additions': additions,
            'deletions': deletions,
            'total': additions + deletions
        })
        self.files = files or []


# IntelligentCache Tests
class TestIntelligentCache:
    """Tests for IntelligentCache module."""
    
    def test_cache_creation(self):
        """Test cache can be created."""
        cache = IntelligentCache(max_size=100, ttl=3600)
        assert cache is not None
        assert cache.max_size == 100
        assert cache.default_ttl == 3600
    
    def test_cache_get_miss(self):
        """Test cache miss behavior."""
        cache = IntelligentCache()
        
        fetch_count = [0]
        def fetch_func():
            fetch_count[0] += 1
            return {'data': 'test_value'}
        
        result = cache.get('test_key', fetch_func)
        
        assert result['data'] == 'test_value'
        assert fetch_count[0] == 1
        assert cache.stats['misses'] == 1
    
    def test_cache_get_hit(self):
        """Test cache hit behavior."""
        cache = IntelligentCache()
        cache.staleness_threshold = 1.0  # Never consider stale
        
        fetch_count = [0]
        def fetch_func():
            fetch_count[0] += 1
            return {'data': 'test_value'}
        
        # First call - miss
        result1 = cache.get('test_key', fetch_func)
        # Second call - hit
        result2 = cache.get('test_key', fetch_func)
        
        assert result1 == result2
        assert fetch_count[0] == 1  # Only fetched once
        assert cache.stats['hits'] == 1
    
    def test_cache_invalidate(self):
        """Test cache invalidation."""
        cache = IntelligentCache()
        
        cache.get('test_key', lambda: 'value')
        cache.invalidate('test_key')
        
        stats = cache.get_stats()
        assert stats['cache_size'] == 0
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = IntelligentCache()
        
        cache.get('key1', lambda: 'val1')
        cache.get('key2', lambda: 'val2')
        
        stats = cache.get_stats()
        assert stats['total_requests'] == 2
        assert stats['cache_size'] == 2
        assert 'hit_rate' in stats
    
    def test_global_cache(self):
        """Test global cache singleton."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2


# MLPriorityScorer Tests
class TestMLPriorityScorer:
    """Tests for MLPriorityScorer module."""
    
    def test_scorer_creation(self):
        """Test scorer can be created."""
        scorer = MLPriorityScorer()
        assert scorer is not None
        assert len(scorer.feature_names) > 0
    
    def test_feature_extraction(self):
        """Test feature extraction from issue."""
        scorer = MLPriorityScorer()
        issue = MockIssue(
            created_days_ago=15,
            comments=10,
            reactions_total=5,
            labels=[MockLabel('bug'), MockLabel('high priority')]
        )
        
        features = scorer.extract_features(issue)
        assert features is not None
        assert features.shape[1] == len(scorer.feature_names)
    
    def test_scoring_basic_issue(self):
        """Test scoring a basic issue."""
        scorer = MLPriorityScorer()
        issue = MockIssue()
        
        result = scorer.score(issue)
        
        assert 'score' in result
        assert 'confidence' in result
        assert 'factors' in result
        assert 'priority_level' in result
        assert 0 <= result['score'] <= 100
        assert 0 <= result['confidence'] <= 1
    
    def test_scoring_high_priority_issue(self):
        """Test scoring a high priority issue."""
        scorer = MLPriorityScorer()
        issue = MockIssue(
            created_days_ago=30,
            comments=20,
            reactions_total=15,
            labels=[MockLabel('critical'), MockLabel('bug'), MockLabel('security')]
        )
        
        result = scorer.score(issue)
        
        assert result['score'] > 50  # Should be high priority
        assert result['priority_level'] in ['high', 'critical']
    
    def test_scoring_low_priority_issue(self):
        """Test scoring a low priority issue."""
        scorer = MLPriorityScorer()
        issue = MockIssue(
            created_days_ago=2,
            comments=1,
            reactions_total=0,
            labels=[MockLabel('documentation')]
        )
        
        result = scorer.score(issue)
        
        assert result['score'] < 50  # Should be lower priority
    
    def test_global_scorer(self):
        """Test global scorer singleton."""
        scorer1 = get_scorer()
        scorer2 = get_scorer()
        assert scorer1 is scorer2


# NLPRelevanceFilter Tests
class TestNLPRelevanceFilter:
    """Tests for NLPRelevanceFilter module."""
    
    def test_filter_creation(self):
        """Test filter can be created."""
        filter_obj = NLPRelevanceFilter()
        assert filter_obj is not None
    
    def test_analyze_urgent_text(self):
        """Test analysis of urgent text."""
        filter_obj = NLPRelevanceFilter()
        text = "URGENT: Production is down! Critical security vulnerability."
        
        result = filter_obj.analyze_relevance(text)
        
        assert result['urgency'] > 0.5
        assert result['relevance_score'] > 0.3
    
    def test_analyze_low_priority_text(self):
        """Test analysis of low priority text."""
        filter_obj = NLPRelevanceFilter()
        text = "Fix typo in README.md"
        
        result = filter_obj.analyze_relevance(text)
        
        assert result['noise_level'] > 0.1
        assert result['urgency'] < 0.3
    
    def test_analyze_question(self):
        """Test question detection."""
        filter_obj = NLPRelevanceFilter()
        text = "How do I configure the database connection?"
        
        result = filter_obj.analyze_relevance(text)
        
        assert result['is_question'] is True
    
    def test_entity_extraction(self):
        """Test entity extraction."""
        filter_obj = NLPRelevanceFilter()
        text = "Fix issue #123 reported by @user1. See PR #456."
        
        result = filter_obj.analyze_relevance(text)
        
        assert len(result['key_entities']) > 0
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis."""
        filter_obj = NLPRelevanceFilter()
        
        positive_text = "This is great! Excellent work!"
        positive_result = filter_obj.analyze_relevance(positive_text)
        assert positive_result['sentiment'] == 'positive'
        
        negative_text = "This is broken and doesn't work at all."
        negative_result = filter_obj.analyze_relevance(negative_text)
        assert negative_result['sentiment'] == 'negative'
    
    def test_filter_items(self):
        """Test filtering items by relevance."""
        filter_obj = NLPRelevanceFilter()
        
        items = [
            "URGENT: Critical bug in production",
            "Fix typo",
            "Add important new feature",
            "Update whitespace"
        ]
        
        filtered = filter_obj.filter_items(items, min_relevance=0.3)
        
        # Should filter out low relevance items
        assert len(filtered) < len(items)
    
    def test_global_filter(self):
        """Test global filter singleton."""
        filter1 = get_filter()
        filter2 = get_filter()
        assert filter1 is filter2


# PerformanceMonitor Tests
class TestPerformanceMonitor:
    """Tests for PerformanceMonitor module."""
    
    def test_monitor_creation(self):
        """Test monitor can be created."""
        monitor = PerformanceMonitor()
        assert monitor is not None
    
    def test_record_metric(self):
        """Test recording metrics."""
        monitor = PerformanceMonitor()
        
        monitor.record_metric('execution_time', 1.5)
        monitor.record_metric('execution_time', 2.0)
        
        stats = monitor.get_metric_stats('execution_time')
        assert stats is not None
        assert stats['count'] == 2
        assert stats['mean'] == 1.75
    
    def test_benchmark_function(self):
        """Test benchmarking a function."""
        monitor = PerformanceMonitor()
        
        def test_func():
            time.sleep(0.01)
            return 'result'
        
        result = monitor.benchmark(test_func, 'test_benchmark')
        
        assert result == 'result'
        assert 'test_benchmark' in monitor.benchmarks
        assert len(monitor.benchmarks['test_benchmark']) == 1
    
    def test_benchmark_stats(self):
        """Test benchmark statistics."""
        monitor = PerformanceMonitor()
        
        def fast_func():
            return 'done'
        
        # Run multiple times
        for _ in range(5):
            monitor.benchmark(fast_func, 'test_func')
        
        stats = monitor.get_benchmark_stats('test_func')
        assert stats['total_runs'] == 5
        assert stats['success_rate'] == 1.0
        assert stats['avg_time'] >= 0
    
    def test_baseline_comparison(self):
        """Test baseline comparison."""
        monitor = PerformanceMonitor()
        
        # Record initial metrics
        monitor.record_metric('execution_time', 5.0)
        monitor.set_baseline()
        
        # Record improved metrics
        monitor.record_metric('execution_time', 2.0)
        
        comparison = monitor.compare_to_baseline()
        assert 'execution_time' in comparison
        assert comparison['execution_time']['improvement_percent'] > 0
    
    def test_global_monitor(self):
        """Test global monitor singleton."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        assert monitor1 is monitor2


# APIOptimizationAgent Tests
class TestAPIOptimizationAgent:
    """Tests for APIOptimizationAgent module."""
    
    def test_optimizer_creation(self):
        """Test optimizer can be created."""
        optimizer = APIOptimizationAgent()
        assert optimizer is not None
        assert len(optimizer.strategies) > 0
    
    def test_choose_strategy(self):
        """Test strategy selection."""
        optimizer = APIOptimizationAgent()
        state = optimizer.get_state(1000, 0.5, 'medium')
        
        strategy = optimizer.choose_strategy(state)
        assert strategy in optimizer.strategies
    
    def test_calculate_reward(self):
        """Test reward calculation."""
        optimizer = APIOptimizationAgent()
        
        # Good performance
        reward1 = optimizer.calculate_reward(0.5, 3, True, False)
        assert reward1 > 0
        
        # Rate limit violation
        reward2 = optimizer.calculate_reward(1.0, 10, True, True)
        assert reward2 < reward1  # Should be lower due to violation
    
    def test_execute_strategy(self):
        """Test executing with a strategy."""
        optimizer = APIOptimizationAgent()
        
        def mock_api_call():
            return {'data': 'test'}
        
        calls = [mock_api_call for _ in range(5)]
        result = optimizer.execute_with_strategy('sequential', calls)
        
        assert result['success'] is True
        assert result['api_calls_made'] > 0
        assert len(result['results']) > 0
    
    def test_global_optimizer(self):
        """Test global optimizer singleton."""
        opt1 = get_optimizer()
        opt2 = get_optimizer()
        assert opt1 is opt2


# AnomalyDetector Tests
class TestAnomalyDetector:
    """Tests for AnomalyDetector module."""
    
    def test_detector_creation(self):
        """Test detector can be created."""
        detector = AnomalyDetector()
        assert detector is not None
    
    def test_establish_baseline(self):
        """Test establishing baseline."""
        detector = AnomalyDetector()
        
        commits = [
            MockCommit("Normal commit", 10, 5),
            MockCommit("Another commit", 15, 8),
            MockCommit("Third commit", 20, 10)
        ]
        
        detector.establish_baseline(commits)
        assert detector.baseline is not None
        assert detector.baseline['count'] == 3
    
    def test_detect_normal_change(self):
        """Test detection of normal change."""
        detector = AnomalyDetector()
        
        # Establish baseline
        baseline_commits = [
            MockCommit("Normal", 10, 5) for _ in range(10)
        ]
        detector.establish_baseline(baseline_commits)
        
        # Test normal commit
        commit = MockCommit("Normal commit", 12, 6)
        result = detector.detect_significant_changes(commit)
        
        assert 'is_significant' in result
        assert 'anomaly_score' in result
    
    def test_detect_anomalous_change(self):
        """Test detection of anomalous change."""
        detector = AnomalyDetector()
        
        # Establish baseline with small commits
        baseline_commits = [
            MockCommit("Small", 10, 5, files=['file.py']) for _ in range(10)
        ]
        detector.establish_baseline(baseline_commits)
        
        # Test large commit (anomaly) - many files and lines
        large_files = [type('File', (), {'filename': f'src/file{i}.py'}) for i in range(50)]
        large_commit = MockCommit("Huge refactor", 1000, 500, files=large_files)
        result = detector.detect_significant_changes(large_commit)
        
        # Check that anomaly features are detected in explanation
        explanation = result['explanation'].lower()
        assert 'files changed' in explanation or 'additions' in explanation
        assert result['change_type'] == 'complex_change'
        # Verify features show large values
        assert result['features']['files_changed'] == 50.0
        assert result['features']['lines_added'] == 1000.0
    
    def test_global_detector(self):
        """Test global detector singleton."""
        det1 = get_detector()
        det2 = get_detector()
        assert det1 is det2


# CommitSummarizer Tests
class TestCommitSummarizer:
    """Tests for CommitSummarizer module."""
    
    def test_summarizer_creation(self):
        """Test summarizer can be created."""
        summarizer = CommitSummarizer()
        assert summarizer is not None
    
    def test_generate_summary_empty(self):
        """Test summary generation with no commits."""
        summarizer = CommitSummarizer()
        summary = summarizer.generate_summary([])
        
        assert summary['summary'] == 'No commits to summarize'
        assert summary['statistics']['commit_count'] == 0
    
    def test_generate_summary_with_commits(self):
        """Test summary generation with commits."""
        summarizer = CommitSummarizer()
        
        commits = [
            MockCommit("Fix bug in authentication", 10, 5, author_name="Alice"),
            MockCommit("Add new API endpoint", 50, 10, author_name="Bob"),
            MockCommit("Update documentation", 20, 5, author_name="Alice"),
        ]
        
        summary = summarizer.generate_summary(commits)
        
        assert summary['statistics']['commit_count'] == 3
        assert summary['statistics']['author_count'] == 2
        assert len(summary['summary']) > 0
        assert isinstance(summary['insights'], list)
        assert isinstance(summary['recommended_actions'], list)
    
    def test_extract_themes(self):
        """Test theme extraction."""
        summarizer = CommitSummarizer()
        
        commits = [
            MockCommit("Fix authentication bug"),
            MockCommit("Update authentication flow"),
            MockCommit("Add authentication tests"),
        ]
        
        summary = summarizer.generate_summary(commits)
        
        # Should identify 'authentication' as a theme
        themes = [t['theme'] for t in summary['key_themes']]
        assert 'authentication' in themes or any('auth' in t for t in themes)
    
    def test_action_categorization(self):
        """Test action categorization."""
        summarizer = CommitSummarizer()
        
        commits = [
            MockCommit("Fix bug #123"),
            MockCommit("Add new feature"),
            MockCommit("Remove deprecated code"),
        ]
        
        summary = summarizer.generate_summary(commits)
        actions = summary['action_breakdown']
        
        assert 'fixes' in actions or 'additions' in actions or 'removals' in actions
    
    def test_global_summarizer(self):
        """Test global summarizer singleton."""
        sum1 = get_summarizer()
        sum2 = get_summarizer()
        assert sum1 is sum2


# Integration Tests
class TestIntegration:
    """Integration tests for AI optimization modules."""
    
    def test_full_pipeline(self):
        """Test full optimization pipeline."""
        # Get all components
        cache = IntelligentCache()
        scorer = MLPriorityScorer()
        filter_obj = NLPRelevanceFilter()
        monitor = PerformanceMonitor()
        
        # Create test data
        issue = MockIssue(
            created_days_ago=15,
            comments=10,
            labels=[MockLabel('bug'), MockLabel('high priority')],
            body="URGENT: Fix critical security issue"
        )
        
        # Benchmark the scoring
        def score_issue():
            return scorer.score(issue)
        
        result = monitor.benchmark(score_issue, 'issue_scoring')
        
        # Analyze with NLP
        nlp_result = filter_obj.analyze_relevance(issue.body)
        
        # Verify all components worked
        assert result is not None
        assert 'score' in result
        assert nlp_result['relevance_score'] > 0
        
        stats = monitor.get_benchmark_stats('issue_scoring')
        assert stats['total_runs'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
