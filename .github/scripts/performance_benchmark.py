#!/usr/bin/env python3
"""
GitHub Actions Performance Benchmarking
Tracks workflow performance over time and identifies trends.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics


class PerformanceBenchmark:
    """Benchmark workflow performance."""
    
    def __init__(self, history_file: str = 'performance-history.json'):
        self.history_file = history_file
        self.history = self.load_history()
        
    def load_history(self) -> List[Dict]:
        """Load historical performance data."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Could not load history: {e}")
        return []
        
    def save_history(self):
        """Save performance history."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving history: {e}")
            
    def record_run(
        self,
        workflow_name: str,
        duration: int,
        success: bool,
        metrics: Optional[Dict] = None
    ):
        """Record a workflow run."""
        record = {
            'timestamp': datetime.now().isoformat(),
            'workflow': workflow_name,
            'duration': duration,
            'success': success,
            'metrics': metrics or {},
        }
        self.history.append(record)
        self.save_history()
        
    def get_workflow_stats(
        self,
        workflow_name: str,
        days: int = 30
    ) -> Dict:
        """Get statistics for a workflow."""
        cutoff = datetime.now() - timedelta(days=days)
        
        runs = [
            r for r in self.history
            if r['workflow'] == workflow_name
            and datetime.fromisoformat(r['timestamp']) > cutoff
        ]
        
        if not runs:
            return {}
            
        durations = [r['duration'] for r in runs]
        successes = [r for r in runs if r['success']]
        
        return {
            'total_runs': len(runs),
            'successful_runs': len(successes),
            'failed_runs': len(runs) - len(successes),
            'success_rate': len(successes) / len(runs) * 100,
            'avg_duration': statistics.mean(durations),
            'median_duration': statistics.median(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'std_deviation': statistics.stdev(durations) if len(durations) > 1 else 0,
        }
        
    def get_trends(
        self,
        workflow_name: str,
        days: int = 90
    ) -> Dict:
        """Analyze performance trends."""
        cutoff = datetime.now() - timedelta(days=days)
        
        runs = [
            r for r in self.history
            if r['workflow'] == workflow_name
            and datetime.fromisoformat(r['timestamp']) > cutoff
        ]
        
        if len(runs) < 2:
            return {'trend': 'insufficient_data'}
            
        # Split into first and second half
        mid = len(runs) // 2
        first_half = runs[:mid]
        second_half = runs[mid:]
        
        first_avg = statistics.mean([r['duration'] for r in first_half])
        second_avg = statistics.mean([r['duration'] for r in second_half])
        
        change = second_avg - first_avg
        change_pct = (change / first_avg) * 100 if first_avg > 0 else 0
        
        # Determine trend
        if abs(change_pct) < 5:
            trend = 'stable'
            trend_emoji = '➡️'
        elif change_pct < 0:
            trend = 'improving'
            trend_emoji = '📈'
        else:
            trend = 'degrading'
            trend_emoji = '📉'
            
        return {
            'trend': trend,
            'trend_emoji': trend_emoji,
            'first_half_avg': first_avg,
            'second_half_avg': second_avg,
            'change_seconds': change,
            'change_percentage': change_pct,
        }
        
    def get_percentiles(
        self,
        workflow_name: str,
        days: int = 30
    ) -> Dict:
        """Calculate performance percentiles."""
        cutoff = datetime.now() - timedelta(days=days)
        
        runs = [
            r for r in self.history
            if r['workflow'] == workflow_name
            and datetime.fromisoformat(r['timestamp']) > cutoff
        ]
        
        if not runs:
            return {}
            
        durations = sorted([r['duration'] for r in runs])
        
        def percentile(data, p):
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] + c * (data[f + 1] - data[f])
            return data[f]
            
        return {
            'p50': percentile(durations, 50),
            'p75': percentile(durations, 75),
            'p90': percentile(durations, 90),
            'p95': percentile(durations, 95),
            'p99': percentile(durations, 99),
        }
        
    def generate_benchmark_report(
        self,
        workflow_name: str = 'code-quality-optimized'
    ) -> str:
        """Generate comprehensive benchmark report."""
        stats_7d = self.get_workflow_stats(workflow_name, days=7)
        stats_30d = self.get_workflow_stats(workflow_name, days=30)
        stats_90d = self.get_workflow_stats(workflow_name, days=90)
        trends = self.get_trends(workflow_name, days=90)
        percentiles = self.get_percentiles(workflow_name, days=30)
        
        report = f"""# Performance Benchmark Report: {workflow_name}

