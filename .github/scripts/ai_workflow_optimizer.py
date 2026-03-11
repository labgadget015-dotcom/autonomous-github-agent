#!/usr/bin/env python3
"""
AI-Powered Workflow Optimizer
Uses machine learning to predict optimal workflow configurations and resource allocation
Continuously learns from execution patterns to improve performance
"""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import statistics

try:
    import orjson
    USE_ORJSON = True
    
    def dumps(obj) -> bytes:
        return orjson.dumps(obj)
    
    def loads(data) -> dict:
        return orjson.loads(data)
except ImportError:
    import json as _json
    USE_ORJSON = False
    
    def dumps(obj) -> bytes:
        return _json.dumps(obj).encode('utf-8')
    
    def loads(data) -> dict:
        return _json.loads(data)


@dataclass
class WorkflowMetrics:
    """Metrics for a single workflow execution"""
    workflow_name: str
    commit_sha: str
    timestamp: datetime
    duration_seconds: float
    success: bool
    cache_hit_rate: float
    files_changed: int
    lines_changed: int
    test_count: int
    parallel_jobs: int
    resource_usage: Dict[str, float]  # CPU, memory, disk I/O
    cost_cents: float
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class OptimizationRecommendation:
    """AI-generated optimization recommendation"""
    category: str  # 'parallelization', 'caching', 'resource_allocation', 'timing'
    confidence: float  # 0.0 to 1.0
    estimated_savings_seconds: float
    estimated_cost_savings_cents: float
    recommendation: str
    implementation: str
    risk_level: str  # 'low', 'medium', 'high'
    
    def to_dict(self) -> dict:
        return asdict(self)


