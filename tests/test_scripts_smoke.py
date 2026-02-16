"""Smoke tests for core workflow scripts to ensure basic coverage and functionality."""
import json
import os
import runpy
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.github', 'scripts'))

import ai_agent_main
import check_policy
import docgen
import error_handler
import gather_context
import test_runner
import utils


def test_core_scripts_workflow(tmp_path, monkeypatch):
    """Run a minimal end-to-end workflow across core scripts."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Isolate environment to temporary workspace
        monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
        monkeypatch.setenv("GITHUB_REPOSITORY", "demo/repo")
        monkeypatch.setenv("GITHUB_EVENT_NAME", "dynamic")
        monkeypatch.setenv("GITHUB_REF", "refs/heads/test")
        monkeypatch.setenv("GITHUB_ACTOR", "tester")
        monkeypatch.setenv("GITHUB_WORKFLOW", "test-workflow")

        # Prepare context files for load/save paths
        context_path = tmp_path / "context.json"
        context_path.write_text(json.dumps({"repository": "demo/repo"}))
        assert ai_agent_main.load_context(context_path)["repository"] == "demo/repo"
        assert ai_agent_main.load_context(tmp_path / "missing.json") == {}

        # Gather context in an isolated workspace and via __main__
        gathered = gather_context.gather_repo_context()
        assert gathered["repository"] == os.environ.get("GITHUB_REPOSITORY", "unknown")
        with pytest.raises(SystemExit):
            runpy.run_module("gather_context", run_name="__main__")

        # Run the AI agent with the gathered context and main entrypoint
        results = ai_agent_main.run_ai_agent(gathered)
        assert results["status"] == "success"
        sys.argv = ["ai_agent_main.py", "--context", str(context_path)]
        with pytest.raises(SystemExit):
            runpy.run_module("ai_agent_main", run_name="__main__")

        # Policy check should exercise both success and warning paths plus __main__
        audit = check_policy.check_policies()
        assert audit["status"] in {"passed", "failed"}
        (tmp_path / "results.json").unlink(missing_ok=True)
        audit_with_warning = check_policy.check_policies()
        assert audit_with_warning["warnings"]
        with pytest.raises(SystemExit):
            runpy.run_module("check_policy", run_name="__main__")

        # Error handler should capture violations and __main__ execution
        (tmp_path / "audit.log").write_text(json.dumps({"violations": ["v1"], "warnings": ["w1"]}))
        (tmp_path / "results.json").write_text(json.dumps({"status": "failed"}))
        report = error_handler.handle_errors()
        assert report["errors"]
        with pytest.raises(SystemExit):
            runpy.run_module("error_handler", run_name="__main__")

        # Documentation generation produces expected artifacts and covers __main__
        assert docgen.generate_documentation() is True
        assert (tmp_path / "AUTODOC.md").exists()
        assert (tmp_path / "diagrams" / "workflow.txt").exists()
        with pytest.raises(SystemExit):
            runpy.run_module("docgen", run_name="__main__")

        # Placeholder test runner should report success and exit cleanly
        assert test_runner.run_tests() is True

        # Utility helpers and edge cases
        assert utils.save_json_file({"key": "value"}, tmp_path / "data.json")
        loaded = utils.load_json_file(tmp_path / "data.json")
        assert loaded == {"key": "value"}
        assert utils.load_json_file(tmp_path / "missing.json") is None
        invalid_json = tmp_path / "bad.json"
        invalid_json.write_text("{invalid")
        with pytest.raises(json.JSONDecodeError):
            utils.load_json_file(invalid_json)
        assert utils.get_env_variable("NON_EXISTENT_ENV") is None
        assert utils.format_file_size(1024) == "1.0 KB"
        assert utils.format_file_size(1024 * 1024) == "1.0 MB"
        found_files = utils.find_files_by_extension(tmp_path, ".json")
        assert any(f.name == "data.json" for f in found_files)
        assert utils.find_files_by_extension(tmp_path / "missing_dir", ".py") == []
        assert utils.validate_threshold(5, 3) is True
        assert utils.validate_threshold(2, 3, higher_is_better=False) is True
    finally:
        os.chdir(original_cwd)
