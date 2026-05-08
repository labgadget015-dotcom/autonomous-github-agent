#!/usr/bin/env python3
"""
Repository Health Dashboard

Generates a visual dashboard showing repository health metrics.
"""

import json
from datetime import datetime
from pathlib import Path


class HealthDashboard:
    """Generate repository health dashboard"""

    def __init__(self, results_file: Path = None):
        if results_file is None:
            results_file = Path("overseer-results.json")

        self.results_file = Path(results_file)
        self.results = self._load_results()

    def _load_results(self) -> dict:
        """Load overseer results"""
        if not self.results_file.exists():
            return {}

        with open(self.results_file) as f:
            return json.load(f)

    def _get_health_score(self) -> int:
        """Calculate overall health score (0-100)"""
        score = 100

        analyses = self.results.get("analyses", {})

        # Code quality (40% weight)
        code = analyses.get("code", {})
        quality_score = code.get("code_quality_score", code.get("quality_score", 100))
        score -= (100 - quality_score) * 0.4

        # Dependencies (30% weight)
        deps = analyses.get("dependencies", {})
        vuln_count = len(deps.get("vulnerable_packages", []))
        score -= min(vuln_count * 10, 30)  # Cap at 30 points

        # CI/CD (15% weight)
        cicd = analyses.get("cicd", {})
        cicd_issues = len(cicd.get("workflow_optimizations", []))
        score -= min(cicd_issues * 2, 15)  # Cap at 15 points

        # Documentation (15% weight)
        docs = analyses.get("documentation", {})
        if not docs.get("readme_updated", True):
            score -= 10
        if not docs.get("contributing_generated", True):
            score -= 5

        return max(0, int(score))

    def _get_status_emoji(self, score: int) -> str:
        """Get emoji for score"""
        if score >= 90:
            return "🟢"
        elif score >= 70:
            return "🟡"
        elif score >= 50:
            return "🟠"
        else:
            return "🔴"

    def _get_priority_counts(self) -> dict[str, int]:
        """Get counts of issues by priority"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        recs = self.results.get("recommendations", [])
        for rec in recs:
            priority = rec.get("priority", "low")
            counts[priority] = counts.get(priority, 0) + 1

        return counts

    def generate_markdown_dashboard(self) -> str:
        """Generate markdown dashboard"""
        content = []

        # Header
        content.append("# 📊 Repository Health Dashboard\n\n")
        timestamp = self.results.get("timestamp", datetime.now().isoformat())
        content.append(f"*Last updated: {timestamp}*\n\n")
        content.append("---\n\n")

        # Overall Health Score
        health_score = self._get_health_score()
        status_emoji = self._get_status_emoji(health_score)

        content.append("## Overall Health\n\n")
        content.append(f"### {status_emoji} Score: {health_score}/100\n\n")

        # Progress bar
        filled = int(health_score / 5)
        empty = 20 - filled
        progress_bar = "█" * filled + "░" * empty
        content.append(f"```\n{progress_bar} {health_score}%\n```\n\n")

        # Status interpretation
        if health_score >= 90:
            content.append("**Status:** Excellent - Repository is in great shape!\n\n")
        elif health_score >= 70:
            content.append("**Status:** Good - Minor improvements recommended\n\n")
        elif health_score >= 50:
            content.append("**Status:** Fair - Some issues need attention\n\n")
        else:
            content.append("**Status:** Poor - Immediate action required\n\n")

        content.append("---\n\n")

        # Metrics
        analyses = self.results.get("analyses", {})

        # Code Quality
        code = analyses.get("code", {})
        if code:
            content.append("## 💻 Code Quality\n\n")

            quality_score = code.get("code_quality_score", code.get("quality_score", 0))
            refactoring = len(code.get("refactoring_opportunities", []))
            architecture = len(code.get("architectural_improvements", []))
            performance = len(code.get("performance_optimizations", []))

            content.append(f"- **Quality Score:** {quality_score}/100\n")
            content.append(f"- **Refactoring Opportunities:** {refactoring}\n")
            content.append(f"- **Architectural Improvements:** {architecture}\n")
            content.append(f"- **Performance Issues:** {performance}\n\n")

        # Dependencies
        deps = analyses.get("dependencies", {})
        if deps:
            content.append("## 📦 Dependencies\n\n")

            vulnerable = len(deps.get("vulnerable_packages", []))
            outdated = len(deps.get("outdated_packages", []))
            recommendations = len(deps.get("upgrade_recommendations", []))

            if vulnerable > 0:
                content.append(
                    f"- ⚠️ **Vulnerable Packages:** {vulnerable} (CRITICAL)\n"
                )
            else:
                content.append("- ✅ **Vulnerable Packages:** 0\n")

            content.append(f"- **Outdated Packages:** {outdated}\n")
            content.append(f"- **Upgrade Recommendations:** {recommendations}\n\n")

        # CI/CD
        cicd = analyses.get("cicd", {})
        if cicd:
            content.append("## ⚙️ CI/CD\n\n")

            optimizations = len(cicd.get("workflow_optimizations", []))
            test_improvements = len(cicd.get("test_improvements", []))
            linting = len(cicd.get("linting_suggestions", []))

            content.append(f"- **Workflow Optimizations:** {optimizations}\n")
            content.append(f"- **Test Improvements:** {test_improvements}\n")
            content.append(f"- **Linting Suggestions:** {linting}\n\n")

        # Documentation
        docs = analyses.get("documentation", {})
        if docs:
            content.append("## 📚 Documentation\n\n")

            readme = "✅" if docs.get("readme_updated", False) else "❌"
            contrib = "✅" if docs.get("contributing_generated", False) else "❌"
            api_docs = "✅" if docs.get("api_docs_generated", False) else "❌"

            content.append(f"- **README:** {readme}\n")
            content.append(f"- **Contributing Guide:** {contrib}\n")
            content.append(f"- **API Documentation:** {api_docs}\n\n")

        # Issue Triage
        issues = analyses.get("issue_triage", {})
        if issues:
            content.append("## 🏷️ Issue Management\n\n")

            processed = issues.get("issues_processed", 0)
            labeled = issues.get("labels_applied", 0)
            prioritized = issues.get("priorities_assigned", 0)

            content.append(f"- **Issues Processed:** {processed}\n")
            content.append(f"- **Labels Applied:** {labeled}\n")
            content.append(f"- **Priorities Assigned:** {prioritized}\n\n")

        # Monitoring
        monitoring = analyses.get("monitoring", {})
        if monitoring:
            content.append("## 📈 Monitoring\n\n")

            recs = monitoring.get("recommendations", [])
            content.append(f"- **Total Recommendations:** {len(recs)}\n")

            # Count by priority
            priority_counts = {"high": 0, "medium": 0, "low": 0}
            for rec in recs:
                priority = rec.get("priority", "low")
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            content.append(f"- **High Priority:** {priority_counts['high']}\n")
            content.append(f"- **Medium Priority:** {priority_counts['medium']}\n")
            content.append(f"- **Low Priority:** {priority_counts['low']}\n\n")

        # Top Recommendations
        recs = self.results.get("recommendations", [])
        if recs:
            content.append("---\n\n")
            content.append("## 💡 Top Recommendations\n\n")

            # Group by priority
            critical = [r for r in recs if r.get("priority") == "critical"]
            high = [r for r in recs if r.get("priority") == "high"]

            if critical:
                content.append("### 🔴 Critical\n\n")
                for rec in critical[:5]:
                    content.append(
                        f"- **[{rec.get('category', 'general')}]** {rec.get('message', '')}\n"
                    )
                content.append("\n")

            if high:
                content.append("### 🟡 High Priority\n\n")
                for rec in high[:5]:
                    content.append(
                        f"- **[{rec.get('category', 'general')}]** {rec.get('message', '')}\n"
                    )
                content.append("\n")

        # Footer
        content.append("---\n\n")
        content.append("*Generated by Repository Overseer*\n")

        return "".join(content)

    def generate_html_dashboard(self) -> str:
        """Generate HTML dashboard (future enhancement)"""
        # TODO: Implement HTML dashboard with charts
        pass

    def save_dashboard(self, output_file: Path = None):
        """Save dashboard to file"""
        if output_file is None:
            output_file = Path("HEALTH_DASHBOARD.md")

        markdown = self.generate_markdown_dashboard()

        with open(output_file, "w") as f:
            f.write(markdown)

        print(f"✅ Dashboard saved to: {output_file}")
        return output_file


def main():
    """Main entry point"""
    import sys

    results_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    print("📊 Generating Repository Health Dashboard...")
    print()

    dashboard = HealthDashboard(results_file)
    dashboard.save_dashboard()

    # Print to console
    print()
    print("=" * 60)
    print(dashboard.generate_markdown_dashboard())
    print("=" * 60)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
