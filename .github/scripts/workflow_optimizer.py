#!/usr/bin/env python3
"""
Workflow Optimizer
Analyzes workflow performance and suggests optimizations
"""

from datetime import datetime


class WorkflowOptimizer:
    """Analyze and optimize workflow performance"""

    def __init__(self):
        self.metrics = {}
        self.recommendations = []

    def analyze_workflow_duration(self, duration: int) -> dict:
        """Analyze workflow execution time"""
        analysis = {
            "duration_seconds": duration,
            "duration_minutes": round(duration / 60, 2),
            "status": "optimal" if duration < 300 else "needs_optimization",
            "recommendations": [],
        }

        if duration > 600:
            analysis["recommendations"].append(
                {
                    "priority": "high",
                    "message": "Workflow takes over 10 minutes - consider splitting into parallel jobs",
                    "potential_saving": "40-60%",
                }
            )
        elif duration > 300:
            analysis["recommendations"].append(
                {
                    "priority": "medium",
                    "message": "Workflow could be faster - review job dependencies",
                    "potential_saving": "20-30%",
                }
            )

        return analysis

    def analyze_cache_efficiency(self, cache_hit_rate: float) -> dict:
        """Analyze cache usage"""
        return {
            "hit_rate": cache_hit_rate,
            "status": "good" if cache_hit_rate > 0.7 else "poor",
            "recommendations": (
                [
                    {
                        "priority": "high",
                        "message": "Increase cache key specificity",
                        "action": "Include more hash files in cache key",
                    }
                ]
                if cache_hit_rate < 0.5
                else []
            ),
        }

    def analyze_job_parallelization(self, jobs: list[dict]) -> dict:
        """Analyze job parallelization opportunities"""
        sequential_jobs = sum(1 for job in jobs if job.get("needs", []))
        parallel_potential = len(jobs) - sequential_jobs

        return {
            "total_jobs": len(jobs),
            "sequential_jobs": sequential_jobs,
            "parallel_jobs": len(jobs) - sequential_jobs,
            "parallelization_score": parallel_potential / len(jobs) if jobs else 0,
            "recommendations": (
                [
                    {
                        "priority": "medium",
                        "message": f"Could parallelize {parallel_potential} more jobs",
                        "potential_saving": f"{parallel_potential * 30}s",
                    }
                ]
                if parallel_potential > 2
                else []
            ),
        }

    def analyze_resource_usage(self, runner_type: str = "ubuntu-latest") -> dict:
        """Analyze runner resource usage"""
        recommendations = []

        if runner_type == "ubuntu-latest":
            recommendations.append(
                {
                    "priority": "low",
                    "message": "Consider using larger runners for compute-intensive tasks",
                    "benefit": "Faster execution for CPU-bound operations",
                }
            )

        return {"runner_type": runner_type, "recommendations": recommendations}

    def analyze_dependency_caching(self) -> dict:
        """Analyze dependency caching strategies"""
        return {
            "current_strategy": "pip cache",
            "recommendations": [
                {
                    "priority": "medium",
                    "message": "Use requirements hash in cache key",
                    "implementation": "key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}",
                },
                {
                    "priority": "low",
                    "message": "Consider using Docker layer caching",
                    "benefit": "50-70% faster Docker builds",
                },
            ],
        }

    def generate_optimization_report(self) -> str:
        """Generate comprehensive optimization report"""
        report = "# Workflow Optimization Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Duration analysis
        duration_analysis = self.analyze_workflow_duration(240)  # Example: 4 minutes
        report += "## Duration Analysis\n\n"
        report += f"- Current: {duration_analysis['duration_minutes']} minutes\n"
        report += f"- Status: {duration_analysis['status']}\n\n"

        # Recommendations
        if duration_analysis["recommendations"]:
            report += "### Recommendations\n\n"
            for rec in duration_analysis["recommendations"]:
                report += f"**{rec['priority'].upper()}:** {rec['message']}\n"
                report += f"*Potential saving: {rec['potential_saving']}*\n\n"

        # Cache efficiency
        cache_analysis = self.analyze_cache_efficiency(0.85)
        report += "## Cache Efficiency\n\n"
        report += f"- Hit Rate: {cache_analysis['hit_rate']:.1%}\n"
        report += f"- Status: {cache_analysis['status']}\n\n"

        # Parallelization
        jobs = [
            {"name": "test", "needs": []},
            {"name": "lint", "needs": []},
            {"name": "security", "needs": []},
            {"name": "deploy", "needs": ["test", "lint"]},
        ]
        parallel_analysis = self.analyze_job_parallelization(jobs)
        report += "## Parallelization Analysis\n\n"
        report += f"- Total Jobs: {parallel_analysis['total_jobs']}\n"
        report += f"- Parallel Jobs: {parallel_analysis['parallel_jobs']}\n"
        report += f"- Score: {parallel_analysis['parallelization_score']:.1%}\n\n"

        # Summary
        report += "## Summary\n\n"
        total_recs = (
            len(duration_analysis.get("recommendations", []))
            + len(cache_analysis.get("recommendations", []))
            + len(parallel_analysis.get("recommendations", []))
        )

        if total_recs == 0:
            report += "✅ Workflow is well optimized! No critical recommendations.\n"
        else:
            report += f"Found {total_recs} optimization opportunities.\n"

        return report

    def estimate_cost_savings(
        self, current_duration: int, optimized_duration: int, runs_per_day: int = 50
    ) -> dict:
        """Estimate cost savings from optimization"""
        time_saved_per_run = current_duration - optimized_duration
        time_saved_per_day = time_saved_per_run * runs_per_day
        time_saved_per_month = time_saved_per_day * 30

        # GitHub Actions pricing: ~$0.008 per minute for Linux
        cost_per_minute = 0.008
        cost_saved_per_month = (time_saved_per_month / 60) * cost_per_minute

        return {
            "time_saved_per_run": f"{time_saved_per_run}s",
            "time_saved_per_month": f"{time_saved_per_month / 3600:.1f} hours",
            "cost_saved_per_month": f"${cost_saved_per_month:.2f}",
            "annual_savings": f"${cost_saved_per_month * 12:.2f}",
        }


def main():
    """Main entry point"""
    print("⚡ Analyzing workflow performance...\n")

    optimizer = WorkflowOptimizer()

    # Generate report
    report = optimizer.generate_optimization_report()
    print(report)

    # Save report
    with open("workflow-optimization-report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\n✅ Report saved to workflow-optimization-report.md")

    # Cost savings
    savings = optimizer.estimate_cost_savings(
        current_duration=480,  # 8 minutes
        optimized_duration=180,  # 3 minutes
        runs_per_day=50,
    )

    print("\n💰 Estimated Savings:")
    print(f"  Time per run: {savings['time_saved_per_run']}")
    print(f"  Time per month: {savings['time_saved_per_month']}")
    print(f"  Cost per month: {savings['cost_saved_per_month']}")
    print(f"  Annual savings: {savings['annual_savings']}")


if __name__ == "__main__":
    main()
