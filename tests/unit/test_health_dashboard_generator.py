"""Unit tests for .github/scripts/health_dashboard_generator.py"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from health_dashboard_generator import HealthDashboardGenerator


def _make_gen(metrics=None):
    gen = HealthDashboardGenerator()
    if metrics is not None:
        gen.metrics = metrics
    return gen


class TestHealthDashboardGeneratorInit:
    def test_creates_empty_metrics(self):
        gen = HealthDashboardGenerator()
        assert gen.metrics == {}

    def test_timestamp_set(self):
        gen = HealthDashboardGenerator()
        assert isinstance(gen.timestamp, str)
        assert len(gen.timestamp) > 0


class TestCalculateHealthScore:
    def test_perfect_score_with_no_issues(self):
        gen = _make_gen({
            "analysis": {"passed": True},
            "coverage": {"totals": {"percent_covered": 95}},
            "security": {"results": []},
            "violations": {"violations": []},
        })
        score = gen.calculate_health_score()
        assert score == 100

    def test_penalty_for_failed_analysis(self):
        gen = _make_gen({
            "analysis": {"passed": False},
            "coverage": {"totals": {"percent_covered": 95}},
            "security": {"results": []},
            "violations": {"violations": []},
        })
        score = gen.calculate_health_score()
        assert score == 80  # 100 - 20

    def test_penalty_for_low_coverage(self):
        gen = _make_gen({
            "analysis": {"passed": True},
            "coverage": {"totals": {"percent_covered": 50}},
            "security": {"results": []},
            "violations": {"violations": []},
        })
        score = gen.calculate_health_score()
        assert score < 100

    def test_penalty_for_security_issues(self):
        gen = _make_gen({
            "analysis": {"passed": True},
            "coverage": {"totals": {"percent_covered": 95}},
            "security": {"results": [{"issue_severity": "HIGH"}]},
            "violations": {"violations": []},
        })
        score = gen.calculate_health_score()
        assert score == 90  # 100 - 10

    def test_penalty_for_medium_security(self):
        gen = _make_gen({
            "analysis": {"passed": True},
            "coverage": {"totals": {"percent_covered": 95}},
            "security": {"results": [{"issue_severity": "MEDIUM"}]},
            "violations": {"violations": []},
        })
        score = gen.calculate_health_score()
        assert score == 95  # 100 - 5

    def test_penalty_for_critical_violations(self):
        gen = _make_gen({
            "analysis": {"passed": True},
            "coverage": {"totals": {"percent_covered": 95}},
            "security": {"results": []},
            "violations": {"violations": [{"severity": "critical"}]},
        })
        score = gen.calculate_health_score()
        assert score == 95  # 100 - 5

    def test_score_clamped_to_zero(self):
        gen = _make_gen({
            "analysis": {"passed": False},
            "coverage": {"totals": {"percent_covered": 0}},
            "security": {"results": [{"issue_severity": "HIGH"}] * 10},
            "violations": {"violations": [{"severity": "critical"}] * 10},
        })
        score = gen.calculate_health_score()
        assert score == 0

    def test_score_clamped_to_hundred(self):
        gen = _make_gen({})
        score = gen.calculate_health_score()
        assert score == 100


class TestGetHealthStatus:
    def _gen(self):
        return HealthDashboardGenerator()

    def test_90_plus_is_excellent(self):
        gen = self._gen()
        status, emoji = gen.get_health_status(95)
        assert status == "Excellent"
        assert "🟢" in emoji

    def test_75_to_89_is_good(self):
        gen = self._gen()
        status, emoji = gen.get_health_status(80)
        assert status == "Good"

    def test_60_to_74_is_fair(self):
        gen = self._gen()
        status, emoji = gen.get_health_status(65)
        assert status == "Fair"

    def test_below_60_is_poor(self):
        gen = self._gen()
        status, emoji = gen.get_health_status(40)
        assert status == "Poor"
        assert "🔴" in emoji


class TestGenerateQuickStats:
    def test_generates_stats_table(self):
        gen = _make_gen({
            "coverage": {"totals": {"percent_covered": 85}},
            "analysis": {"passed": True},
            "security": {"results": []},
            "violations": {"violations": []},
        })
        stats = gen._generate_quick_stats()
        assert "Metric" in stats
        assert "Coverage" in stats
        assert "85.0%" in stats

    def test_failed_analysis_shows_failed(self):
        gen = _make_gen({
            "coverage": {},
            "analysis": {"passed": False},
            "security": {},
            "violations": {},
        })
        stats = gen._generate_quick_stats()
        assert "Failed" in stats

    def test_security_issues_count_shown(self):
        gen = _make_gen({
            "coverage": {},
            "analysis": {},
            "security": {"results": [{"issue_severity": "HIGH"}, {"issue_severity": "MEDIUM"}]},
            "violations": {},
        })
        stats = gen._generate_quick_stats()
        assert "2" in stats


class TestGenerateCoverageSection:
    def test_no_coverage_data_shows_message(self):
        gen = _make_gen({"coverage": {}})
        section = gen._generate_coverage_section()
        assert "No coverage data" in section

    def test_coverage_section_with_data(self):
        gen = _make_gen({
            "coverage": {
                "totals": {
                    "percent_covered": 87.5,
                    "covered_lines": 350,
                    "num_statements": 400,
                    "covered_branches": 100,
                    "num_branches": 120,
                    "covered_functions": 50,
                    "num_functions": 55,
                }
            }
        })
        section = gen._generate_coverage_section()
        assert "87.50%" in section
        assert "Test Coverage" in section


class TestGenerateQualitySection:
    def test_no_analysis_data_shows_message(self):
        gen = _make_gen({"analysis": {}})
        section = gen._generate_quality_section()
        assert "No analysis data" in section

    def test_quality_section_with_data(self):
        gen = _make_gen({
            "analysis": {
                "passed": True,
                "elapsed_seconds": 5.5,
                "tools": {
                    "pylint": {"status": "passed"},
                    "flake8": {"status": "failed"},
                }
            }
        })
        section = gen._generate_quality_section()
        assert "Passed" in section
        assert "pylint" in section.lower() or "PYLINT" in section


class TestLoadMethods:
    def test_load_analysis_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        gen = HealthDashboardGenerator()
        result = gen.load_analysis_results()
        assert result == {}

    def test_load_coverage_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        gen = HealthDashboardGenerator()
        result = gen.load_coverage_data()
        assert result == {}

    def test_load_security_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        gen = HealthDashboardGenerator()
        result = gen.load_security_data()
        assert result == {}

    def test_load_violations_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        gen = HealthDashboardGenerator()
        result = gen.load_violations()
        assert result == {}

    def test_load_complexity_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        gen = HealthDashboardGenerator()
        result = gen.load_complexity_data()
        assert result == {}
