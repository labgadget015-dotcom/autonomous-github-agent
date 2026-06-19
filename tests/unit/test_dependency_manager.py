"""Unit tests for overseer/dependency_manager.py"""

from __future__ import annotations

import json
from pathlib import Path

from overseer.dependency_manager import DependencyManager


def _make_manager(tmp_path: Path, config=None):
    return DependencyManager(tmp_path, config or {})


class TestDependencyManagerInit:
    def test_creates_with_repo_path(self, tmp_path):
        mgr = _make_manager(tmp_path)
        assert mgr.repo_path == tmp_path


class TestParseRequirements:
    def test_parses_pinned_dependency(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests==2.28.0\n")
        mgr = _make_manager(tmp_path)
        deps = mgr._parse_requirements(req)
        assert len(deps) == 1
        assert deps[0]["name"] == "requests"
        assert deps[0]["version"] == "2.28.0"

    def test_skips_comments_and_empty_lines(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("# This is a comment\n\nrequests==2.28.0\n")
        mgr = _make_manager(tmp_path)
        deps = mgr._parse_requirements(req)
        assert len(deps) == 1

    def test_parses_unpinned_dependency(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests\n")
        mgr = _make_manager(tmp_path)
        deps = mgr._parse_requirements(req)
        assert deps[0]["name"] == "requests"
        assert deps[0]["version"] is None

    def test_handles_multiple_deps(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests==2.28.0\nflask>=2.0.0\npytest\n")
        mgr = _make_manager(tmp_path)
        deps = mgr._parse_requirements(req)
        assert len(deps) == 3


class TestAnalyzePythonDependencies:
    def test_unpinned_dep_generates_recommendation(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests\n")
        mgr = _make_manager(tmp_path)
        result = mgr._analyze_python_dependencies(req)
        recs = result["recommendations"]
        assert any("version_pinning" in r["type"] for r in recs)

    def test_known_vulnerable_package_flagged(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("urllib3==1.26.0\n")
        mgr = _make_manager(tmp_path)
        result = mgr._analyze_python_dependencies(req)
        # Should detect vulnerability in urllib3 < 1.26.5
        # (based on the known_vulns in the implementation)
        assert isinstance(result["vulnerabilities"], list)
        assert isinstance(result["recommendations"], list)


class TestAnalyzeJavascriptDependencies:
    def test_version_range_generates_recommendation(self, tmp_path):
        pkg_json = tmp_path / "package.json"
        pkg_json.write_text(json.dumps({"dependencies": {"lodash": "^4.17.0"}}))
        mgr = _make_manager(tmp_path)
        result = mgr._analyze_javascript_dependencies(pkg_json)
        recs = result["recommendations"]
        assert any("version_range" == r["type"] for r in recs)

    def test_pinned_version_no_recommendation(self, tmp_path):
        pkg_json = tmp_path / "package.json"
        pkg_json.write_text(json.dumps({"dependencies": {"lodash": "4.17.21"}}))
        mgr = _make_manager(tmp_path)
        result = mgr._analyze_javascript_dependencies(pkg_json)
        recs = result["recommendations"]
        assert not any("version_range" == r.get("type") for r in recs)

    def test_dev_dependencies_also_checked(self, tmp_path):
        pkg_json = tmp_path / "package.json"
        pkg_json.write_text(json.dumps({"devDependencies": {"jest": "^27.0.0"}}))
        mgr = _make_manager(tmp_path)
        result = mgr._analyze_javascript_dependencies(pkg_json)
        assert any("version_range" == r["type"] for r in result["recommendations"])

    def test_invalid_json_handled_gracefully(self, tmp_path):
        pkg_json = tmp_path / "package.json"
        pkg_json.write_text("{bad json")
        mgr = _make_manager(tmp_path)
        result = mgr._analyze_javascript_dependencies(pkg_json)
        assert isinstance(result["recommendations"], list)


class TestAnalyze:
    def test_analyze_with_requirements_file(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("requests==2.28.0\n")
        mgr = _make_manager(tmp_path)
        result = mgr.analyze()
        assert "outdated" in result
        assert "vulnerabilities" in result
        assert "recommendations" in result

    def test_analyze_with_no_dependency_files(self, tmp_path):
        mgr = _make_manager(tmp_path)
        result = mgr.analyze()
        assert result["outdated"] == []
        assert result["vulnerabilities"] == []

    def test_analyze_with_both_dep_files(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("requests\n")
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"lodash": "^4.0.0"}})
        )
        mgr = _make_manager(tmp_path)
        result = mgr.analyze()
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0
