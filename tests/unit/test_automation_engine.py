"""Unit tests for overseer/automation_engine.py"""

from __future__ import annotations

import pytest
from pathlib import Path

from overseer.automation_engine import AutomationEngine


def _make_engine(tmp_path: Path, config=None):
    return AutomationEngine(tmp_path, config or {})


class TestAutomationEngineInit:
    def test_creates_with_repo_path(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.repo_path == tmp_path

    def test_scripts_dir_set(self, tmp_path):
        engine = _make_engine(tmp_path)
        assert engine.scripts_dir == tmp_path / "scripts" / "automation"


class TestGenerate:
    def test_generate_returns_dict(self, tmp_path):
        engine = _make_engine(tmp_path)
        result = engine.generate()
        assert isinstance(result, dict)
        assert "formatting" in result
        assert "release" in result
        assert "setup" in result

    def test_no_scripts_when_config_disabled(self, tmp_path):
        config = {
            "automation": {
                "code_formatting": False,
                "release_tagging": False,
                "environment_setup": False,
            }
        }
        engine = _make_engine(tmp_path, config=config)
        result = engine.generate()
        assert result["formatting"] == []
        assert result["release"] == []
        assert result["setup"] == []

    def test_creates_scripts_directory(self, tmp_path):
        engine = _make_engine(tmp_path)
        engine.generate()
        assert (tmp_path / "scripts" / "automation").exists()

    def test_formatting_scripts_when_enabled(self, tmp_path):
        config = {"automation": {"code_formatting": True}}
        engine = _make_engine(tmp_path, config=config)
        result = engine.generate()
        assert isinstance(result["formatting"], list)

    def test_release_scripts_when_enabled(self, tmp_path):
        config = {"automation": {"release_tagging": True}}
        engine = _make_engine(tmp_path, config=config)
        result = engine.generate()
        assert isinstance(result["release"], list)

    def test_setup_scripts_when_enabled(self, tmp_path):
        config = {"automation": {"environment_setup": True}}
        engine = _make_engine(tmp_path, config=config)
        result = engine.generate()
        assert isinstance(result["setup"], list)


class TestGenerateFormattingScripts:
    def test_returns_list(self, tmp_path):
        engine = _make_engine(tmp_path)
        scripts = engine._generate_formatting_scripts()
        assert isinstance(scripts, list)

    def test_scripts_contain_py_formatter(self, tmp_path):
        engine = _make_engine(tmp_path)
        scripts = engine._generate_formatting_scripts()
        if scripts:
            assert any(
                "format" in s.lower() or "black" in s.lower() or "py" in s.lower()
                for s in scripts
            )


class TestGenerateReleaseScripts:
    def test_returns_list(self, tmp_path):
        engine = _make_engine(tmp_path)
        # Need scripts dir to exist first
        engine.scripts_dir.mkdir(parents=True, exist_ok=True)
        scripts = engine._generate_release_scripts()
        assert isinstance(scripts, list)


class TestGenerateSetupScripts:
    def test_returns_list(self, tmp_path):
        engine = _make_engine(tmp_path)
        engine.scripts_dir.mkdir(parents=True, exist_ok=True)
        scripts = engine._generate_setup_scripts()
        assert isinstance(scripts, list)

    def test_setup_script_with_requirements_file(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("requests\n")
        engine = _make_engine(tmp_path)
        engine.scripts_dir.mkdir(parents=True, exist_ok=True)
        scripts = engine._generate_setup_scripts()
        assert isinstance(scripts, list)