## Overview

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        # 7-day stats
        if stats_7d:
            report += f"""### Last 7 Days
- **Total Runs**: {stats_7d['total_runs']}
- **Success Rate**: {stats_7d['success_rate']:.1f}%
- **Average Duration**: {stats_7d['avg_duration']:.1f}s ({stats_7d['avg_duration']/60:.1f} min)
- **Median Duration**: {stats_7d['median_duration']:.1f}s
- **Range**: {stats_7d['min_duration']:.1f}s - {stats_7d['max_duration']:.1f}s
- **Std Deviation**: {stats_7d['std_deviation']:.1f}s

"""
        
        # 30-day stats
        if stats_30d:
            report += f"""### Last 30 Days
- **Total Runs**: {stats_30d['total_runs']}
- **Success Rate**: {stats_30d['success_rate']:.1f}%
- **Average Duration**: {stats_30d['avg_duration']:.1f}s ({stats_30d['avg_duration']/60:.1f} min)
- **Median Duration**: {stats_30d['median_duration']:.1f}s
- **Range**: {stats_30d['min_duration']:.1f}s - {stats_30d['max_duration']:.1f}s

"""
        
        # Percentiles
        if percentiles:
            report += f"""### Performance Percentiles (30 days)
- **P50 (median)**: {percentiles['p50']:.1f}s
- **P75**: {percentiles['p75']:.1f}s
- **P90**: {percentiles['p90']:.1f}s
- **P95**: {percentiles['p95']:.1f}s
- **P99**: {percentiles['p99']:.1f}s

"""
        
        # Trends
        if 'trend' in trends and trends['trend'] != 'insufficient_data':
            report += f"""## Trend Analysis (90 days)

{trends['trend_emoji']} **Trend**: {trends['trend'].title()}

- **First Half Average**: {trends['first_half_avg']:.1f}s
- **Second Half Average**: {trends['second_half_avg']:.1f}s
- **Change**: {trends['change_seconds']:+.1f}s ({trends['change_percentage']:+.1f}%)

"""
        
        # Recommendations
        report += """## Performance Recommendations

"""
        
        recommendations = []
        
        if stats_30d:
            if stats_30d['avg_duration'] > 300:
                recommendations.append("🔴 **High Priority**: Average duration exceeds 5 minutes. Consider optimization.")
            
            if stats_30d['success_rate'] < 90:
                recommendations.append("🔴 **High Priority**: Success rate below 90%. Investigate failures.")
                
            if stats_30d['std_deviation'] > 60:
                recommendations.append("🟡 **Medium Priority**: High variance in duration. Investigate inconsistency.")
                
        if trends and trends['trend'] == 'degrading':
            recommendations.append("🟡 **Medium Priority**: Performance is degrading. Review recent changes.")
            
        if percentiles and percentiles['p99'] > percentiles['p50'] * 2:
            recommendations.append("🟡 **Medium Priority**: P99 is 2x median. Some runs are significantly slower.")
            
        if not recommendations:
            recommendations.append("✅ **All Good**: Performance is stable and within acceptable limits.")
            
        for rec in recommendations:
            report += f"- {rec}\n"
            
        report += """
## Optimization Checklist

- [ ] Review workflow dependencies
- [ ] Check cache hit rates
- [ ] Optimize test execution
- [ ] Review matrix build strategy
- [ ] Check for network bottlenecks
- [ ] Review conditional job execution
- [ ] Consider parallel job optimization
- [ ] Check runner resource usage

## Historical Data

"""
        
        # Add recent runs table
        if stats_7d:
            cutoff = datetime.now() - timedelta(days=7)
            recent = [
                r for r in self.history
                if r['workflow'] == workflow_name
                and datetime.fromisoformat(r['timestamp']) > cutoff
            ][-10:]  # Last 10 runs
            
            report += "### Recent Runs (Last 10)\n\n"
            report += "| Timestamp | Duration | Status | Notes |\n"
            report += "|-----------|----------|--------|-------|\n"
            
            for run in reversed(recent):
                timestamp = datetime.fromisoformat(run['timestamp']).strftime('%m-%d %H:%M')
                duration = f"{run['duration']:.0f}s"
                status = "✅" if run['success'] else "❌"
                notes = run.get('metrics', {}).get('notes', '-')
                report += f"| {timestamp} | {duration} | {status} | {notes} |\n"
                
        report += """
---

**Metrics Collection**: Automated via GitHub Actions
**Next Review**: Weekly
"""
        
        return report
        
    def compare_workflows(
        self,
        workflow_names: List[str],
        days: int = 30
    ) -> str:
        """Compare multiple workflows."""
        report = f"""# Workflow Comparison Report

**Period**: Last {days} days
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Comparison Table

| Workflow | Runs | Success Rate | Avg Duration | P50 | P90 | P95 |
|----------|------|--------------|--------------|-----|-----|-----|
"""
        
        for workflow in workflow_names:
            stats = self.get_workflow_stats(workflow, days)
            percentiles = self.get_percentiles(workflow, days)
            
            if stats:
                report += f"| {workflow} | {stats['total_runs']} | {stats['success_rate']:.1f}% | "
                report += f"{stats['avg_duration']:.0f}s | "
                report += f"{percentiles.get('p50', 0):.0f}s | "
                report += f"{percentiles.get('p90', 0):.0f}s | "
                report += f"{percentiles.get('p95', 0):.0f}s |\n"
            else:
                report += f"| {workflow} | - | - | - | - | - | - |\n"
                
        return report


def main():
    """Main execution."""
    benchmark = PerformanceBenchmark()
    
    # Example: Record current run
    workflow_name = os.getenv('GITHUB_WORKFLOW', 'code-quality-optimized')
    
    # For demo, load from environment or use default
    duration = int(os.getenv('WORKFLOW_DURATION', '0'))
    success = os.getenv('WORKFLOW_STATUS', 'success') == 'success'
    
    if duration > 0:
        print(f"📊 Recording workflow run: {workflow_name}")
        benchmark.record_run(workflow_name, duration, success)
    
    # Generate report
    print("📈 Generating benchmark report...")
    report = benchmark.generate_benchmark_report(workflow_name)
    
    # Save report
    output_file = 'docs/PERFORMANCE_BENCHMARK.md'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Benchmark report saved to {output_file}")
    except Exception as e:
        print(f"❌ Error saving report: {e}")
        
    print("\n✅ Benchmarking complete!")


if __name__ == '__main__':
    main()
