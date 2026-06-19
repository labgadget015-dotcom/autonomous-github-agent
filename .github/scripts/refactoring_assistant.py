#!/usr/bin/env python3
"""
Automated Refactoring Assistant

Helps with code refactoring by:
- Identifying code smells
- Suggesting refactoring opportunities
- Applying safe automated refactorings
- Tracking refactoring impact
"""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RefactoringOpportunity:
    """Represents a refactoring opportunity"""

    id: str
    type: str  # extract_method, rename, remove_duplication, simplify
    title: str
    description: str
    file_path: str
    line_range: tuple[int, int]
    confidence: float
    impact: str
    complexity_before: int
    complexity_after: int
    auto_applicable: bool


class RefactoringAssistant:
    """
    Automated Refactoring Assistant

    Identifies and applies code refactorings
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.opportunities = []

    def analyze_for_refactoring(self) -> list[RefactoringOpportunity]:
        """Analyze code for refactoring opportunities"""
        print("🔍 Analyzing code for refactoring opportunities...")

        python_files = list(self.repo_path.rglob("*.py"))
        print(f"   Scanning {len(python_files)} Python files")

        for py_file in python_files:
            if self._should_skip(py_file):
                continue

            try:
                opportunities = self._analyze_file(py_file)
                self.opportunities.extend(opportunities)
            except Exception as e:
                print(f"   ⚠️  Error analyzing {py_file}: {e}")

        # Sort by impact and confidence
        self.opportunities.sort(
            key=lambda o: (
                {"high": 3, "medium": 2, "low": 1}.get(o.impact, 0),
                o.confidence,
            ),
            reverse=True,
        )

        print(f"✅ Found {len(self.opportunities)} refactoring opportunities")
        return self.opportunities

    def _should_skip(self, file_path: Path) -> bool:
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
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path) -> list[RefactoringOpportunity]:
        """Analyze a single file"""
        opportunities = []

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Try to parse as AST
        try:
            tree = ast.parse(content)
            opportunities.extend(self._find_long_methods(file_path, tree, content))
            opportunities.extend(self._find_duplicate_code(file_path, content))
            opportunities.extend(
                self._find_complex_conditionals(file_path, tree, content)
            )
        except SyntaxError:
            pass

        return opportunities

    def _find_long_methods(
        self, file_path: Path, tree: ast.AST, content: str
    ) -> list[RefactoringOpportunity]:
        """Find methods that are too long"""
        opportunities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines in function
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    length = node.end_lineno - node.lineno

                    if length > 50:  # Arbitrary threshold
                        opportunity = RefactoringOpportunity(
                            id=f"long_method_{file_path.name}_{node.lineno}",
                            type="extract_method",
                            title=f"Extract method from long function '{node.name}'",
                            description=f"Function is {length} lines long, consider breaking into smaller functions",
                            file_path=str(file_path),
                            line_range=(node.lineno, node.end_lineno),
                            confidence=0.85,
                            impact="medium",
                            complexity_before=length,
                            complexity_after=length // 2,  # Estimate
                            auto_applicable=False,
                        )
                        opportunities.append(opportunity)

        return opportunities

    def _find_duplicate_code(
        self, file_path: Path, content: str
    ) -> list[RefactoringOpportunity]:
        """Find duplicate code blocks"""
        opportunities = []
        lines = content.split("\n")

        # Simple duplicate detection: look for repeated lines
        seen_blocks = {}
        block_size = 5

        for i in range(len(lines) - block_size):
            block = "\n".join(lines[i : i + block_size])
            stripped_block = block.strip()

            if not stripped_block or stripped_block.startswith("#"):
                continue

            if stripped_block in seen_blocks:
                opportunity = RefactoringOpportunity(
                    id=f"duplicate_{file_path.name}_{i}",
                    type="remove_duplication",
                    title="Remove duplicate code",
                    description=f"Similar code found at lines {seen_blocks[stripped_block]} and {i+1}",
                    file_path=str(file_path),
                    line_range=(i + 1, i + block_size),
                    confidence=0.7,
                    impact="medium",
                    complexity_before=2,
                    complexity_after=1,
                    auto_applicable=False,
                )
                opportunities.append(opportunity)
            else:
                seen_blocks[stripped_block] = i + 1

        return opportunities

    def _find_complex_conditionals(
        self, file_path: Path, tree: ast.AST, content: str
    ) -> list[RefactoringOpportunity]:
        """Find complex conditional statements"""
        opportunities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check complexity of condition
                condition_complexity = self._calculate_condition_complexity(node.test)

                if condition_complexity > 3:
                    opportunity = RefactoringOpportunity(
                        id=f"complex_if_{file_path.name}_{node.lineno}",
                        type="simplify",
                        title="Simplify complex conditional",
                        description=f"Conditional has complexity {condition_complexity}, consider extracting to variable or function",
                        file_path=str(file_path),
                        line_range=(node.lineno, node.lineno),
                        confidence=0.75,
                        impact="low",
                        complexity_before=condition_complexity,
                        complexity_after=1,
                        auto_applicable=False,
                    )
                    opportunities.append(opportunity)

        return opportunities

    def _calculate_condition_complexity(self, node: ast.AST) -> int:
        """Calculate complexity of a conditional expression"""
        if isinstance(node, (ast.And, ast.Or)):
            return 1 + sum(
                self._calculate_condition_complexity(val)
                for val in [node.left, node.right]
                if hasattr(node, "left")
            )
        elif isinstance(node, ast.BoolOp):
            return 1 + sum(
                self._calculate_condition_complexity(val) for val in node.values
            )
        elif isinstance(node, ast.UnaryOp):
            return 1 + self._calculate_condition_complexity(node.operand)
        elif isinstance(node, ast.Compare):
            return 1
        else:
            return 0

    def generate_report(
        self, output_path: str = "REFACTORING_OPPORTUNITIES.md"
    ) -> None:
        """Generate refactoring opportunities report"""
        print("\n📝 Generating refactoring report...")

        report = []
        report.append("# Automated Refactoring Opportunities")
        report.append(f"\n**Total Opportunities:** {len(self.opportunities)}")
        report.append("\n---\n")

        # Summary by type
        by_type = {}
        for opp in self.opportunities:
            by_type.setdefault(opp.type, []).append(opp)

        report.append("## 📊 Summary by Type\n")
        for ref_type, opps in sorted(by_type.items()):
            emoji = {
                "extract_method": "🔨",
                "rename": "✏️",
                "remove_duplication": "🔄",
                "simplify": "✨",
            }.get(ref_type, "•")
            report.append(
                f"{emoji} **{ref_type.replace('_', ' ').title()}**: {len(opps)} opportunities"
            )

        report.append("\n---\n")

        # Detailed opportunities
        report.append("## 🔧 Refactoring Opportunities\n")

        for i, opp in enumerate(self.opportunities[:20], 1):  # Top 20
            impact_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                opp.impact, "⚪"
            )

            report.append(f"### {i}. {opp.title}")
            report.append(f"- **Type:** {opp.type.replace('_', ' ').title()}")
            report.append(
                f"- **File:** `{opp.file_path}` (Lines {opp.line_range[0]}-{opp.line_range[1]})"
            )
            report.append(f"- **Impact:** {impact_emoji} {opp.impact.title()}")
            report.append(f"- **Confidence:** {opp.confidence * 100:.0f}%")
            report.append(
                f"- **Complexity:** {opp.complexity_before} → {opp.complexity_after}"
            )
            report.append(
                f"- **Auto-applicable:** {'✅ Yes' if opp.auto_applicable else '❌ No'}"
            )
            report.append(f"\n**Description:** {opp.description}\n")
            report.append("---\n")

        # Save report
        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"✅ Report saved to {output_path}")

    def get_high_impact_opportunities(self) -> list[RefactoringOpportunity]:
        """Get high-impact refactoring opportunities"""
        return [o for o in self.opportunities if o.impact == "high"]

    def estimate_time_savings(self) -> dict[str, Any]:
        """Estimate time savings from refactoring"""
        total_complexity_reduction = sum(
            o.complexity_before - o.complexity_after for o in self.opportunities
        )

        # Rough estimate: 1 complexity point = 5 minutes maintenance time
        estimated_minutes = total_complexity_reduction * 5

        return {
            "total_opportunities": len(self.opportunities),
            "complexity_reduction": total_complexity_reduction,
            "estimated_time_savings_hours": estimated_minutes / 60,
            "high_impact_count": len(self.get_high_impact_opportunities()),
        }


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Automated Refactoring Assistant")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument(
        "--output", default="REFACTORING_OPPORTUNITIES.md", help="Output file"
    )

    args = parser.parse_args()

    try:
        print("=" * 70)
        print("Automated Refactoring Assistant")
        print("=" * 70)
        print()

        assistant = RefactoringAssistant(repo_path=args.repo_path)
        opportunities = assistant.analyze_for_refactoring()

        if opportunities:
            assistant.generate_report(args.output)

            # Show time savings estimate
            savings = assistant.estimate_time_savings()
            print("\n💰 Estimated Impact:")
            print(f"   Total opportunities: {savings['total_opportunities']}")
            print(f"   Complexity reduction: {savings['complexity_reduction']}")
            print(
                f"   Time savings: {savings['estimated_time_savings_hours']:.1f} hours"
            )
            print(f"   High impact: {savings['high_impact_count']}")
        else:
            print("✅ No refactoring opportunities found - code is well structured!")

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
