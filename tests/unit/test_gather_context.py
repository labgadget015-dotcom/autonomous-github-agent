"""Unit tests for .github/scripts/gather_context.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from gather_context import SmartContextGatherer, ContextMode


def _make_gatherer(tmp_path):
    gatherer = SmartContextGatherer.__new__(SmartContextGatherer)
    gatherer.workspace = tmp_path
    gatherer.event_name = "push"
    gatherer.files_changed_threshold = {"minimal": 3, "standard": 10}
    return gatherer


class TestContextModeEnum:
    def test_minimal_value(self):
        assert ContextMode.MINIMAL.value == "minimal"

    def test_standard_value(self):
        assert ContextMode.STANDARD.value == "standard"

    def test_comprehensive_value(self):
        assert ContextMode.COMPREHENSIVE.value == "comprehensive"


class TestDetermineContextMode:
    def test_zero_files_returns_standard(self, tmp_path):
        g = _make_gatherer(tmp_path)
        mode = g.determine_context_mode([])
        assert mode == ContextMode.STANDARD

    def test_one_file_returns_minimal(self, tmp_path):
        g = _make_gatherer(tmp_path)
        mode = g.determine_context_mode(["file.py"])
        assert mode == ContextMode.MINIMAL

    def test_three_files_returns_minimal(self, tmp_path):
        g = _make_gatherer(tmp_path)
        mode = g.determine_context_mode(["a.py", "b.py", "c.py"])
        assert mode == ContextMode.MINIMAL

    def test_five_files_returns_standard(self, tmp_path):
        g = _make_gatherer(tmp_path)
        mode = g.determine_context_mode([f"file{i}.py" for i in range(5)])
        assert mode == ContextMode.STANDARD

    def test_eleven_files_returns_comprehensive(self, tmp_path):
        g = _make_gatherer(tmp_path)
        mode = g.determine_context_mode([f"file{i}.py" for i in range(11)])
        assert mode == ContextMode.COMPREHENSIVE

    def test_empty_strings_filtered(self, tmp_path):
        g = _make_gatherer(tmp_path)
        mode = g.determine_context_mode(["", "", ""])
        assert mode == ContextMode.STANDARD


class TestGatherMinimalContext:
    def test_returns_mode_minimal(self, tmp_path):
        g = _make_gatherer(tmp_path)
        result = g.gather_minimal_context(["a.py", "b.py"])
        assert result["mode"] == "minimal"

    def test_files_limited_to_50(self, tmp_path):
        g = _make_gatherer(tmp_path)
        files = [f"file{i}.py" for i in range(100)]
        result = g.gather_minimal_context(files)
        assert len(result["files"]) <= 50

    def test_file_count_is_total(self, tmp_path):
        g = _make_gatherer(tmp_path)
        files = ["a.py", "b.py", "c.py"]
        result = g.gather_minimal_context(files)
        assert result["file_count"] == 3


class TestGatherStandardContext:
    def test_returns_mode_standard(self, tmp_path):
        g = _make_gatherer(tmp_path)
        result = g.gather_standard_context(["a.py"])
        assert result["mode"] == "standard"

    def test_changed_files_in_result(self, tmp_path):
        g = _make_gatherer(tmp_path)
        result = g.gather_standard_context(["main.py"])
        assert "changed_files" in result
        assert "main.py" in result["changed_files"]

    def test_related_files_gathered_from_same_dir(self, tmp_path):
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "a.py").write_text("# a")
        (sub / "b.py").write_text("# b")
        g = _make_gatherer(tmp_path)
        result = g.gather_standard_context(["src/a.py"])
        assert result["related_count"] >= 1

    def test_empty_changed_files(self, tmp_path):
        g = _make_gatherer(tmp_path)
        result = g.gather_standard_context([])
        assert result["file_count"] == 0


class TestGatherComprehensiveContext:
    def test_returns_mode_comprehensive(self, tmp_path):
        g = _make_gatherer(tmp_path)
        result = g.gather_comprehensive_context()
        assert result["mode"] == "comprehensive"

    def test_finds_non_hidden_files(self, tmp_path):
        (tmp_path / "module.py").write_text("pass")
        g = _make_gatherer(tmp_path)
        result = g.gather_comprehensive_context()
        assert "module.py" in result["files"]

    def test_ignores_hidden_dirs(self, tmp_path):
        hidden = tmp_path / ".git"
        hidden.mkdir()
        (hidden / "config").write_text("")
        g = _make_gatherer(tmp_path)
        result = g.gather_comprehensive_context()
        assert not any(".git" in f for f in result["files"])

    def test_files_limited_to_200(self, tmp_path):
        for i in range(250):
            (tmp_path / f"file{i}.py").write_text("")
        g = _make_gatherer(tmp_path)
        result = g.gather_comprehensive_context()
        assert len(result["files"]) <= 200


class TestEstimateTokens:
    def test_empty_context_returns_positive(self, tmp_path):
        g = _make_gatherer(tmp_path)
        tokens = g._estimate_tokens({})
        assert tokens >= 0

    def test_larger_context_has_more_tokens(self, tmp_path):
        g = _make_gatherer(tmp_path)
        small_ctx = {"a": "b"}
        large_ctx = {"key": "value " * 1000}
        assert g._estimate_tokens(large_ctx) > g._estimate_tokens(small_ctx)