class WorkflowPatternAnalyzer:
    """
    Analyzes workflow execution patterns using statistical methods
    (Simplified ML approach - can be extended with sklearn/tensorflow)
    """
    
    def __init__(self, history_file: Path):
        self.history_file = history_file
        self.metrics: List[WorkflowMetrics] = []
        self.load_history()
    
    def load_history(self):
        """Load historical metrics"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'rb') as f:
                    data = loads(f.read())
                    self.metrics = [
                        WorkflowMetrics(
                            workflow_name=m['workflow_name'],
                            commit_sha=m['commit_sha'],
                            timestamp=datetime.fromisoformat(m['timestamp']),
                            duration_seconds=m['duration_seconds'],
                            success=m['success'],
                            cache_hit_rate=m['cache_hit_rate'],
                            files_changed=m['files_changed'],
                            lines_changed=m['lines_changed'],
                            test_count=m['test_count'],
                            parallel_jobs=m['parallel_jobs'],
                            resource_usage=m['resource_usage'],
                            cost_cents=m['cost_cents']
                        )
                        for m in data
                    ]
            except Exception as e:
                print(f"⚠️  Error loading history: {e}")
    
    def save_history(self):
        """Save metrics history"""
        try:
            with open(self.history_file, 'wb') as f:
                data = [m.to_dict() for m in self.metrics]
                f.write(dumps(data))
        except Exception as e:
            print(f"❌ Error saving history: {e}")
    
    def add_metric(self, metric: WorkflowMetrics):
        """Add new metric and save"""
        self.metrics.append(metric)
        # Keep last 1000 executions
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
        self.save_history()
    
    def analyze_cache_patterns(self) -> Optional[OptimizationRecommendation]:
        """Analyze cache hit rates and recommend improvements"""
        if len(self.metrics) < 10:
            return None
        
        recent = self.metrics[-50:]
        cache_rates = [m.cache_hit_rate for m in recent]
        avg_cache_rate = statistics.mean(cache_rates)
        
        if avg_cache_rate < 0.7:  # Less than 70% cache hit rate
            potential_savings = statistics.mean([m.duration_seconds for m in recent]) * 0.3
            
            return OptimizationRecommendation(
                category='caching',
                confidence=0.85,
                estimated_savings_seconds=potential_savings,
                estimated_cost_savings_cents=potential_savings * 0.008 * 60,  # $0.008/min
                recommendation=f"Cache hit rate is {avg_cache_rate:.1%}. Increase cache coverage.",
                implementation="""
                1. Add more paths to cache in workflow YAML
                2. Increase cache retention time
                3. Implement warm cache strategy
                4. Use shared cache across jobs
                """,
                risk_level='low'
            )
        return None
    
    def analyze_parallelization(self) -> Optional[OptimizationRecommendation]:
        """Analyze parallel job efficiency"""
        if len(self.metrics) < 10:
            return None
        
        recent = self.metrics[-50:]
        
        # Check if increasing parallelization would help
        durations_by_jobs = {}
        for m in recent:
            jobs = m.parallel_jobs
            if jobs not in durations_by_jobs:
                durations_by_jobs[jobs] = []
            durations_by_jobs[jobs].append(m.duration_seconds)
        
        if len(durations_by_jobs) >= 2:
            # Find if there's correlation between jobs and duration
            avg_durations = {k: statistics.mean(v) for k, v in durations_by_jobs.items()}
            max_jobs = max(avg_durations.keys())
            
            if max_jobs < 8:  # Could add more parallelization
                potential_savings = avg_durations[max_jobs] * 0.2
                
                return OptimizationRecommendation(
                    category='parallelization',
                    confidence=0.75,
                    estimated_savings_seconds=potential_savings,
                    estimated_cost_savings_cents=potential_savings * 0.008 * 60,
                    recommendation=f"Currently using {max_jobs} parallel jobs. Consider increasing to 8-12.",
                    implementation="""
                    1. Update pytest to use: -n 8
                    2. Split test suites into more groups
                    3. Use matrix strategy for multi-version testing
                    4. Parallelize linting tools
                    """,
                    risk_level='medium'
                )
        return None
    
    def analyze_timing_patterns(self) -> Optional[OptimizationRecommendation]:
        """Analyze execution timing patterns"""
        if len(self.metrics) < 20:
            return None
        
        # Group by hour of day
        by_hour = {}
        for m in self.metrics[-100:]:
            hour = m.timestamp.hour
            if hour not in by_hour:
                by_hour[hour] = []
            by_hour[hour].append(m.duration_seconds)
        
        if len(by_hour) >= 5:
            avg_by_hour = {h: statistics.mean(durations) for h, durations in by_hour.items()}
            fastest_hour = min(avg_by_hour, key=avg_by_hour.get)
            slowest_hour = max(avg_by_hour, key=avg_by_hour.get)
            
            time_diff = avg_by_hour[slowest_hour] - avg_by_hour[fastest_hour]
            
            if time_diff > 60:  # More than 1 minute difference
                return OptimizationRecommendation(
                    category='timing',
                    confidence=0.65,
                    estimated_savings_seconds=time_diff,
                    estimated_cost_savings_cents=time_diff * 0.008 * 60,
                    recommendation=f"Workflows run {time_diff:.0f}s faster at {fastest_hour}:00. Consider scheduling non-urgent workflows during off-peak hours.",
                    implementation="""
                    1. Schedule daily cron jobs for off-peak hours
                    2. Use workflow_dispatch for manual runs
                    3. Implement smart queuing system
                    4. Consider runner scaling patterns
                    """,
                    risk_level='low'
                )
        return None
    
    def analyze_resource_efficiency(self) -> Optional[OptimizationRecommendation]:
        """Analyze resource usage patterns"""
        if len(self.metrics) < 10:
            return None
        
        recent = self.metrics[-50:]
        
        # Check CPU utilization
        cpu_usage = [m.resource_usage.get('cpu_percent', 0) for m in recent]
        avg_cpu = statistics.mean(cpu_usage)
        
        if avg_cpu < 40:  # Under-utilizing CPU
            return OptimizationRecommendation(
                category='resource_allocation',
                confidence=0.80,
                estimated_savings_seconds=0,
                estimated_cost_savings_cents=25.0,  # Could use smaller runners
                recommendation=f"CPU utilization is only {avg_cpu:.1f}%. Consider using smaller runners to reduce costs.",
                implementation="""
                1. Change to ubuntu-latest-small or ubuntu-latest-2-cores
                2. Reduce resource limits in docker-compose
                3. Optimize parallel job count
                4. Consider spot/preemptible instances
                """,
                risk_level='low'
            )
        elif avg_cpu > 85:  # Over-utilizing CPU
            potential_speedup = 30.0  # Estimate
            return OptimizationRecommendation(
                category='resource_allocation',
                confidence=0.75,
                estimated_savings_seconds=potential_speedup,
                estimated_cost_savings_cents=potential_speedup * 0.008 * 60,
                recommendation=f"CPU utilization is {avg_cpu:.1f}%. Upgrade to larger runners for better performance.",
                implementation="""
                1. Upgrade to ubuntu-latest-4-cores or ubuntu-latest-8-cores
                2. Increase docker resource limits
                3. Consider self-hosted runners with better specs
                4. Profile and optimize CPU-intensive tasks
                """,
                risk_level='medium'
            )
        return None
    
    def analyze_cost_trends(self) -> Dict[str, any]:
        """Analyze cost trends over time"""
        if len(self.metrics) < 30:
            return {'status': 'insufficient_data'}
        
        # Last 7 days vs previous 7 days
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        last_week = [m for m in self.metrics if week_ago <= m.timestamp <= now]
        prev_week = [m for m in self.metrics if two_weeks_ago <= m.timestamp < week_ago]
        
        if not last_week or not prev_week:
            return {'status': 'insufficient_data'}
        
        last_week_cost = sum(m.cost_cents for m in last_week) / 100
        prev_week_cost = sum(m.cost_cents for m in prev_week) / 100
        
        change_pct = ((last_week_cost - prev_week_cost) / prev_week_cost * 100) if prev_week_cost > 0 else 0
        
        return {
            'status': 'analyzed',
            'last_week_cost_usd': last_week_cost,
            'prev_week_cost_usd': prev_week_cost,
            'change_percent': change_pct,
            'trend': 'increasing' if change_pct > 5 else 'decreasing' if change_pct < -5 else 'stable',
            'monthly_projection_usd': last_week_cost * 4.33
        }
    
    def generate_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate all optimization recommendations"""
        recommendations = []
        
        # Run all analysis functions
        analyses = [
            self.analyze_cache_patterns(),
            self.analyze_parallelization(),
            self.analyze_timing_patterns(),
            self.analyze_resource_efficiency(),
        ]
        
        for rec in analyses:
            if rec:
                recommendations.append(rec)
        
        # Sort by estimated savings
        recommendations.sort(
            key=lambda r: r.estimated_savings_seconds + (r.estimated_cost_savings_cents / 100),
            reverse=True
        )
        
        return recommendations


