"""Unit tests for .github/scripts/cost_calculator.py"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from cost_calculator import CostCalculator


class TestCostCalculatorInit:
    def test_default_account_type_is_free(self, monkeypatch):
        monkeypatch.delenv("GITHUB_ACCOUNT_TYPE", raising=False)
        calc = CostCalculator()
        assert calc.account_type == "free"

    def test_account_type_from_env(self, monkeypatch):
        monkeypatch.setenv("GITHUB_ACCOUNT_TYPE", "PRO")
        calc = CostCalculator()
        assert calc.account_type == "pro"


class TestCalculateRunCost:
    def _calc(self):
        return CostCalculator()

    def test_ubuntu_runner_cost(self):
        calc = self._calc()
        # 60 seconds = 1 minute * $0.008
        cost = calc.calculate_run_cost(60, "ubuntu", 1)
        assert abs(cost - 0.008) < 1e-6

    def test_windows_runner_costs_more(self):
        calc = self._calc()
        ubuntu_cost = calc.calculate_run_cost(300, "ubuntu")
        windows_cost = calc.calculate_run_cost(300, "windows")
        assert windows_cost > ubuntu_cost

    def test_macos_runner_is_most_expensive(self):
        calc = self._calc()
        ubuntu = calc.calculate_run_cost(300, "ubuntu")
        macos = calc.calculate_run_cost(300, "macos")
        assert macos > ubuntu

    def test_multiple_jobs_multiplies_cost(self):
        calc = self._calc()
        single = calc.calculate_run_cost(300, "ubuntu", 1)
        triple = calc.calculate_run_cost(300, "ubuntu", 3)
        assert abs(triple - single * 3) < 1e-9

    def test_unknown_runner_uses_ubuntu_pricing(self):
        calc = self._calc()
        ubuntu = calc.calculate_run_cost(300, "ubuntu")
        unknown = calc.calculate_run_cost(300, "custom-runner")
        assert abs(ubuntu - unknown) < 1e-9

    def test_zero_duration_costs_zero(self):
        calc = self._calc()
        assert calc.calculate_run_cost(0) == 0.0


class TestCalculateDailyCost:
    def test_returns_all_expected_keys(self):
        calc = CostCalculator()
        costs = calc.calculate_daily_cost(runs_per_day=5)
        assert "single_run" in costs
        assert "daily" in costs
        assert "weekly" in costs
        assert "monthly" in costs
        assert "annual" in costs

    def test_weekly_is_seven_times_daily(self):
        calc = CostCalculator()
        costs = calc.calculate_daily_cost(runs_per_day=10)
        assert abs(costs["weekly"] - costs["daily"] * 7) < 1e-9

    def test_more_runs_per_day_increases_cost(self):
        calc = CostCalculator()
        low = calc.calculate_daily_cost(runs_per_day=5)
        high = calc.calculate_daily_cost(runs_per_day=50)
        assert high["daily"] > low["daily"]


class TestCalculateOptimizationSavings:
    def test_savings_structure(self):
        calc = CostCalculator()
        result = calc.calculate_optimization_savings(600, 300, runs_per_day=10)
        assert "time_saved_per_run_minutes" in result
        assert "cost_saved_per_run" in result
        assert "daily_savings" in result
        assert "monthly_savings" in result
        assert "annual_savings" in result
        assert "percentage_improvement" in result

    def test_positive_savings_when_new_is_faster(self):
        calc = CostCalculator()
        result = calc.calculate_optimization_savings(600, 300)
        assert result["cost_saved_per_run"] > 0
        assert result["time_saved_per_run_minutes"] == 5.0

    def test_percentage_improvement_calculated_correctly(self):
        calc = CostCalculator()
        # old=600, new=300 → 50% improvement
        result = calc.calculate_optimization_savings(600, 300)
        assert abs(result["percentage_improvement"] - 50.0) < 1e-6

    def test_monthly_savings_is_30_times_daily(self):
        calc = CostCalculator()
        result = calc.calculate_optimization_savings(600, 300, runs_per_day=10)
        expected_monthly = result["cost_saved_per_run"] * 10 * 30
        assert abs(result["monthly_savings"] - expected_monthly) < 1e-9


class TestCheckFreeTierUsage:
    def test_within_free_tier(self, monkeypatch):
        monkeypatch.delenv("GITHUB_ACCOUNT_TYPE", raising=False)
        calc = CostCalculator()
        result = calc.check_free_tier_usage(1000)  # free tier = 2000 min
        assert result["within_free_tier"] is True
        assert result["overage_minutes"] == 0
        assert result["remaining_minutes"] == 1000

    def test_exceeds_free_tier(self, monkeypatch):
        monkeypatch.delenv("GITHUB_ACCOUNT_TYPE", raising=False)
        calc = CostCalculator()
        result = calc.check_free_tier_usage(3000)  # exceeds 2000 min free tier
        assert result["within_free_tier"] is False
        assert result["overage_minutes"] == 1000

    def test_overage_cost_calculated(self, monkeypatch):
        monkeypatch.delenv("GITHUB_ACCOUNT_TYPE", raising=False)
        calc = CostCalculator()
        result = calc.check_free_tier_usage(2500)
        # 500 overage minutes * $0.008/min
        expected = 500 * calc.PRICING["ubuntu"]
        assert abs(result["overage_cost"] - expected) < 1e-9

    def test_unknown_account_type_has_zero_free_minutes(self, monkeypatch):
        monkeypatch.setenv("GITHUB_ACCOUNT_TYPE", "unknown")
        calc = CostCalculator()
        result = calc.check_free_tier_usage(100)
        assert result["free_tier_minutes"] == 0
        assert result["overage_minutes"] == 100


class TestGenerateCostReport:
    def test_report_is_string(self):
        calc = CostCalculator()
        report = calc.generate_cost_report()
        assert isinstance(report, str)

    def test_report_contains_cost_section(self):
        calc = CostCalculator()
        report = calc.generate_cost_report()
        assert "Cost" in report

    def test_report_with_overage(self, monkeypatch):
        monkeypatch.delenv("GITHUB_ACCOUNT_TYPE", raising=False)
        calc = CostCalculator()
        # 100 runs/day * 300s = 500 min/day * 30 = 15000 min/month (exceeds free 2000)
        report = calc.generate_cost_report(runs_per_day=100, avg_duration_seconds=300)
        assert "Exceeds" in report or "exceeds" in report or "Overage" in report


class TestLoadWorkflowData:
    def test_load_nonexistent_file_is_noop(self, tmp_path):
        calc = CostCalculator()
        calc.load_workflow_data(str(tmp_path / "missing.json"))
        # workflow_data should remain empty
        assert calc.workflow_data == []

    def test_load_valid_file(self, tmp_path):
        import json

        data_file = tmp_path / "runs.json"
        data_file.write_text(json.dumps([{"id": 1}, {"id": 2}]))
        calc = CostCalculator()
        calc.load_workflow_data(str(data_file))
        assert len(calc.workflow_data) == 2
