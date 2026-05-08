"""Unit tests for overseer/monitor.py"""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from overseer.monitor import RepositoryMonitor


def _make_monitor(tmp_path: Path, config=None):
    return RepositoryMonitor(tmp_path, config or {})


class TestRepositoryMonitorInit:
    def test_creates_with_repo_path(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        assert monitor.repo_path == tmp_path

    def test_monitoring_start_set(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        assert monitor.monitoring_start is not None


class TestMonitorCodeQuality:
    def test_returns_quality_dict(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        quality = monitor._monitor_code_quality()
        assert "test_coverage" in quality
        assert "has_linting" in quality
        assert "has_type_hints" in quality

    def test_detects_test_files(self, tmp_path):
        (tmp_path / "test_module.py").write_text("def test_foo(): pass")
        monitor = _make_monitor(tmp_path)
        quality = monitor._monitor_code_quality()
        assert quality["test_coverage"] > 0

    def test_detects_linting_config(self, tmp_path):
        (tmp_path / ".flake8").write_text("[flake8]\nmax-line-length=120\n")
        monitor = _make_monitor(tmp_path)
        quality = monitor._monitor_code_quality()
        assert quality["has_linting"] is True

    def test_no_linting_config(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        quality = monitor._monitor_code_quality()
        assert quality["has_linting"] is False

    def test_documentation_coverage_from_md_files(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project")
        monitor = _make_monitor(tmp_path)
        quality = monitor._monitor_code_quality()
        assert quality["documentation_coverage"] > 0

    def test_has_type_hints_with_python_files(self, tmp_path):
        (tmp_path / "module.py").write_text("def foo() -> int:\n    return 1\n")
        monitor = _make_monitor(tmp_path)
        quality = monitor._monitor_code_quality()
        assert quality["has_type_hints"] is True


class TestMonitorPerformance:
    def test_returns_performance_dict(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        perf = monitor._monitor_performance()
        assert "dependency_count" in perf
        assert "build_size" in perf

    def test_counts_python_dependencies(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("requests==2.28.0\nflask==2.0.0\n")
        monitor = _make_monitor(tmp_path)
        perf = monitor._monitor_performance()
        assert perf["dependency_count"] >= 2

    def test_counts_js_dependencies(self, tmp_path):
        (tmp_path / "package.json").write_text(
            json.dumps(
                {
                    "dependencies": {"lodash": "4.17.0"},
                    "devDependencies": {"jest": "27.0.0"},
                }
            )
        )
        monitor = _make_monitor(tmp_path)
        perf = monitor._monitor_performance()
        assert perf["dependency_count"] >= 2

    def test_no_deps_files_returns_zero(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        perf = monitor._monitor_performance()
        assert perf["dependency_count"] == 0


class TestMonitorSecurity:
    def test_returns_security_dict(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        security = monitor._monitor_security()
        assert "has_security_policy" in security
        assert "has_dependabot" in security
        assert "has_codeowners" in security

    def test_detects_security_policy(self, tmp_path):
        (tmp_path / "SECURITY.md").write_text("# Security Policy")
        monitor = _make_monitor(tmp_path)
        security = monitor._monitor_security()
        assert security["has_security_policy"] is True

    def test_detects_dependabot(self, tmp_path):
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "dependabot.yml").write_text("version: 2")
        monitor = _make_monitor(tmp_path)
        security = monitor._monitor_security()
        assert security["has_dependabot"] is True

    def test_detects_codeowners(self, tmp_path):
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "CODEOWNERS").write_text("* @owner")
        monitor = _make_monitor(tmp_path)
        security = monitor._monitor_security()
        assert security["has_codeowners"] is True

    def test_no_security_files_present(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        security = monitor._monitor_security()
        assert security["has_security_policy"] is False
        assert security["has_dependabot"] is False


class TestMonitorCollaboration:
    def test_returns_collaboration_dict(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        collab = monitor._monitor_collaboration()
        assert "has_contributing_guide" in collab
        assert "has_readme" in collab

    def test_detects_readme(self, tmp_path):
        (tmp_path / "README.md").write_text("# My Project")
        monitor = _make_monitor(tmp_path)
        collab = monitor._monitor_collaboration()
        assert collab["has_readme"] is True

    def test_detects_contributing_guide(self, tmp_path):
        (tmp_path / "CONTRIBUTING.md").write_text("# Contributing")
        monitor = _make_monitor(tmp_path)
        collab = monitor._monitor_collaboration()
        assert collab["has_contributing_guide"] is True

    def test_detects_issue_templates(self, tmp_path):
        templates = tmp_path / ".github" / "ISSUE_TEMPLATE"
        templates.mkdir(parents=True)
        (templates / "bug.md").write_text("# Bug Report")
        monitor = _make_monitor(tmp_path)
        collab = monitor._monitor_collaboration()
        assert collab["has_issue_templates"] is True

    def test_detects_pr_template(self, tmp_path):
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "PULL_REQUEST_TEMPLATE.md").write_text("# PR Template")
        monitor = _make_monitor(tmp_path)
        collab = monitor._monitor_collaboration()
        assert collab["has_pr_template"] is True


class TestGenerateRecommendations:
    def test_generates_recommendations_from_results(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        results = {
            "quality": {
                "test_coverage": 10,  # Low
                "has_linting": False,
                "has_type_hints": False,
                "documentation_coverage": 0,
                "code_complexity": 0,
            },
            "performance": {"dependency_count": 100, "build_size": 0},
            "security": {
                "has_security_policy": False,
                "has_dependabot": False,
                "has_codeowners": False,
                "security_workflows": [],
                "exposed_secrets": [],
            },
            "collaboration": {
                "has_contributing_guide": False,
                "has_code_of_conduct": False,
                "has_issue_templates": False,
                "has_pr_template": False,
                "has_readme": False,
            },
        }
        recs = monitor._generate_recommendations(results)
        assert isinstance(recs, list)
        assert len(recs) > 0


class TestAnalyze:
    def test_analyze_returns_dict_with_expected_keys(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        result = monitor.analyze()
        assert "quality" in result
        assert "performance" in result
        assert "security" in result
        assert "collaboration" in result
        assert "recommendations" in result
