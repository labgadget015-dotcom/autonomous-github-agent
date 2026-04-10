"""Unit tests for overseer/code_analyzer.py"""

from __future__ import annotations

import ast
import pytest
from pathlib import Path

from overseer.code_analyzer import CodeAnalyzer


def _make_analyzer(tmp_path: Path, config=None):
    return CodeAnalyzer(tmp_path, config or {})


class TestCodeAnalyzerInit:
    def test_creates_with_repo_path(self, tmp_path):
        analyzer = _make_analyzer(tmp_path)
        assert analyzer.repo_path == tmp_path

    def test_initial_results_structure(self, tmp_path):
        analyzer = _make_analyzer(tmp_path)
        assert "refactoring" in analyzer.results
        assert "architecture" in analyzer.results
        assert "performance" in analyzer.results
        assert "quality_score" in analyzer.results
        assert analyzer.results["quality_score"] == 100


class TestFindPythonFiles:
    def test_finds_py_files(self, tmp_path):
        (tmp_path / "module.py").write_text("x = 1")
        (tmp_path / "README.md").write_text("# Docs")
        analyzer = _make_analyzer(tmp_path)
        files = analyzer._find_python_files()
        assert any(f.name == "module.py" for f in files)
        assert all(f.suffix == ".py" for f in files)

    def test_excludes_venv_dir(self, tmp_path):
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "setup.py").write_text("")
        analyzer = _make_analyzer(tmp_path)
        files = analyzer._find_python_files()
        assert not any(".venv" in str(f) for f in files)

    def test_excludes_pycache(self, tmp_path):
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "mod.cpython-39.pyc").write_text("")
        analyzer = _make_analyzer(tmp_path)
        files = analyzer._find_python_files()
        assert not any("__pycache__" in str(f) for f in files)

    def test_finds_nested_files(self, tmp_path):
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "app.py").write_text("pass")
        analyzer = _make_analyzer(tmp_path)
        files = analyzer._find_python_files()
        assert any(f.name == "app.py" for f in files)

    def test_empty_dir_returns_empty_list(self, tmp_path):
        analyzer = _make_analyzer(tmp_path)
        files = analyzer._find_python_files()
        assert files == []


class TestDetectLongFunctions:
    def _make_long_function(self, num_lines: int) -> str:
        lines = ["def long_func():"]
        for i in range(num_lines):
            lines.append(f"    x_{i} = {i}")
        return "\n".join(lines)

    def test_short_function_not_flagged(self, tmp_path):
        code = "def short():\n    return 1\n"
        py_file = tmp_path / "mod.py"
        py_file.write_text(code)
        analyzer = _make_analyzer(tmp_path)
        tree = ast.parse(code)
        analyzer._detect_long_functions(tree, py_file)
        long_func_issues = [r for r in analyzer.results["refactoring"] if r["type"] == "long_function"]
        assert long_func_issues == []

    def test_long_function_flagged(self, tmp_path):
        code = self._make_long_function(60)
        py_file = tmp_path / "mod.py"
        py_file.write_text(code)
        analyzer = _make_analyzer(tmp_path)
        tree = ast.parse(code)
        analyzer._detect_long_functions(tree, py_file)
        long_func_issues = [r for r in analyzer.results["refactoring"] if r["type"] == "long_function"]
        assert len(long_func_issues) >= 1

    def test_very_long_function_has_high_severity(self, tmp_path):
        code = self._make_long_function(110)
        py_file = tmp_path / "mod.py"
        py_file.write_text(code)
        analyzer = _make_analyzer(tmp_path)
        tree = ast.parse(code)
        analyzer._detect_long_functions(tree, py_file)
        issues = [r for r in analyzer.results["refactoring"] if r["type"] == "long_function"]
        assert any(r["severity"] == "high" for r in issues)


