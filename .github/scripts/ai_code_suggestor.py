#!/usr/bin/env python3
"""
AI-Powered Code Suggestions Module

Provides intelligent code suggestions based on:
- Repository patterns and conventions
- Best practices analysis
- Historical changes
- Common patterns across files
- Performance optimization opportunities
"""

import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class CodeSuggestion:
    """Represents a code suggestion"""

    id: str
    category: str  # refactoring, performance, security, style, documentation
    title: str
    description: str
    file_path: str
    line_number: int
    current_code: str
    suggested_code: str
    reasoning: str
    confidence: float  # 0.0 to 1.0
    impact: str  # low, medium, high
    effort: str  # low, medium, high
    auto_fixable: bool


class AICodeSuggestor:
    """
    AI-Powered Code Suggestion Engine

    Analyzes code and provides intelligent suggestions for improvements
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.suggestions = []
        self.patterns_learned = {}

    def analyze_repository(self) -> list[CodeSuggestion]:
        """Analyze repository and generate code suggestions"""
        print("🔍 Analyzing repository for improvement opportunities...")

        # Analyze Python files
        python_files = list(self.repo_path.rglob("*.py"))
        print(f"   Found {len(python_files)} Python files")

        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue

            try:
                suggestions = self._analyze_file(py_file)
                self.suggestions.extend(suggestions)
            except Exception as e:
                print(f"   ⚠️  Error analyzing {py_file}: {e}")

        # Sort by confidence and impact
        self.suggestions.sort(
            key=lambda s: (
                {"high": 3, "medium": 2, "low": 1}.get(s.impact, 0),
                s.confidence,
            ),
            reverse=True,
        )

        print(f"✅ Generated {len(self.suggestions)} suggestions")
        return self.suggestions

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            ".git",
            "__pycache__",
            "venv",
            "env",
            ".pytest_cache",
            "htmlcov",
            "dist",
            "build",
            ".eggs",
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path) -> list[CodeSuggestion]:
        """Analyze a single file for suggestions"""
        suggestions = []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        # Check for common patterns
        suggestions.extend(self._check_import_organization(file_path, lines))
        suggestions.extend(self._check_function_complexity(file_path, lines))
        suggestions.extend(self._check_docstring_presence(file_path, lines))
        suggestions.extend(self._check_error_handling(file_path, lines))
        suggestions.extend(self._check_performance_patterns(file_path, lines))

        return suggestions

    def _check_import_organization(
        self, file_path: Path, lines: list[str]
    ) -> list[CodeSuggestion]:
        """Check if imports are properly organized"""
        suggestions = []

        # Find import lines
        import_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                import_lines.append((i, line))

        if not import_lines:
            return suggestions

        # Check if imports are grouped
        stdlib_imports = []
        third_party_imports = []
        local_imports = []

        for i, line in import_lines:
            stripped = line.strip()
            if stripped.startswith("from .") or stripped.startswith("import ."):
                local_imports.append((i, line))
            elif any(
                lib in stripped
                for lib in ["os", "sys", "json", "time", "datetime", "re", "pathlib"]
            ):
                stdlib_imports.append((i, line))
            else:
                third_party_imports.append((i, line))

        # Check if they're in the right order and grouped
        all_imports = stdlib_imports + third_party_imports + local_imports
        if len(all_imports) > 1:
            # Simple check: if imports are not in order
            actual_order = [i for i, _ in import_lines]
            expected_order = [i for i, _ in all_imports]

            if actual_order != expected_order and len(import_lines) > 3:
                suggestion = CodeSuggestion(
                    id=f"import_org_{file_path.name}",
                    category="style",
                    title="Organize imports following PEP 8",
                    description="Imports should be grouped: stdlib, third-party, local",
                    file_path=str(file_path),
                    line_number=import_lines[0][0] + 1,
                    current_code="# Current import order",
                    suggested_code="# Group: stdlib, third-party, local with blank lines",
                    reasoning="PEP 8 recommends organizing imports in groups",
                    confidence=0.9,
                    impact="low",
                    effort="low",
                    auto_fixable=True,
                )
                suggestions.append(suggestion)

        return suggestions

    def _check_function_complexity(
        self, file_path: Path, lines: list[str]
    ) -> list[CodeSuggestion]:
        """Check for overly complex functions"""
        suggestions = []

        in_function = False
        function_start = 0
        function_name = ""
        indent_count = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Detect function definition
            if stripped.startswith("def "):
                in_function = True
                function_start = i
                function_name = stripped.split("(")[0].replace("def ", "").strip()
                indent_count = len(line) - len(line.lstrip())

            elif in_function and stripped and not stripped.startswith("#"):
                current_indent = len(line) - len(line.lstrip())

                # Function ended
                if current_indent <= indent_count and stripped:
                    # Check complexity (simple heuristic: count nesting levels)
                    function_lines = lines[function_start:i]
                    max_nesting = self._calculate_nesting(function_lines)

                    if max_nesting > 4:
                        suggestion = CodeSuggestion(
                            id=f"complexity_{file_path.name}_{function_start}",
                            category="refactoring",
                            title=f"Reduce complexity in function '{function_name}'",
                            description=f"Function has nesting level {max_nesting}, consider refactoring",
                            file_path=str(file_path),
                            line_number=function_start + 1,
                            current_code=f"def {function_name}(...): # {max_nesting} levels deep",
                            suggested_code="Consider extracting nested logic into helper functions",
                            reasoning="High nesting levels reduce readability and maintainability",
                            confidence=0.85,
                            impact="medium",
                            effort="medium",
                            auto_fixable=False,
                        )
                        suggestions.append(suggestion)

                    in_function = False

        return suggestions

    def _calculate_nesting(self, lines: list[str]) -> int:
        """Calculate maximum nesting level in code"""
        max_nesting = 0
        current_nesting = 0
        base_indent = None

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())

            if base_indent is None:
                base_indent = indent

            relative_indent = (indent - base_indent) // 4
            current_nesting = relative_indent
            max_nesting = max(max_nesting, current_nesting)

        return max_nesting

    def _check_docstring_presence(
        self, file_path: Path, lines: list[str]
    ) -> list[CodeSuggestion]:
        """Check if functions and classes have docstrings"""
        suggestions = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check for function or class without docstring
            if stripped.startswith(("def ", "class ")):
                # Look for docstring in next few lines
                has_docstring = False
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith(('"""', "'''")):
                        has_docstring = True
                        break
                    elif next_line and not next_line.startswith("#"):
                        break

                if not has_docstring and not stripped.startswith("def __"):
                    name = (
                        stripped.split("(")[0]
                        .replace("def ", "")
                        .replace("class ", "")
                        .strip()
                    )
                    suggestion = CodeSuggestion(
                        id=f"docstring_{file_path.name}_{i}",
                        category="documentation",
                        title=f"Add docstring to '{name}'",
                        description="Function/class lacks documentation",
                        file_path=str(file_path),
                        line_number=i + 1,
                        current_code=stripped,
                        suggested_code=f'{stripped}\n    """Add description here"""',
                        reasoning="Docstrings improve code maintainability and auto-documentation",
                        confidence=0.95,
                        impact="low",
                        effort="low",
                        auto_fixable=False,
                    )
                    suggestions.append(suggestion)

        return suggestions

    def _check_error_handling(
        self, file_path: Path, lines: list[str]
    ) -> list[CodeSuggestion]:
        """Check for bare except clauses"""
        suggestions = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped == "except:" or stripped.startswith("except:"):
                suggestion = CodeSuggestion(
                    id=f"except_{file_path.name}_{i}",
                    category="security",
                    title="Avoid bare except clause",
                    description="Bare except catches all exceptions including system exits",
                    file_path=str(file_path),
                    line_number=i + 1,
                    current_code=line,
                    suggested_code=line.replace("except:", "except Exception:"),
                    reasoning="Bare except can hide critical errors and make debugging difficult",
                    confidence=0.98,
                    impact="medium",
                    effort="low",
                    auto_fixable=True,
                )
                suggestions.append(suggestion)

        return suggestions

    def _check_performance_patterns(
        self, file_path: Path, lines: list[str]
    ) -> list[CodeSuggestion]:
        """Check for performance anti-patterns"""
        suggestions = []

        for i, line in enumerate(lines):
            # Check for string concatenation in loops
            if "+=" in line and any(
                loop in lines[max(0, i - 10) : i] for loop in ["for ", "while "]
            ):
                if "str" in line or "'" in line or '"' in line:
                    suggestion = CodeSuggestion(
                        id=f"perf_{file_path.name}_{i}",
                        category="performance",
                        title="String concatenation in loop",
                        description="Consider using list.join() for better performance",
                        file_path=str(file_path),
                        line_number=i + 1,
                        current_code=line.strip(),
                        suggested_code="# Use: ''.join(list) instead",
                        reasoning="String concatenation creates new objects; join is more efficient",
                        confidence=0.7,
                        impact="low",
                        effort="low",
                        auto_fixable=False,
                    )
                    suggestions.append(suggestion)

        return suggestions

    def generate_report(self, output_path: str = "CODE_SUGGESTIONS.md") -> None:
        """Generate markdown report of suggestions"""
        print(f"\n📝 Generating suggestions report...")

        report = []
        report.append("# AI-Powered Code Suggestions Report")
        report.append(f"\n**Generated:** {Path(output_path).stem}")
        report.append(f"**Total Suggestions:** {len(self.suggestions)}")
        report.append("\n---\n")

        # Group by category
        by_category = defaultdict(list)
        for suggestion in self.suggestions:
            by_category[suggestion.category].append(suggestion)

        # Summary by category
        report.append("## 📊 Summary by Category\n")
        for category, suggestions in sorted(by_category.items()):
            emoji = {
                "refactoring": "🔨",
                "performance": "⚡",
                "security": "🔒",
                "style": "🎨",
                "documentation": "📚",
            }.get(category, "•")
            report.append(
                f"{emoji} **{category.title()}**: {len(suggestions)} suggestions"
            )

        report.append("\n---\n")

        # Detailed suggestions by category
        for category in sorted(by_category.keys()):
            suggestions = by_category[category]
            emoji = {
                "refactoring": "🔨",
                "performance": "⚡",
                "security": "🔒",
                "style": "🎨",
                "documentation": "📚",
            }.get(category, "•")

            report.append(f"\n## {emoji} {category.title()} Suggestions\n")

            for suggestion in suggestions[:10]:  # Limit to top 10 per category
                impact_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    suggestion.impact, "⚪"
                )

                report.append(f"### {suggestion.title}")
                report.append(
                    f"- **File:** `{suggestion.file_path}` (Line {suggestion.line_number})"
                )
                report.append(
                    f"- **Impact:** {impact_emoji} {suggestion.impact.title()}"
                )
                report.append(f"- **Effort:** {suggestion.effort.title()}")
                report.append(f"- **Confidence:** {suggestion.confidence * 100:.0f}%")
                report.append(
                    f"- **Auto-fixable:** {'✅ Yes' if suggestion.auto_fixable else '❌ No'}"
                )
                report.append(f"\n**Description:** {suggestion.description}")
                report.append(f"\n**Reasoning:** {suggestion.reasoning}")

                if suggestion.current_code != suggestion.suggested_code:
                    report.append(f"\n**Current:**")
                    report.append(f"```python\n{suggestion.current_code}\n```")
                    report.append(f"\n**Suggested:**")
                    report.append(f"```python\n{suggestion.suggested_code}\n```")

                report.append("\n---\n")

        # Save report
        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"✅ Report saved to {output_path}")

    def get_auto_fixable_suggestions(self) -> list[CodeSuggestion]:
        """Get suggestions that can be automatically fixed"""
        return [s for s in self.suggestions if s.auto_fixable]

    def export_json(self, output_path: str = "code_suggestions.json") -> None:
        """Export suggestions as JSON"""
        data = {
            "total_suggestions": len(self.suggestions),
            "suggestions": [asdict(s) for s in self.suggestions],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✅ JSON export saved to {output_path}")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="AI-Powered Code Suggestions")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--output", default="CODE_SUGGESTIONS.md", help="Output file")
    parser.add_argument("--json", help="Also export as JSON")

    args = parser.parse_args()

    try:
        print("=" * 70)
        print("AI-Powered Code Suggestions")
        print("=" * 70)
        print()

        suggestor = AICodeSuggestor(repo_path=args.repo_path)
        suggestions = suggestor.analyze_repository()

        if suggestions:
            suggestor.generate_report(args.output)

            if args.json:
                suggestor.export_json(args.json)

            # Show summary
            print(f"\n📊 Summary:")
            print(f"   Total suggestions: {len(suggestions)}")
            print(f"   Auto-fixable: {len(suggestor.get_auto_fixable_suggestions())}")

            # Top suggestions
            print(f"\n🔝 Top 3 Suggestions:")
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"   {i}. {suggestion.title} ({suggestion.file_path})")
        else:
            print("✅ No suggestions - code looks great!")

        print("\n" + "=" * 70)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
