"""Unit tests for small workflow helper scripts in .github/scripts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / ".github" / "scripts"


def load_script_module(module_name: str):
    spec = importlib.util.spec_from_file_location(
        module_name, SCRIPTS_DIR / f"{module_name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ai_agent_main = load_script_module("ai_agent_main")
docgen = load_script_module("docgen")
error_handler = load_script_module("error_handler")


class TestAiAgentMain:
    def test_load_context_returns_parsed_json(self, tmp_path):
        context_file = tmp_path / "context.json"
        expected = {"repository": "owner/repo", "event_name": "push"}
        context_file.write_text(json.dumps(expected))

        assert ai_agent_main.load_context(context_file) == expected

    def test_load_context_returns_empty_dict_on_invalid_json(self, tmp_path, capsys):
        context_file = tmp_path / "context.json"
        context_file.write_text("{invalid json")

        assert ai_agent_main.load_context(context_file) == {}

        output = capsys.readouterr().out
        assert "Error loading context:" in output

    def test_run_ai_agent_writes_results_with_context_and_defaults(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        context = {
            "repository": "owner/repo",
            "event_name": "workflow_dispatch",
            "ref": "refs/heads/main",
        }

        result = ai_agent_main.run_ai_agent(context)

        assert result == {
            "status": "success",
            "agent_actions": [],
            "recommendations": [],
        }
        assert json.loads((tmp_path / "results.json").read_text()) == result

        output = capsys.readouterr().out
        assert "Repository: owner/repo" in output
        assert "Event: workflow_dispatch" in output
        assert "Ref: refs/heads/main" in output
        assert "Actor: unknown" in output

    def test_run_ai_agent_uses_explicit_actor(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)

        ai_agent_main.run_ai_agent({"actor": "octocat"})

        output = capsys.readouterr().out
        assert "Actor: octocat" in output


class TestErrorHandler:
    def test_handle_errors_returns_success_when_no_input_files_exist(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)

        report = error_handler.handle_errors()

        assert report == {
            "errors": [],
            "warnings": [],
            "status": "success",
            "branch_decision": "continue",
        }
        assert json.loads((tmp_path / "error_report.json").read_text()) == report

        output = capsys.readouterr().out
        assert "Status: success" in output
        assert "Branch decision: continue" in output

    def test_handle_errors_collects_violations_warnings_and_failed_results(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "audit.log").write_text(
            json.dumps(
                {
                    "violations": ["policy violation"],
                    "warnings": ["needs review"],
                }
            )
        )
        (tmp_path / "results.json").write_text(json.dumps({"status": "failed"}))

        report = error_handler.handle_errors()

        assert report == {
            "errors": ["policy violation", "AI agent reported non-success status"],
            "warnings": ["needs review"],
            "status": "failed",
            "branch_decision": "stop",
        }
        assert json.loads((tmp_path / "error_report.json").read_text()) == report

        output = capsys.readouterr().out
        assert "Errors: 2" in output
        assert "Warnings: 1" in output
        assert "Branch decision: stop" in output

    def test_handle_errors_keeps_success_when_only_warnings_are_present(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "audit.log").write_text(json.dumps({"warnings": ["be careful"]}))
        (tmp_path / "results.json").write_text(json.dumps({"status": "success"}))

        report = error_handler.handle_errors()

        assert report["errors"] == []
        assert report["warnings"] == ["be careful"]
        assert report["status"] == "success"
        assert report["branch_decision"] == "continue"


class TestDocgen:
    def test_generate_documentation_creates_expected_files(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)

        assert docgen.generate_documentation() is True

        autodoc = tmp_path / "AUTODOC.md"
        workflow = tmp_path / "diagrams" / "workflow.txt"

        assert autodoc.exists()
        assert workflow.exists()
        assert "Automated Documentation" in autodoc.read_text()
        assert "Workflow Diagram" in workflow.read_text()

        output = capsys.readouterr().out
        assert "Documentation generated:" in output
        assert "Diagram generated:" in output

    def test_generate_documentation_reuses_existing_diagrams_directory(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        diagrams_dir = tmp_path / "diagrams"
        diagrams_dir.mkdir()
        existing = diagrams_dir / "existing.txt"
        existing.write_text("keep me")

        docgen.generate_documentation()

        assert existing.read_text() == "keep me"
        assert (diagrams_dir / "workflow.txt").exists()