class AIWorkflowOptimizer:
    """
    Main AI optimizer that coordinates analysis and generates reports
    """
    
    def __init__(self, history_file: str = '.workflow_history.json'):
        self.analyzer = WorkflowPatternAnalyzer(Path(history_file))
    
    async def optimize(self) -> Dict[str, any]:
        """Run optimization analysis"""
        print("🤖 AI Workflow Optimizer\n")
        print("📊 Analyzing workflow patterns...\n")
        
        # Generate recommendations
        recommendations = self.analyzer.generate_recommendations()
        
        # Analyze cost trends
        cost_analysis = self.analyzer.analyze_cost_trends()
        
        # Calculate total potential savings
        total_time_savings = sum(r.estimated_savings_seconds for r in recommendations)
        total_cost_savings = sum(r.estimated_cost_savings_cents for r in recommendations) / 100
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics_analyzed': len(self.analyzer.metrics),
            'recommendations': [r.to_dict() for r in recommendations],
            'cost_analysis': cost_analysis,
            'total_potential_savings': {
                'time_seconds': total_time_savings,
                'time_minutes': total_time_savings / 60,
                'cost_usd_per_run': total_cost_savings,
                'cost_usd_monthly': total_cost_savings * 30 * 10  # Assume 10 runs/day
            }
        }
        
        return report
    
    def print_report(self, report: Dict[str, any]):
        """Print optimization report"""
        print("="*70)
        print("🎯 AI OPTIMIZATION RECOMMENDATIONS")
        print("="*70)
        
        print(f"\n📈 Analysis Summary:")
        print(f"  • Metrics analyzed: {report['metrics_analyzed']}")
        print(f"  • Recommendations: {len(report['recommendations'])}")
        
        if report['cost_analysis']['status'] == 'analyzed':
            cost = report['cost_analysis']
            print(f"\n💰 Cost Trends:")
            print(f"  • Last week: ${cost['last_week_cost_usd']:.2f}")
            print(f"  • Previous week: ${cost['prev_week_cost_usd']:.2f}")
            print(f"  • Change: {cost['change_percent']:+.1f}% ({cost['trend']})")
            print(f"  • Monthly projection: ${cost['monthly_projection_usd']:.2f}")
        
        savings = report['total_potential_savings']
        print(f"\n💎 Total Potential Savings:")
        print(f"  • Time: {savings['time_minutes']:.1f} minutes per run")
        print(f"  • Cost: ${savings['cost_usd_per_run']:.2f} per run")
        print(f"  • Monthly: ${savings['cost_usd_monthly']:.2f}")
        
        if report['recommendations']:
            print(f"\n🔍 Recommendations (by priority):\n")
            
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"{i}. {rec['category'].upper()} (Confidence: {rec['confidence']:.0%}, Risk: {rec['risk_level']})")
                print(f"   {rec['recommendation']}")
                print(f"   💰 Savings: {rec['estimated_savings_seconds']:.0f}s, ${rec['estimated_cost_savings_cents']/100:.2f}")
                print(f"   📝 Implementation:{rec['implementation']}")
                print()
        else:
            print("\n✅ No optimization recommendations - workflows are well-optimized!")
        
        print("="*70)


