"""Unit tests for overseer/cicd_optimizer.py"""

from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from overseer.cicd_optimizer import CICDOptimizer


def _make_optimizer(tmp_path: Path, config=None):
    return CICDOptimizer(tmp_path, config or {})


class TestCICDOptimizerInit:
    def test_creates_with_repo_path(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        assert opt.repo_path == tmp_path

    def test_workflows_dir_set(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        assert opt.workflows_dir == tmp_path / ".github" / "workflows"


class TestCheckForCaching:
    def test_detects_cache_step(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        workflow = {
            "jobs": {
                "build": {
                    "steps": [
                        {"uses": "actions/cache@v3", "with": {"path": "~/.cache"}},
                    ]
                }
            }
        }
        assert opt._check_for_caching(workflow) is True

    def test_no_cache_step(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        workflow = {"jobs": {"build": {"steps": [{"run": "echo hello"}]}}}
        assert opt._check_for_caching(workflow) is False

    def test_empty_workflow(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        assert opt._check_for_caching({}) is False


class TestCheckForMatrix:
    def test_detects_matrix_strategy(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        workflow = {
            "jobs": {
                "test": {"strategy": {"matrix": {"python-version": ["3.10", "3.11"]}}}
            }
        }
        assert opt._check_for_matrix(workflow) is True

    def test_no_matrix_strategy(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        workflow = {"jobs": {"test": {"steps": [{"run": "pytest"}]}}}
        assert opt._check_for_matrix(workflow) is False


class TestCheckForArtifacts:
    def test_detects_artifact_upload(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        workflow = {
            "jobs": {
                "build": {
                    "steps": [
                        {"uses": "actions/upload-artifact@v3", "with": {"name": "dist"}}
                    ]
                }
            }
        }
        assert opt._check_for_artifacts(workflow) is True

    def test_no_artifact_upload(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        workflow = {"jobs": {"build": {"steps": [{"run": "make build"}]}}}
        assert opt._check_for_artifacts(workflow) is False


class TestCheckMissingWorkflows:
    def test_detects_missing_test_workflow(self, tmp_path):
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        opt = _make_optimizer(tmp_path)
        results = {"testing": [], "linting": [], "deployment": []}
        opt._check_missing_workflows(results)
        assert any(r["type"] == "missing_test_workflow" for r in results["testing"])

    def test_no_missing_test_when_ci_exists(self, tmp_path):
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text("on: push")
        opt = _make_optimizer(tmp_path)
        results = {"testing": [], "linting": [], "deployment": []}
        opt._check_missing_workflows(results)
        assert not any(r["type"] == "missing_test_workflow" for r in results["testing"])

    def test_detects_missing_lint_workflow(self, tmp_path):
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        opt = _make_optimizer(tmp_path)
        results = {"testing": [], "linting": [], "deployment": []}
        opt._check_missing_workflows(results)
        assert any(r["type"] == "missing_lint_workflow" for r in results["linting"])


class TestAnalyze:
    def test_no_workflows_dir_returns_missing_cicd(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        result = opt.analyze()
        assert any(r["type"] == "missing_cicd" for r in result["optimizations"])

    def test_with_workflows_dir_analyzes_workflows(self, tmp_path):
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        workflow = {
            "on": "push",
            "jobs": {
                "build": {"runs-on": "ubuntu-latest", "steps": [{"run": "pytest"}]}
            },
        }
        (workflows_dir / "ci.yml").write_text(yaml.dump(workflow))
        opt = _make_optimizer(tmp_path)
        result = opt.analyze()
        assert isinstance(result, dict)
        assert "optimizations" in result

    def test_with_caching_no_cache_warning(self, tmp_path):
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        workflow = {
            "on": "push",
            "jobs": {
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": [{"uses": "actions/cache@v3", "with": {"path": "~"}}],
                }
            },
        }
        (workflows_dir / "ci.yml").write_text(yaml.dump(workflow))
        opt = _make_optimizer(tmp_path)
        result = opt.analyze()
        cache_warnings = [
            r for r in result["optimizations"] if r.get("type") == "missing_cache"
        ]
        assert cache_warnings == []


class TestAnalyzeWorkflow:
    def test_workflow_with_no_cache_flagged(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        workflow = {"jobs": {"build": {"steps": [{"run": "pytest"}]}}}
        results = {"optimizations": [], "testing": [], "linting": [], "deployment": []}
        workflow_file = tmp_path / "ci.yml"
        workflow_file.write_text(yaml.dump(workflow))
        opt._analyze_workflow(workflow_file, results)
        types = [r["type"] for r in results["optimizations"]]
        assert "missing_cache" in types

    def test_empty_workflow_file_handled(self, tmp_path):
        opt = _make_optimizer(tmp_path)
        workflow_file = tmp_path / "empty.yml"
        workflow_file.write_text("")
        results = {"optimizations": [], "testing": [], "linting": [], "deployment": []}
        opt._analyze_workflow(workflow_file, results)  # should not raise
