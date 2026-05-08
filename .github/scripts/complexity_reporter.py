#!/usr/bin/env python3
"""
Complexity Reporter - Generates PR comments and reports for code complexity
Integrates with Radon to track cyclomatic complexity and maintainability
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


class ComplexityReporter:
    """Generate complexity reports and recommendations"""

    def __init__(self):
        self.complexity_data = self._load_json("complexity.json")
        self.maintainability_data = self._load_json("maintainability.json")
        self.thresholds = {"complexity": 10, "maintainability": 65}

    def _load_json(self, filename: str) -> Dict:
        """Load JSON data file"""
        try:
            with open(filename) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {filename}")
            return {}

    def analyze_complexity(self) -> Dict:
        """Analyze complexity data and identify issues"""
        issues = {
            "high_complexity": [],
            "low_maintainability": [],
            "total_functions": 0,
            "avg_complexity": 0,
        }

        total_complexity = 0
        function_count = 0

        for filepath, functions in self.complexity_data.items():
            for func in functions:
                function_count += 1
                complexity = func.get("complexity", 0)
                total_complexity += complexity

                if complexity > self.thresholds["complexity"]:
                    issues["high_complexity"].append(
                        {
                            "file": filepath,
                            "function": func.get("name", "unknown"),
                            "complexity": complexity,
                            "line": func.get("lineno", 0),
                        }
                    )

        if function_count > 0:
            issues["avg_complexity"] = round(total_complexity / function_count, 2)
        issues["total_functions"] = function_count

        # Analyze maintainability
        for filepath, mi_score in self.maintainability_data.items():
            if isinstance(mi_score, dict):
                score = mi_score.get("mi", 100)
            else:
                score = mi_score

            if score < self.thresholds["maintainability"]:
                issues["low_maintainability"].append(
                    {"file": filepath, "score": round(score, 2)}
                )

        return issues

    def generate_markdown_report(self, issues: Dict) -> str:
        """Generate markdown report for PR comment"""
        report = f"""## 📊 Code Complexity Analysis

**Summary:**
- Total Functions Analyzed: {issues['total_functions']}
- Average Complexity: {issues['avg_complexity']}
- High Complexity Functions: {len(issues['high_complexity'])}
- Low Maintainability Files: {len(issues['low_maintainability'])}

"""

        if issues["high_complexity"]:
            report += "### ⚠️ High Complexity Functions\n\n"
            report += "These functions exceed the complexity threshold and should be refactored:\n\n"
            report += "| File | Function | Complexity | Line |\n"
            report += "|------|----------|------------|------|\n"

            for item in sorted(
                issues["high_complexity"], key=lambda x: x["complexity"], reverse=True
            )[:10]:
                report += f"| `{item['file']}` | `{item['function']}` | {item['complexity']} | {item['line']} |\n"

            if len(issues["high_complexity"]) > 10:
                report += f"\n*... and {len(issues['high_complexity']) - 10} more*\n"

            report += "\n**Recommendations:**\n"
            report += "- Break down large functions into smaller, focused units\n"
            report += "- Extract complex conditional logic into separate functions\n"
            report += "- Use early returns to reduce nesting\n\n"

        if issues["low_maintainability"]:
            report += "### 🔧 Low Maintainability Files\n\n"
            report += "These files have low maintainability scores and may need refactoring:\n\n"
            report += "| File | Score | Status |\n"
            report += "|------|-------|--------|\n"

            for item in sorted(issues["low_maintainability"], key=lambda x: x["score"]):
                status = "🔴" if item["score"] < 50 else "🟡"
                report += f"| `{item['file']}` | {item['score']} | {status} |\n"

            report += "\n**Maintainability Index Guide:**\n"
            report += "- 🟢 85-100: Excellent maintainability\n"
            report += "- 🟡 65-84: Good maintainability\n"
            report += "- 🟠 50-64: Moderate maintainability (consider refactoring)\n"
            report += "- 🔴 0-49: Poor maintainability (needs refactoring)\n\n"

        if not issues["high_complexity"] and not issues["low_maintainability"]:
            report += "### ✅ All Clear!\n\n"
            report += (
                "No complexity or maintainability issues detected. Great job! 🎉\n"
            )

        return report

    def generate_refactoring_recommendations(self, issues: Dict) -> List[str]:
        """Generate specific refactoring recommendations"""
        recommendations = []

        for item in issues["high_complexity"][:5]:
            recommendations.append(
                f"Refactor `{item['function']}` in {item['file']} "
                f"(complexity: {item['complexity']}) by breaking it into smaller functions"
            )

        for item in issues["low_maintainability"][:3]:
            recommendations.append(
                f"Improve maintainability of {item['file']} "
                f"(score: {item['score']}) through code cleanup and documentation"
            )

        return recommendations

    def should_block_merge(self, issues: Dict) -> bool:
        """Determine if complexity issues should block merge"""
        # Block if there are functions with very high complexity
        critical_complexity = [
            i for i in issues["high_complexity"] if i["complexity"] > 20
        ]
        critical_maintainability = [
            i for i in issues["low_maintainability"] if i["score"] < 40
        ]

        return len(critical_complexity) > 0 or len(critical_maintainability) > 0

    def save_report(self, report: str, filename: str = "complexity-report.md"):
        """Save report to file"""
        with open(filename, "w") as f:
            f.write(report)
        print(f"✅ Report saved to {filename}")


def main():
    """Main entry point"""
    reporter = ComplexityReporter()

    # Analyze complexity
    issues = reporter.analyze_complexity()

    # Generate report
    report = reporter.generate_markdown_report(issues)
    print(report)

    # Save report
    reporter.save_report(report)

    # Generate recommendations
    recommendations = reporter.generate_refactoring_recommendations(issues)
    if recommendations:
        print("\n🔧 Top Refactoring Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

    # Check if should block
    if reporter.should_block_merge(issues):
        print("\n❌ Critical complexity issues detected!")
        print("These issues should be addressed before merging.")
        sys.exit(1)
    else:
        print("\n✅ No critical complexity issues")
        sys.exit(0)


if __name__ == "__main__":
    main()
