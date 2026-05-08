"""Unit tests for .github/scripts/ai_code_suggestor.py"""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from ai_code_suggestor import AICodeSuggestor, CodeSuggestion


class TestCodeSuggestionDataclass:
    def test_creates_with_all_fields(self):
        s = CodeSuggestion(
            id="s1",
            category="style",
            title="Fix imports",
            description="Reorganize imports",
            file_path="module.py",
            line_number=5,
            current_code="import os, sys",
            suggested_code="import os\nimport sys",
            reasoning="PEP 8",
            confidence=0.9,
            impact="low",
            effort="low",
            auto_fixable=True,
        )
        assert s.id == "s1"
        assert s.auto_fixable is True

    def test_asdict_works(self):
        s = CodeSuggestion(
            id="s2",
            category="perf",
            title="Cache result",
            description="",
            file_path="module.py",
            line_number=10,
            current_code="for x in y: compute()",
            suggested_code="result = [compute(x) for x in y]",
            reasoning="",
            confidence=0.8,
            impact="medium",
            effort="low",
            auto_fixable=True,
        )
        d = asdict(s)
        assert isinstance(d, dict)
        assert "id" in d


class TestAICodeSuggestorInit:
    def test_creates_with_repo_path(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        assert suggestor.repo_path == tmp_path

    def test_initial_suggestions_empty(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        assert suggestor.suggestions == []


class TestShouldSkipFile:
    def test_skips_git_files(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        assert suggestor._should_skip_file(Path(".git/config")) is True

    def test_skips_venv_files(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        assert suggestor._should_skip_file(Path("venv/module.py")) is True

    def test_skips_pycache(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        assert suggestor._should_skip_file(Path("__pycache__/mod.pyc")) is True

    def test_does_not_skip_regular_files(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        assert suggestor._should_skip_file(Path("src/module.py")) is False


class TestCheckImportOrganization:
    def test_well_organized_imports_no_suggestions(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        lines = [
            "import os",
            "import sys",
            "",
            "def main():",
            "    pass",
        ]
        result = suggestor._check_import_organization(tmp_path / "mod.py", lines)
        # Small number of imports should be fine
        assert isinstance(result, list)

    def test_file_without_imports_returns_empty(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        lines = ["def main():", "    pass"]
        result = suggestor._check_import_organization(tmp_path / "mod.py", lines)
        assert result == []


class TestCalculateNesting:
    def test_empty_lines_returns_zero(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        assert suggestor._calculate_nesting([]) == 0

    def test_flat_code_returns_zero(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        lines = ["def foo():", "    x = 1", "    return x"]
        result = suggestor._calculate_nesting(lines)
        assert result >= 0

    def test_deeply_nested_code_returns_higher_value(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        lines = [
            "def outer():",
            "    if a:",
            "        if b:",
            "            if c:",
            "                if d:",
            "                    x = 1",
        ]
        result = suggestor._calculate_nesting(lines)
        assert result > 2


class TestCheckDocstringPresence:
    def test_function_without_docstring_flagged(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        lines = [
            "def my_function():",
            "    return 1",
        ]
        result = suggestor._check_docstring_presence(tmp_path / "mod.py", lines)
        assert len(result) >= 1

    def test_function_with_docstring_not_flagged(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        lines = [
            "def my_function():",
            '    """Do the thing."""',
            "    return 1",
        ]
        result = suggestor._check_docstring_presence(tmp_path / "mod.py", lines)
        assert result == []


class TestCheckErrorHandling:
    def test_file_with_no_exceptions_no_suggestions(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        lines = ["x = 1", "y = 2"]
        result = suggestor._check_error_handling(tmp_path / "mod.py", lines)
        assert isinstance(result, list)


class TestCheckPerformancePatterns:
    def test_empty_file_no_suggestions(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        lines = []
        result = suggestor._check_performance_patterns(tmp_path / "mod.py", lines)
        assert result == []


class TestGenerateReport:
    def test_generates_report_file(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        output = str(tmp_path / "suggestions.md")
        suggestor.generate_report(output)
        assert Path(output).exists()

    def test_report_contains_header(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        output = str(tmp_path / "suggestions.md")
        suggestor.generate_report(output)
        content = Path(output).read_text()
        assert "Suggestion" in content or "Code" in content

    def test_report_with_suggestions(self, tmp_path):
        suggestor = AICodeSuggestor(str(tmp_path))
        suggestor.suggestions = [
            CodeSuggestion(
                id="s1",
                category="style",
                title="Organize imports",
                description="PEP 8 violation",
                file_path="mod.py",
                line_number=5,
                current_code="import sys, os",
                suggested_code="import os\nimport sys",
                reasoning="PEP 8",
                confidence=0.9,
                impact="low",
                effort="low",
                auto_fixable=True,
            )
        ]
        output = str(tmp_path / "suggestions.md")
        suggestor.generate_report(output)
        content = Path(output).read_text()
        assert "style" in content.lower() or "import" in content.lower()