async def simulate_metrics(optimizer: AIWorkflowOptimizer):
    """Simulate some historical metrics for demo"""
    import random
    
    for i in range(50):
        metric = WorkflowMetrics(
            workflow_name='code-quality',
            commit_sha=f'abc{i:04d}',
            timestamp=datetime.now() - timedelta(hours=random.randint(1, 168)),
            duration_seconds=random.uniform(180, 480),
            success=random.random() > 0.1,
            cache_hit_rate=random.uniform(0.5, 0.95),
            files_changed=random.randint(1, 50),
            lines_changed=random.randint(10, 500),
            test_count=random.randint(50, 200),
            parallel_jobs=random.choice([2, 4, 4, 4, 6]),
            resource_usage={
                'cpu_percent': random.uniform(30, 90),
                'memory_mb': random.uniform(500, 2000),
                'disk_io_mb': random.uniform(100, 500)
            },
            cost_cents=random.uniform(5, 15)
        )
        optimizer.analyzer.add_metric(metric)


async def main():
    """Main entry point"""
    optimizer = AIWorkflowOptimizer()
    
    # Simulate data if history is empty
    if len(optimizer.analyzer.metrics) < 10:
        print("📝 Simulating historical data for demo...\n")
        await simulate_metrics(optimizer)
    
    # Run optimization
    report = await optimizer.optimize()
    
    # Print report
    optimizer.print_report(report)
    
    # Save report
    report_file = Path('ai-optimization-report.json')
    with open(report_file, 'wb') as f:
        f.write(dumps(report))
    print(f"\n✅ Report saved to {report_file}")


if __name__ == '__main__':
    asyncio.run(main())
