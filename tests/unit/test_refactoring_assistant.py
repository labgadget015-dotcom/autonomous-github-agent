"""Unit tests for .github/scripts/refactoring_assistant.py"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from refactoring_assistant import RefactoringAssistant, RefactoringOpportunity


class TestRefactoringAssistantInit:
    def test_creates_with_repo_path(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        assert assistant.repo_path == tmp_path

    def test_initial_opportunities_empty(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        assert assistant.opportunities == []


class TestShouldSkip:
    def _assistant(self, tmp_path):
        return RefactoringAssistant(str(tmp_path))

    def test_skips_venv_files(self, tmp_path):
        a = self._assistant(tmp_path)
        assert a._should_skip(Path("/project/venv/lib/module.py")) is True

    def test_skips_git_files(self, tmp_path):
        a = self._assistant(tmp_path)
        assert a._should_skip(Path("/project/.git/hooks/pre-commit")) is True

    def test_skips_pycache(self, tmp_path):
        a = self._assistant(tmp_path)
        assert a._should_skip(Path("/project/__pycache__/module.pyc")) is True

    def test_does_not_skip_regular_files(self, tmp_path):
        a = self._assistant(tmp_path)
        assert a._should_skip(Path("/project/src/module.py")) is False


class TestFindLongMethods:
    def _make_long_function_code(self, num_lines: int) -> str:
        lines = ["def big_func():"]
        for i in range(num_lines):
            lines.append(f"    x_{i} = {i}")
        return "\n".join(lines)

    def test_short_function_not_flagged(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        code = "def small():\n    return 1\n"
        tree = ast.parse(code)
        opps = assistant._find_long_methods(tmp_path / "mod.py", tree, code)
        assert opps == []

    def test_long_function_flagged(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        code = self._make_long_function_code(60)
        tree = ast.parse(code)
        opps = assistant._find_long_methods(tmp_path / "mod.py", tree, code)
        assert len(opps) >= 1
        assert opps[0].type == "extract_method"

    def test_opportunity_has_correct_file_path(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        code = self._make_long_function_code(60)
        tree = ast.parse(code)
        py_file = tmp_path / "mod.py"
        opps = assistant._find_long_methods(py_file, tree, code)
        assert str(py_file) in opps[0].file_path


class TestFindDuplicateCode:
    def test_no_duplicates_in_unique_code(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        code = "\n".join(f"line_{i} = {i}" for i in range(20))
        opps = assistant._find_duplicate_code(tmp_path / "mod.py", code)
        assert opps == []

    def test_detects_duplicate_block(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        block = "\n".join(f"    result = some_function_{i}()" for i in range(6))
        code = f"def func_a():\n{block}\n\ndef func_b():\n{block}\n"
        opps = assistant._find_duplicate_code(tmp_path / "mod.py", code)
        assert len(opps) >= 1
        assert opps[0].type == "remove_duplication"


class TestFindComplexConditionals:
    def test_simple_if_not_flagged(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        code = "if x:\n    pass\n"
        tree = ast.parse(code)
        opps = assistant._find_complex_conditionals(tmp_path / "mod.py", tree, code)
        assert opps == []

    def test_complex_conditional_flagged(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        code = "if (a and b and c) or (d and e and f) or (g and h):\n    pass\n"
        tree = ast.parse(code)
        opps = assistant._find_complex_conditionals(tmp_path / "mod.py", tree, code)
        assert len(opps) >= 1
        assert opps[0].type == "simplify"


class TestCalculateConditionComplexity:
    def test_simple_compare_is_one(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        node = ast.parse("a > 0").body[0].value
        complexity = assistant._calculate_condition_complexity(node)
        assert complexity == 1

    def test_bool_op_adds_complexity(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        # BoolOp with 3 values (a and b and c) gives complexity > 0
        node = ast.parse("a and b and c").body[0].value
        complexity = assistant._calculate_condition_complexity(node)
        assert complexity >= 1  # BoolOp itself adds complexity

    def test_not_adds_complexity(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        node = ast.parse("not x").body[0].value
        complexity = assistant._calculate_condition_complexity(node)
        assert complexity > 0


class TestAnalyzeFile:
    def test_analyzes_valid_python_file(self, tmp_path):
        py_file = tmp_path / "module.py"
        py_file.write_text("def foo():\n    return 1\n")
        assistant = RefactoringAssistant(str(tmp_path))
        opps = assistant._analyze_file(py_file)
        assert isinstance(opps, list)

    def test_handles_syntax_error_gracefully(self, tmp_path):
        py_file = tmp_path / "bad.py"
        py_file.write_text("def broken(:\n    pass\n")
        assistant = RefactoringAssistant(str(tmp_path))
        opps = assistant._analyze_file(py_file)
        assert opps == []


class TestGenerateReport:
    def test_generates_report_file(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        output = str(tmp_path / "report.md")
        assistant.generate_report(output)
        assert Path(output).exists()

    def test_report_contains_header(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        output = str(tmp_path / "report.md")
        assistant.generate_report(output)
        content = Path(output).read_text()
        assert "Refactoring" in content

    def test_report_with_opportunities(self, tmp_path):
        assistant = RefactoringAssistant(str(tmp_path))
        assistant.opportunities = [
            RefactoringOpportunity(
                id="opp1",
                type="extract_method",
                title="Extract big method",
                description="Method is too long",
                file_path="src/module.py",
                line_range=(10, 80),
                confidence=0.9,
                impact="high",
                complexity_before=70,
                complexity_after=35,
                auto_applicable=False,
            )
        ]
        output = str(tmp_path / "report.md")
        assistant.generate_report(output)
        content = Path(output).read_text()
        assert "extract_method" in content or "Extract" in content
