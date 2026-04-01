#!/usr/bin/env python3
"""
Metrics Collector for CI/CD Pipeline Monitoring
Collects and exports metrics to Prometheus, logs workflows duration and failures
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psutil
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, push_to_gateway


class MetricsCollector:
    """Collects and exports CI/CD pipeline metrics."""
    
    def __init__(self, pushgateway_url: Optional[str] = None):
        self.registry = CollectorRegistry()
        self.pushgateway_url = pushgateway_url or os.getenv(
            'PROMETHEUS_PUSHGATEWAY_URL', 'localhost:9091'
        )
        
        # Define metrics
        self.workflow_duration = Histogram(
            'workflow_duration_seconds',
            'Duration of workflow execution in seconds',
            ['workflow_name', 'job_name'],
            registry=self.registry
        )
        
        self.workflow_success = Counter(
            'workflow_success_total',
            'Total number of successful workflow runs',
            ['workflow_name', 'job_name'],
            registry=self.registry
        )
        
        self.workflow_failure = Counter(
            'workflow_failure_total',
            'Total number of failed workflow runs',
            ['workflow_name', 'job_name'],
            registry=self.registry
        )
        
        self.code_quality_score = Gauge(
            'code_quality_score',
            'Code quality score from static analysis',
            ['tool'],
            registry=self.registry
        )
        
        self.test_coverage = Gauge(
            'test_coverage_percentage',
            'Test coverage percentage',
            ['project'],
            registry=self.registry
        )
        
        self.security_vulnerabilities = Gauge(
            'security_vulnerabilities',
            'Number of security vulnerabilities by severity',
            ['severity'],
            registry=self.registry
        )
        
        self.complexity_score = Gauge(
            'code_complexity_average',
            'Average code complexity score',
            ['metric_type'],
            registry=self.registry
        )
        
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'Current CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_percent',
            'Current memory usage percentage',
            registry=self.registry
        )
    
    def collect_system_metrics(self):
        """Collect current system resource usage."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        self.system_cpu_usage.set(cpu_percent)
        self.system_memory_usage.set(memory.percent)
        
        print(f"📊 System Metrics:")
        print(f"  CPU Usage: {cpu_percent:.2f}%")
        print(f"  Memory Usage: {memory.percent:.2f}%")
    
    def record_workflow_duration(self, workflow_name: str, job_name: str, duration: float):
        """Record workflow execution duration."""
        self.workflow_duration.labels(
            workflow_name=workflow_name,
            job_name=job_name
        ).observe(duration)
        print(f"⏱️  Workflow '{workflow_name}' - Job '{job_name}' took {duration:.2f}s")
    
    def record_workflow_result(self, workflow_name: str, job_name: str, success: bool):
        """Record workflow execution result."""
        if success:
            self.workflow_success.labels(
                workflow_name=workflow_name,
                job_name=job_name
            ).inc()
            print(f"✅ Workflow '{workflow_name}' - Job '{job_name}' succeeded")
        else:
            self.workflow_failure.labels(
                workflow_name=workflow_name,
                job_name=job_name
            ).inc()
            print(f"❌ Workflow '{workflow_name}' - Job '{job_name}' failed")
    
    def update_code_quality(self, tool: str, score: float):
        """Update code quality score from static analysis tools."""
        self.code_quality_score.labels(tool=tool).set(score)
        print(f"📈 Code Quality ({tool}): {score:.2f}")
    
    def update_test_coverage(self, project: str, coverage: float):
        """Update test coverage percentage."""
        self.test_coverage.labels(project=project).set(coverage)
        print(f"🧪 Test Coverage ({project}): {coverage:.2f}%")
    
    def update_security_vulnerabilities(self, vulnerabilities: Dict[str, int]):
        """Update security vulnerability counts by severity."""
        for severity, count in vulnerabilities.items():
            self.security_vulnerabilities.labels(severity=severity).set(count)
            print(f"🔒 {severity.upper()} vulnerabilities: {count}")
    
    def update_complexity(self, metric_type: str, score: float):
        """Update code complexity metrics."""
        self.complexity_score.labels(metric_type=metric_type).set(score)
        print(f"📊 Complexity ({metric_type}): {score:.2f}")
    
    def parse_workflow_metrics(self, reports_dir: Path):
        """Parse reports from various tools and update metrics."""
        print("\n🔍 Parsing workflow reports...")
        
        # Parse Bandit security reports
        bandit_report = reports_dir / 'bandit-report.json'
        if bandit_report.exists():
            with open(bandit_report) as f:
                data = json.load(f)
                results = data.get('results', [])
                
                vulns = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
                for issue in results:
                    severity = issue.get('issue_severity', 'LOW')
                    if severity in vulns:
                        vulns[severity] += 1
                
                self.update_security_vulnerabilities(vulns)
        
        # Parse Radon complexity reports
        radon_cc = reports_dir / 'radon-cc.json'
        if radon_cc.exists():
            with open(radon_cc) as f:
                data = json.load(f)
                complexities = []
                for filepath, metrics in data.items():
                    for metric in metrics:
                        complexities.append(metric.get('complexity', 0))
                
                if complexities:
                    avg_complexity = sum(complexities) / len(complexities)
                    self.update_complexity('cyclomatic', avg_complexity)
        
        # Parse coverage reports
        coverage_xml = reports_dir / 'coverage.xml'
        if coverage_xml.exists():
            # Simple coverage extraction (you can use xml.etree for proper parsing)
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(coverage_xml)
                root = tree.getroot()
                coverage_elem = root.attrib.get('line-rate', '0')
                coverage_pct = float(coverage_elem) * 100
                self.update_test_coverage('main', coverage_pct)
            except Exception as e:
                print(f"Warning: Could not parse coverage report: {e}")
        
        # Parse Pylint reports
        pylint_report = reports_dir / 'pylint-report.json'
        if pylint_report.exists():
            with open(pylint_report) as f:
                try:
                    data = json.load(f)
                    # Pylint score is typically out of 10
                    if isinstance(data, dict) and 'score' in data:
                        self.update_code_quality('pylint', data['score'])
                except Exception as e:
                    print(f"Warning: Could not parse Pylint report: {e}")
    
    def push_metrics(self, job_name: str = 'ci_pipeline'):
        """Push metrics to Prometheus Pushgateway."""
        try:
            push_to_gateway(
                self.pushgateway_url,
                job=job_name,
                registry=self.registry
            )
            print(f"\n✅ Metrics pushed to Pushgateway: {self.pushgateway_url}")
        except Exception as e:
            print(f"\n⚠️  Warning: Could not push metrics to Pushgateway: {e}")
            print("Metrics collected locally but not exported.")
    
    def generate_dashboard_data(self, output_file: Path):
        """Generate JSON data for dashboards."""
        dashboard_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                },
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        
        print(f"📊 Dashboard data written to: {output_file}")