class TestDetectCodeDuplication:
    def test_no_duplication_in_unique_code(self, tmp_path):
        code = "\n".join(f"line_{i} = {i}" for i in range(20))
        py_file = tmp_path / "mod.py"
        py_file.write_text(code)
        analyzer = _make_analyzer(tmp_path)
        analyzer._detect_code_duplication(code, py_file)
        dup_issues = [r for r in analyzer.results["refactoring"] if r["type"] == "code_duplication"]
        assert dup_issues == []

    def test_detects_duplicated_block(self, tmp_path):
        # A block of lines that repeats exactly
        block = "\n".join(f"    some_var_{i} = some_func_{i}()" for i in range(6))
        code = f"def a():\n{block}\n\ndef b():\n{block}\n"
        py_file = tmp_path / "mod.py"
        py_file.write_text(code)
        analyzer = _make_analyzer(tmp_path)
        analyzer._detect_code_duplication(code, py_file)
        dup_issues = [r for r in analyzer.results["refactoring"] if r["type"] == "code_duplication"]
        assert len(dup_issues) >= 1


class TestDetectComplexConditionals:
    def test_simple_if_not_flagged(self, tmp_path):
        code = "if x:\n    pass\n"
        py_file = tmp_path / "mod.py"
        py_file.write_text(code)
        analyzer = _make_analyzer(tmp_path)
        tree = ast.parse(code)
        analyzer._detect_complex_conditionals(tree, py_file)
        issues = [r for r in analyzer.results["refactoring"] if r["type"] == "complex_conditional"]
        assert issues == []

    def test_complex_conditional_flagged(self, tmp_path):
        # Use nested boolean conditions to exceed threshold of 3
        code = "if (a > 0 and b < 10) or (c == 5 and d != 0) or (e >= 3 and f <= 7) or (g == h):\n    pass\n"
        py_file = tmp_path / "mod.py"
        py_file.write_text(code)
        analyzer = _make_analyzer(tmp_path)
        tree = ast.parse(code)
        analyzer._detect_complex_conditionals(tree, py_file)
        issues = [r for r in analyzer.results["refactoring"] if r["type"] == "complex_conditional"]
        assert len(issues) >= 1


class TestCountBooleanOps:
    def test_simple_condition(self, tmp_path):
        analyzer = _make_analyzer(tmp_path)
        node = ast.parse("a").body[0].value
        count = analyzer._count_boolean_ops(node)
        assert count == 0

    def test_and_condition_counted(self, tmp_path):
        analyzer = _make_analyzer(tmp_path)
        code = "a and b and c"
        node = ast.parse(code).body[0].value
        count = analyzer._count_boolean_ops(node)
        assert count >= 1


class TestDetectMagicNumbers:
    def test_literal_42_flagged(self, tmp_path):
        code = "x = 42\n"
        py_file = tmp_path / "mod.py"
        py_file.write_text(code)
        analyzer = _make_analyzer(tmp_path)
        tree = ast.parse(code)
        analyzer._detect_magic_numbers(tree, py_file)
        issues = [r for r in analyzer.results["refactoring"] if r["type"] == "magic_number"]
        assert len(issues) >= 1

    def test_zero_and_one_not_flagged(self, tmp_path):
        code = "x = 0\ny = 1\nz = -1\n"
        py_file = tmp_path / "mod.py"
        py_file.write_text(code)
        analyzer = _make_analyzer(tmp_path)
        tree = ast.parse(code)
        analyzer._detect_magic_numbers(tree, py_file)
        issues = [r for r in analyzer.results["refactoring"] if r["type"] == "magic_number"]
        assert issues == []


class TestAnalyzeFile:
    def test_analyze_valid_python_file(self, tmp_path):
        py_file = tmp_path / "app.py"
        py_file.write_text("x = 1\n\ndef simple():\n    return True\n")
        analyzer = _make_analyzer(tmp_path)
        analyzer._analyze_file(py_file)  # should not raise

    def test_analyze_file_with_syntax_error(self, tmp_path):
        py_file = tmp_path / "bad.py"
        py_file.write_text("def broken(:\n    pass\n")
        analyzer = _make_analyzer(tmp_path)
        analyzer._analyze_file(py_file)  # should handle gracefully


class TestAnalyze:
    def test_analyze_empty_dir(self, tmp_path):
        analyzer = _make_analyzer(tmp_path)
        result = analyzer.analyze()
        assert isinstance(result, dict)
        assert "quality_score" in result

    def test_analyze_with_python_files(self, tmp_path):
        (tmp_path / "module.py").write_text("def foo():\n    return 1\n")
        analyzer = _make_analyzer(tmp_path)
        result = analyzer.analyze()
        assert isinstance(result, dict)
