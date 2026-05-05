#!/usr/bin/env python3
"""
AI Optimization Demo - GitHub Autopilot

This script demonstrates the AI-powered optimization features.
"""

import time
from datetime import datetime, timedelta


def demo_intelligent_cache():
    """Demonstrate intelligent caching."""
    from autopilot.ai_optimization import get_cache
    
    print("=" * 70)
    print("DEMO 1: Intelligent Cache with ML-Based Staleness Prediction")
    print("=" * 70)
    
    cache = get_cache()
    
    # Simulate API calls
    call_count = [0]
    
    def expensive_api_call(repo_id):
        call_count[0] += 1
        time.sleep(0.05)  # Simulate API delay
        return {'repo_id': repo_id, 'data': f'repo_data_{repo_id}'}
    
    # Access same repos multiple times
    print("\nAccessing 10 repositories 3 times each...")
    start = time.time()
    
    for iteration in range(3):
        for repo_id in range(10):
            result = cache.get(
                f"repo_{repo_id}",
                lambda id=repo_id: expensive_api_call(id)
            )
    
    elapsed = time.time() - start
    stats = cache.get_stats()
    
    print(f"\n✅ Completed in {elapsed:.2f}s")
    print(f"📊 Cache Statistics:")
    print(f"   - Total requests: {stats['total_requests']}")
    print(f"   - Cache hits: {stats['hits']}")
    print(f"   - Cache misses: {stats['misses']}")
    print(f"   - Hit rate: {stats['hit_rate']:.1%}")
    print(f"   - API calls saved: {30 - call_count[0]} out of 30")
    print(f"   - Time saved: ~{(30 - call_count[0]) * 0.05:.2f}s")


