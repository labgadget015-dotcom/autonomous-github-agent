"""Unit tests for .github/scripts/workflow_optimizer.py"""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from workflow_optimizer import WorkflowOptimizer


class TestWorkflowOptimizerInit:
    def test_creates_with_empty_metrics(self):
        opt = WorkflowOptimizer()
        assert opt.metrics == {}
        assert opt.recommendations == []


class TestAnalyzeWorkflowDuration:
    def _opt(self):
        return WorkflowOptimizer()

    def test_optimal_duration(self):
        opt = self._opt()
        result = opt.analyze_workflow_duration(180)
        assert result["status"] == "optimal"
        assert result["recommendations"] == []

    def test_duration_needs_optimization(self):
        opt = self._opt()
        result = opt.analyze_workflow_duration(400)
        assert result["status"] == "needs_optimization"
        assert len(result["recommendations"]) > 0
        assert result["recommendations"][0]["priority"] == "medium"

    def test_very_long_duration_high_priority(self):
        opt = self._opt()
        result = opt.analyze_workflow_duration(700)
        assert result["status"] == "needs_optimization"
        assert any(r["priority"] == "high" for r in result["recommendations"])

    def test_duration_minutes_calculated(self):
        opt = self._opt()
        result = opt.analyze_workflow_duration(300)
        assert result["duration_minutes"] == 5.0

    def test_duration_seconds_stored(self):
        opt = self._opt()
        result = opt.analyze_workflow_duration(123)
        assert result["duration_seconds"] == 123


class TestAnalyzeCacheEfficiency:
    def _opt(self):
        return WorkflowOptimizer()

    def test_high_cache_hit_rate_is_good(self):
        opt = self._opt()
        result = opt.analyze_cache_efficiency(0.85)
        assert result["status"] == "good"
        assert result["recommendations"] == []

    def test_low_cache_hit_rate_is_poor(self):
        opt = self._opt()
        result = opt.analyze_cache_efficiency(0.3)
        assert result["status"] == "poor"
        assert len(result["recommendations"]) > 0

    def test_hit_rate_stored(self):
        opt = self._opt()
        result = opt.analyze_cache_efficiency(0.75)
        assert result["hit_rate"] == 0.75

    def test_boundary_at_0_7(self):
        opt = self._opt()
        # 0.7 is NOT above 0.7, so it's poor
        poor = opt.analyze_cache_efficiency(0.7)
        assert poor["status"] == "poor"
        good = opt.analyze_cache_efficiency(0.71)
        assert good["status"] == "good"


class TestAnalyzeJobParallelization:
    def _opt(self):
        return WorkflowOptimizer()

    def test_empty_jobs_returns_zero_score(self):
        opt = self._opt()
        result = opt.analyze_job_parallelization([])
        assert result["parallelization_score"] == 0
        assert result["total_jobs"] == 0

    def test_all_independent_jobs_score_one(self):
        opt = self._opt()
        jobs = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        result = opt.analyze_job_parallelization(jobs)
        assert result["parallelization_score"] == 1.0

    def test_sequential_jobs_counted(self):
        opt = self._opt()
        jobs = [
            {"name": "build"},
            {"name": "test", "needs": ["build"]},
        ]
        result = opt.analyze_job_parallelization(jobs)
        assert result["sequential_jobs"] == 1

    def test_many_parallel_jobs_generates_recommendation(self):
        opt = self._opt()
        jobs = [{"name": f"job_{i}"} for i in range(6)]
        result = opt.analyze_job_parallelization(jobs)
        assert len(result["recommendations"]) > 0


class TestAnalyzeResourceUsage:
    def _opt(self):
        return WorkflowOptimizer()

    def test_ubuntu_latest_has_recommendation(self):
        opt = self._opt()
        result = opt.analyze_resource_usage("ubuntu-latest")
        assert len(result["recommendations"]) > 0

    def test_result_contains_runner_type(self):
        opt = self._opt()
        result = opt.analyze_resource_usage("windows-latest")
        assert result["runner_type"] == "windows-latest"


class TestAnalyzeDependencyCaching:
    def test_returns_recommendations(self):
        opt = WorkflowOptimizer()
        result = opt.analyze_dependency_caching()
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0


class TestGenerateOptimizationReport:
    def test_returns_string_report(self):
        opt = WorkflowOptimizer()
        report = opt.generate_optimization_report()
        assert isinstance(report, str)

    def test_report_contains_sections(self):
        opt = WorkflowOptimizer()
        report = opt.generate_optimization_report()
        assert "Duration" in report
        assert "Cache" in report
        assert "Parallelization" in report
        assert "Summary" in report


class TestEstimateCostSavings:
    def _opt(self):
        return WorkflowOptimizer()

    def test_returns_savings_dict(self):
        opt = self._opt()
        result = opt.estimate_cost_savings(600, 300)
        assert "time_saved_per_run" in result
        assert "time_saved_per_month" in result
        assert "cost_saved_per_month" in result
        assert "annual_savings" in result

    def test_time_saved_per_run(self):
        opt = self._opt()
        result = opt.estimate_cost_savings(600, 300)
        assert "300s" in result["time_saved_per_run"]

    def test_annual_is_12_times_monthly(self):
        opt = self._opt()
        result = opt.estimate_cost_savings(600, 300, runs_per_day=10)
        # Extract dollar values
        monthly = float(result["cost_saved_per_month"].replace("$", ""))
        annual = float(result["annual_savings"].replace("$", ""))
        assert abs(annual - monthly * 12) < 0.01