def main():
    """Main entry point for metrics collection."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect and export CI/CD metrics')
    parser.add_argument('--reports-dir', type=Path, default=Path('reports'),
                        help='Directory containing analysis reports')
    parser.add_argument('--workflow-name', type=str, default='ci_pipeline',
                        help='Name of the workflow')
    parser.add_argument('--job-name', type=str, default='metrics_collection',
                        help='Name of the job')
    parser.add_argument('--duration', type=float, help='Workflow duration in seconds')
    parser.add_argument('--success', action='store_true', help='Workflow succeeded')
    parser.add_argument('--push', action='store_true', help='Push metrics to Pushgateway')
    parser.add_argument('--dashboard-output', type=Path, help='Output file for dashboard data')
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = MetricsCollector()
    
    # Collect system metrics
    collector.collect_system_metrics()
    
    # Parse reports if directory exists
    if args.reports_dir.exists():
        collector.parse_workflow_metrics(args.reports_dir)
    else:
        print(f"\n⚠️  Reports directory not found: {args.reports_dir}")
    
    # Record workflow metrics if provided
    if args.duration:
        collector.record_workflow_duration(
            args.workflow_name,
            args.job_name,
            args.duration
        )
    
    collector.record_workflow_result(
        args.workflow_name,
        args.job_name,
        args.success
    )
    
    # Generate dashboard data if requested
    if args.dashboard_output:
        collector.generate_dashboard_data(args.dashboard_output)
    
    # Push metrics if requested
    if args.push:
        collector.push_metrics(args.job_name)
    
    print("\n✅ Metrics collection complete.")


if __name__ == '__main__':
    main()
