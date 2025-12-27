#!/usr/bin/env python3
"""
Metrics Summary Agent (Objective 7)

Generates comprehensive daily/weekly reports and dashboards from CI/CD metrics.
Provides automated recommendations based on quality trends and patterns.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


class MetricsSummaryAgent:
    """Generates summaries and recommendations from quality metrics."""
    
    def __init__(self, output_format: str = 'markdown'):
        self.output_format = output_format
        self.timestamp = datetime.utcnow()
        
        # Configuration from environment
        self.generate_daily = os.getenv('GENERATE_DAILY_REPORTS', 'true').lower() == 'true'
        self.generate_weekly = os.getenv('GENERATE_WEEKLY_SUMMARIES', 'true').lower() == 'true'
        self.slack_channel = os.getenv('REPORT_SLACK_CHANNEL', '#ci-reports')
    
    def load_metrics(self, metrics_dir: str) -> List[Dict]:
        """Load all metrics files from directory."""
        metrics = []
        metrics_path = Path(metrics_dir)
        
        if not metrics_path.exists():
            print(f"Metrics directory not found: {metrics_dir}")
            return metrics
        
        for file in sorted(metrics_path.glob('*.json')):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    data['_filename'] = file.name
                    data['_timestamp'] = file.stat().st_mtime
                    metrics.append(data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Failed to load {file}: {e}")
        
        return metrics
    
    def calculate_trends(self, metrics: List[Dict], metric_key: str) -> Dict:
        """Calculate trends for a specific metric."""
        values = [m.get(metric_key, 0) for m in metrics if metric_key in m]
        
        if not values:
            return {'trend': 'unknown', 'change': 0, 'current': 0, 'average': 0}
        
        current = values[-1] if values else 0
        average = sum(values) / len(values) if values else 0
        
        # Calculate trend
        if len(values) >= 2:
            previous = values[-2]
            change = ((current - previous) / previous * 100) if previous != 0 else 0
            trend = 'improving' if change > 5 else 'declining' if change < -5 else 'stable'
        else:
            change = 0
            trend = 'stable'
        
        return {
            'trend': trend,
            'change': round(change, 2),
            'current': round(current, 2),
            'average': round(average, 2),
            'min': round(min(values), 2),
            'max': round(max(values), 2)
        }
    
    def generate_recommendations(self, summary: Dict) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []
        
        # Coverage recommendations
        if 'coverage' in summary:
            cov = summary['coverage']
            if cov['trend'] == 'declining':
                recommendations.append(
                    f"📉 **Test Coverage Declining** ({cov['change']:.1f}%): "
                    f"Add tests for recently modified files. Current: {cov['current']:.1f}%"
                )
            elif cov['current'] < 80:
                recommendations.append(
                    f"🎯 **Coverage Below Target** ({cov['current']:.1f}% < 80%): "
                    "Focus on testing critical paths and edge cases."
                )
        
        # Complexity recommendations
        if 'complexity' in summary:
            comp = summary['complexity']
            if comp['trend'] == 'increasing' or comp['current'] > 15:
                recommendations.append(
                    f"⚠️ **Code Complexity Increasing** (Current: {comp['current']:.1f}): "
                    "Consider refactoring complex functions. Target: <10 per function."
                )
        
        # Quality score recommendations
        if 'quality_score' in summary:
            qual = summary['quality_score']
            if qual['trend'] == 'declining':
                recommendations.append(
                    f"🚨 **Quality Score Declining** ({qual['change']:.1f}%): "
                    "Review recent changes and address linting issues."
                )
            elif qual['current'] < 7.0:
                recommendations.append(
                    f"🔴 **Quality Below Threshold** ({qual['current']:.1f}/10): "
                    "Focus on code style, documentation, and best practices."
                )
        
        # Security recommendations
        if 'security_issues' in summary:
            sec = summary['security_issues']
            if sec['current'] > 0:
                recommendations.append(
                    f"🔒 **Security Issues Detected** ({int(sec['current'])} issues): "
                    "Run security scan and address vulnerabilities immediately."
                )
        
        # Workflow performance
        if 'workflow_duration' in summary:
            dur = summary['workflow_duration']
            if dur['trend'] == 'increasing':
                recommendations.append(
                    f"⏱️ **Workflow Duration Increasing** (+{dur['change']:.1f}%): "
                    "Consider caching dependencies and parallelizing tests."
                )
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ **All Metrics Healthy**: Continue current practices.")
        else:
            recommendations.append(
                "\n💡 **Pro Tip**: Use `pytest -n auto` for parallel test execution and "
                "enable caching in CI/CD workflows."
            )
        
        return recommendations
    
    def generate_markdown_report(self, metrics: List[Dict], report_type: str = 'daily') -> str:
        """Generate a markdown-formatted report."""
        lines = [
            f"# {'Daily' if report_type == 'daily' else 'Weekly'} Quality Metrics Report",
            f"**Generated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Period:** {'Last 24 hours' if report_type == 'daily' else 'Last 7 days'}",
            "",
            "---",
            ""
        ]
        
        # Calculate summary statistics
        summary = {}
        for key in ['coverage', 'complexity', 'quality_score', 'security_issues', 'workflow_duration']:
            trends = self.calculate_trends(metrics, key)
            if trends['current'] != 0 or trends['average'] != 0:
                summary[key] = trends
        
        # Metrics overview
        lines.extend([
            "## 📊 Metrics Overview",
            "",
            "| Metric | Current | Trend | Change | Average |",
            "|--------|---------|-------|--------|---------|"        ])
        
        metric_labels = {
            'coverage': 'Test Coverage',
            'complexity': 'Avg Complexity',
            'quality_score': 'Quality Score',
            'security_issues': 'Security Issues',
            'workflow_duration': 'Workflow Duration (min)'
        }
        
        trend_emoji = {
            'improving': '📈',
            'declining': '📉',
            'stable': '➡️',
            'unknown': '❔'
        }
        
        for key, data in summary.items():
            label = metric_labels.get(key, key)
            emoji = trend_emoji.get(data['trend'], '')
            change_str = f"{data['change']:+.1f}%" if data['change'] != 0 else "0%"
            
            lines.append(
                f"| {label} | {data['current']:.1f} | {emoji} {data['trend'].title()} | "
                f"{change_str} | {data['average']:.1f} |"
            )
        
        # Recommendations
        lines.extend([
            "",
            "## 🔍 Recommendations",
            ""
        ])
        
        recommendations = self.generate_recommendations(summary)
        for rec in recommendations:
            lines.append(f"- {rec}")
        
        # Recent changes
        if metrics:
            recent = metrics[-1]
            lines.extend([
                "",
                "## 📅 Recent Activity",
                "",
                f"**Last Run:** {datetime.fromtimestamp(recent['_timestamp']).strftime('%Y-%m-%d %H:%M:%S')}" if '_timestamp' in recent else "Unknown",
                f"**Workflow:** {recent.get('workflow_name', 'Unknown')}",
                f"**Status:** {recent.get('status', 'Unknown')}"
            ])
        
        # Footer
        lines.extend([
            "",
            "---",
            f"*Report generated automatically by Metrics Summary Agent*",
            f"*Slack Channel: {self.slack_channel}*"
        ])
        
        return "\n".join(lines)
    
    def generate_json_summary(self, metrics: List[Dict]) -> Dict:
        """Generate a JSON-formatted summary."""
        summary = {
            'generated_at': self.timestamp.isoformat(),
            'metrics_count': len(metrics),
            'summary': {},
            'recommendations': []
        }
        
        # Calculate trends
        for key in ['coverage', 'complexity', 'quality_score', 'security_issues', 'workflow_duration']:
            trends = self.calculate_trends(metrics, key)
            if trends['current'] != 0 or trends['average'] != 0:
                summary['summary'][key] = trends
        
        # Generate recommendations
        summary['recommendations'] = self.generate_recommendations(summary['summary'])
        
        return summary
    
    def save_report(self, content: str, output_file: str):
        """Save report to file."""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Report saved to: {output_file}")
        except IOError as e:
            print(f"❌ Failed to save report: {e}")
    
    def generate_dashboard_data(self, metrics: List[Dict]) -> Dict:
        """Generate data for dashboard visualization."""
        dashboard = {
            'timestamp': self.timestamp.isoformat(),
            'charts': {}
        }
        
        # Time series data for each metric
        for key in ['coverage', 'complexity', 'quality_score', 'workflow_duration']:
            values = []
            timestamps = []
            
            for m in metrics:
                if key in m and '_timestamp' in m:
                    values.append(m[key])
                    timestamps.append(datetime.fromtimestamp(m['_timestamp']).isoformat())
            
            if values:
                dashboard['charts'][key] = {
                    'timestamps': timestamps,
                    'values': values,
                    'trend': self.calculate_trends(metrics, key)
                }
        
        return dashboard


def main():
    parser = argparse.ArgumentParser(
        description='Generate metrics summaries and recommendations'
    )
    parser.add_argument(
        '--metrics-dir',
        required=True,
        help='Directory containing metrics JSON files'
    )
    parser.add_argument(
        '--output',
        default='metrics_summary.md',
        help='Output file path'
    )
    parser.add_argument(
        '--format',
        choices=['markdown', 'json', 'dashboard'],
        default='markdown',
        help='Output format'
    )
    parser.add_argument(
        '--report-type',
        choices=['daily', 'weekly'],
        default='daily',
        help='Report type'
    )
    
    args = parser.parse_args()
    
    agent = MetricsSummaryAgent(output_format=args.format)
    metrics = agent.load_metrics(args.metrics_dir)
    
    if not metrics:
        print("⚠️ No metrics found. Exiting.")
        sys.exit(0)
    
    print(f"Loaded {len(metrics)} metrics files")
    
    # Generate report based on format
    if args.format == 'markdown':
        content = agent.generate_markdown_report(metrics, args.report_type)
        agent.save_report(content, args.output)
        print("\n" + content)
    elif args.format == 'json':
        summary = agent.generate_json_summary(metrics)
        content = json.dumps(summary, indent=2)
        agent.save_report(content, args.output)
        print(json.dumps(summary, indent=2))
    elif args.format == 'dashboard':
        dashboard_data = agent.generate_dashboard_data(metrics)
        content = json.dumps(dashboard_data, indent=2)
        agent.save_report(content, args.output)
        print(f"Dashboard data saved: {args.output}")


if __name__ == '__main__':
    main()
