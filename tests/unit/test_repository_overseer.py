"""Unit tests for overseer/orchestrator.py (RepositoryOverseer)"""

from __future__ import annotations

from pathlib import Path


def _make_overseer(tmp_path: Path, config=None):
    from overseer.orchestrator import RepositoryOverseer

    return RepositoryOverseer(str(tmp_path), config)


class TestRepositoryOverseerInit:
    def test_creates_with_repo_path(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        assert overseer.repo_path == tmp_path

    def test_results_structure_initialized(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        assert "timestamp" in overseer.results
        assert "repo_path" in overseer.results
        assert "analyses" in overseer.results

    def test_default_config_loaded(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        assert "code_analysis" in overseer.config
        assert "documentation" in overseer.config
        assert "dependency_management" in overseer.config

    def test_custom_config_respected(self, tmp_path):
        config = {
            "code_analysis": {"enabled": False},
            "documentation": {"enabled": False},
            "dependency_management": {"enabled": False},
            "cicd": {"enabled": False},
            "issue_triaging": {"enabled": False},
            "automation": {"enabled": False},
            "monitoring": {"enabled": False},
        }
        overseer = _make_overseer(tmp_path, config=config)
        assert overseer.config["code_analysis"]["enabled"] is False


class TestLoadDefaultConfig:
    def test_default_config_has_all_sections(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        config = overseer._load_default_config()
        expected_keys = [
            "code_analysis",
            "documentation",
            "dependency_management",
            "cicd",
            "issue_triaging",
            "automation",
            "monitoring",
        ]
        for key in expected_keys:
            assert key in config

    def test_code_analysis_enabled_by_default(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        assert overseer.config["code_analysis"]["enabled"] is True


class TestAnalyzeCode:
    def test_code_analysis_disabled_returns_empty(self, tmp_path):
        config = _make_overseer(tmp_path)._load_default_config()
        config["code_analysis"]["enabled"] = False
        overseer = _make_overseer(tmp_path, config=config)
        result = overseer.analyze_code()
        assert result["refactoring_opportunities"] == []
        assert result["architectural_improvements"] == []

    def test_code_analysis_enabled_runs_analysis(self, tmp_path):
        (tmp_path / "module.py").write_text("def foo():\n    return 1\n")
        overseer = _make_overseer(tmp_path)
        result = overseer.analyze_code()
        assert "code_quality_score" in result

    def test_analysis_stored_in_results(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        overseer.analyze_code()
        assert "code" in overseer.results["analyses"]


class TestManageDependencies:
    def test_dependency_disabled_returns_empty(self, tmp_path):
        config = _make_overseer(tmp_path)._load_default_config()
        config["dependency_management"]["enabled"] = False
        overseer = _make_overseer(tmp_path, config=config)
        result = overseer.manage_dependencies()
        assert result["outdated_packages"] == []
        assert result["vulnerable_packages"] == []

    def test_dependency_analysis_with_requirements_file(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("requests==2.28.0\n")
        overseer = _make_overseer(tmp_path)
        result = overseer.manage_dependencies()
        assert isinstance(result["upgrade_recommendations"], list)


class TestTriageIssues:
    def test_triaging_disabled_returns_empty(self, tmp_path):
        config = _make_overseer(tmp_path)._load_default_config()
        config["issue_triaging"]["enabled"] = False
        overseer = _make_overseer(tmp_path, config=config)
        result = overseer.triage_issues()
        assert result["patterns_detected"] == []

    def test_triaging_enabled_returns_patterns(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        result = overseer.triage_issues()
        assert "patterns_detected" in result


class TestOptimizeCICD:
    def test_cicd_disabled_returns_empty(self, tmp_path):
        config = _make_overseer(tmp_path)._load_default_config()
        config["cicd"]["enabled"] = False
        overseer = _make_overseer(tmp_path, config=config)
        result = overseer.optimize_cicd()
        assert result["test_improvements"] == []
        assert result["linting_suggestions"] == []

    def test_cicd_enabled_returns_optimizations(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        result = overseer.optimize_cicd()
        assert "test_improvements" in result


class TestMonitorRepository:
    def test_monitoring_disabled_returns_empty(self, tmp_path):
        config = _make_overseer(tmp_path)._load_default_config()
        config["monitoring"]["enabled"] = False
        overseer = _make_overseer(tmp_path, config=config)
        result = overseer.monitor_repository()
        assert result["recommendations"] == []

    def test_monitoring_enabled_returns_results(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        result = overseer.monitor_repository()
        assert "recommendations" in result


class TestGenerateSummaryReport:
    def test_generate_recommendations_runs(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        overseer.analyze_code()  # Populate results
        overseer._generate_recommendations()
        assert isinstance(overseer.results["recommendations"], list)

    def test_save_results_creates_file(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        output_file = str(tmp_path / "results.json")
        overseer.save_results(output_file)
        assert Path(output_file).exists()


class TestSaveResults:
    def test_saves_results_to_file(self, tmp_path):
        overseer = _make_overseer(tmp_path)
        output_file = str(tmp_path / "results.json")
        overseer.save_results(output_file)
        import json

        data = json.loads(Path(output_file).read_text())
        assert "timestamp" in data
        assert "repo_path" in data

    def test_saves_to_default_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        overseer = _make_overseer(tmp_path)
        overseer.save_results()
        assert (tmp_path / "overseer-results.json").exists()