def demo_ml_priority_scorer():
    """Demonstrate ML priority scoring."""
    from autopilot.ai_optimization import get_scorer
    
    print("\n" + "=" * 70)
    print("DEMO 2: ML-Based Priority Scoring")
    print("=" * 70)
    
    scorer = get_scorer()
    
    # Mock issues with different characteristics
    class MockIssue:
        def __init__(self, title, days_old, comments, labels):
            self.title = title
            self.created_at = datetime.now() - timedelta(days=days_old)
            self.updated_at = datetime.now() - timedelta(days=1)
            self.comments = comments
            self.reactions = type('R', (), {'total_count': comments // 2})
            self.labels = [type('L', (), {'name': l}) for l in labels]
            self.milestone = None
            self.assignees = []
            self.body = title
            self.pull_request = None
    
    test_issues = [
        MockIssue("Critical security vulnerability", 5, 20, ['security', 'critical', 'bug']),
        MockIssue("Fix typo in README", 2, 1, ['documentation']),
        MockIssue("Add new feature for authentication", 10, 15, ['enhancement', 'high priority']),
        MockIssue("Question about setup", 1, 3, ['question']),
    ]
    
    print("\nScoring test issues:\n")
    
    for issue in test_issues:
        result = scorer.analyze(issue)
        print(f"Issue: {issue.title[:50]}")
        print(f"  Priority: {result['priority_level'].upper()}")
        print(f"  Score: {result['score']}/100")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Key Factors: {', '.join(result['factors'].get('key_factors', []))}")
        print()


def demo_nlp_relevance_filter():
    """Demonstrate NLP relevance filtering."""
    from autopilot.ai_optimization import get_filter
    
    print("=" * 70)
    print("DEMO 3: NLP-Based Relevance Filtering")
    print("=" * 70)
    
    filter_obj = get_filter()
    
    test_texts = [
        "URGENT: Production database is down! Need immediate fix.",
        "Fix small typo in comment",
        "Implement OAuth2 authentication for API endpoints",
        "How do I configure the environment variables?",
    ]
    
    print("\nAnalyzing text relevance:\n")
    
    for text in test_texts:
        result = filter_obj.analyze_relevance(text)
        print(f"Text: {text[:50]}...")
        print(f"  Relevance: {result['relevance_score']:.2f}")
        print(f"  Urgency: {result['urgency']:.2f}")
        print(f"  Action Required: {result['action_required']}")
        print(f"  Is Question: {result['is_question']}")
        print(f"  Sentiment: {result['sentiment']}")
        print()


def demo_performance_monitor():
    """Demonstrate performance monitoring."""
    from autopilot.ai_optimization import get_monitor
    
    print("=" * 70)
    print("DEMO 4: Performance Monitoring & Benchmarking")
    print("=" * 70)
    
    monitor = get_monitor()
    
    # Benchmark different operations
    def fast_operation():
        return sum(range(100))
    
    def slow_operation():
        time.sleep(0.1)
        return sum(range(1000))
    
    print("\nBenchmarking operations...")
    
    # Run benchmarks
    for _ in range(3):
        monitor.benchmark(fast_operation, "fast_op")
        monitor.benchmark(slow_operation, "slow_op")
    
    # Record metrics
    monitor.record_metric('cache_hit_rate', 0.88)
    monitor.record_metric('cache_hit_rate', 0.92)
    monitor.record_metric('api_calls_per_run', 30)
    monitor.record_metric('api_calls_per_run', 5)
    
    # Show statistics
    print("\n📊 Benchmark Results:")
    for bench_name in ['fast_op', 'slow_op']:
        stats = monitor.get_benchmark_stats(bench_name)
        print(f"\n{bench_name}:")
        print(f"  Runs: {stats['total_runs']}")
        print(f"  Avg Time: {stats['avg_time']*1000:.2f}ms")
        print(f"  Success Rate: {stats['success_rate']:.1%}")


def demo_anomaly_detector():
    """Demonstrate anomaly detection."""
    from autopilot.ai_optimization import get_detector
    
    print("\n" + "=" * 70)
    print("DEMO 5: Anomaly Detection for Significant Changes")
    print("=" * 70)
    
    detector = get_detector()
    
    # Mock commits
    class MockCommit:
        def __init__(self, msg, additions, deletions, num_files):
            self.sha = "abc123"
            self.commit = type('C', (), {
                'message': msg,
                'author': type('A', (), {'name': 'Developer'})
            })
            self.stats = type('S', (), {
                'additions': additions,
                'deletions': deletions,
                'total': additions + deletions
            })
            self.files = [type('F', (), {'filename': f'file{i}.py'}) 
                         for i in range(num_files)]
    
    # Establish baseline with normal commits
    baseline_commits = [
        MockCommit("Fix bug", 15, 8, 2) for _ in range(10)
    ]
    detector.establish_baseline(baseline_commits)
    
    print("\nBaseline established with 10 normal commits")
    
    # Test different commit types
    test_commits = [
        ("Normal commit", MockCommit("Update config", 20, 10, 1)),
        ("Large refactor", MockCommit("Refactor codebase", 500, 300, 30)),
        ("Documentation", MockCommit("Update README", 50, 5, 1)),
    ]
    
    print("\nAnalyzing commits:\n")
    
    for name, commit in test_commits:
        result = detector.detect_significant_changes(commit)
        print(f"{name}:")
        print(f"  Significant: {result['is_significant']}")
        print(f"  Change Type: {result['change_type']}")
        print(f"  Files: {int(result['features']['files_changed'])}")
        print(f"  Lines: +{int(result['features']['lines_added'])} "
              f"-{int(result['features']['lines_deleted'])}")
        print()


def demo_commit_summarizer():
    """Demonstrate commit summarization."""
    from autopilot.ai_optimization import get_summarizer
    
    print("=" * 70)
    print("DEMO 6: Intelligent Commit Summarization")
    print("=" * 70)
    
    summarizer = get_summarizer()
    
    # Mock commits
    class MockCommit:
        def __init__(self, msg, author, additions, deletions):
            self.sha = "abc123"
            self.commit = type('C', (), {
                'message': msg,
                'author': type('A', (), {'name': author})
            })
            self.stats = {'additions': additions, 'deletions': deletions}
            self.files = []
    
    commits = [
        MockCommit("Fix critical security vulnerability in auth module", "Alice", 25, 10),
        MockCommit("Add OAuth2 authentication support", "Bob", 200, 20),
        MockCommit("Update API documentation", "Alice", 50, 10),
        MockCommit("Refactor database queries for performance", "Charlie", 80, 60),
        MockCommit("Add integration tests for auth", "Bob", 150, 5),
        MockCommit("Fix bug in token validation", "Alice", 15, 8),
    ]
    
    summary = summarizer.generate_summary(commits)
    
    print(f"\n📝 Summary:")
    print(f"   {summary['summary']}\n")
    
    print("📊 Statistics:")
    stats = summary['statistics']
    print(f"   - Commits: {stats['commit_count']}")
    print(f"   - Authors: {stats['author_count']}")
    print(f"   - Files Changed: {stats['files_changed']}")
    print(f"   - Lines: +{stats['lines_added']} -{stats['lines_deleted']}")
    
    if summary['key_themes']:
        print("\n🎯 Key Themes:")
        for theme in summary['key_themes'][:3]:
            print(f"   - {theme['theme']} ({theme['frequency']}x)")
    
    if summary['components_affected']:
        print("\n🔧 Components Affected:")
        for component, count in list(summary['components_affected'].items())[:3]:
            print(f"   - {component}: {count}")
    
    if summary['insights']:
        print("\n💡 Insights:")
        for insight in summary['insights'][:3]:
            print(f"   • {insight}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  AI OPTIMIZATION SYSTEM DEMONSTRATION".center(68) + "║")
    print("║" + "  GitHub Autopilot v0.1".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    try:
        demo_intelligent_cache()
        demo_ml_priority_scorer()
        demo_nlp_relevance_filter()
        demo_performance_monitor()
        demo_anomaly_detector()
        demo_commit_summarizer()
        
        print("\n" + "=" * 70)
        print("✅ All demonstrations completed successfully!")
        print("=" * 70)
        print("\nFor more information, see AI_OPTIMIZATION.md\n")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
