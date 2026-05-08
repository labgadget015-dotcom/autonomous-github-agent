#!/usr/bin/env python3
"""
Health Dashboard Generator
Creates automated markdown dashboards for repository health metrics
"""

import json
from datetime import datetime
from pathlib import Path


class HealthDashboardGenerator:
    """Generate comprehensive health dashboards"""

    def __init__(self):
        self.metrics = {}
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    def load_analysis_results(self) -> dict:
        """Load code analysis results"""
        try:
            with open("analysis-results.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def load_coverage_data(self) -> dict:
        """Load test coverage data"""
        try:
            with open("coverage.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def load_complexity_data(self) -> dict:
        """Load complexity metrics"""
        complexity = {}
        try:
            with open("complexity.json") as f:
                complexity["cyclomatic"] = json.load(f)
        except FileNotFoundError:
            pass

        try:
            with open("maintainability.json") as f:
                complexity["maintainability"] = json.load(f)
        except FileNotFoundError:
            pass

        return complexity

    def load_security_data(self) -> dict:
        """Load security scan results"""
        try:
            with open("bandit-report.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def load_violations(self) -> dict:
        """Load threshold violations"""
        try:
            with open("threshold-violations.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def calculate_health_score(self) -> int:
        """Calculate overall health score (0-100)"""
        score = 100

        # Analysis results (-20 if failed)
        analysis = self.metrics.get("analysis", {})
        if not analysis.get("passed", True):
            score -= 20

        # Coverage (-30 if below 80%)
        coverage = self.metrics.get("coverage", {})
        coverage_pct = coverage.get("totals", {}).get("percent_covered", 100)
        if coverage_pct < 80:
            score -= int((80 - coverage_pct) * 1.5)

        # Security issues (-10 per critical, -5 per high)
        security = self.metrics.get("security", {})
        for result in security.get("results", []):
            if result.get("issue_severity") == "HIGH":
                score -= 10
            elif result.get("issue_severity") == "MEDIUM":
                score -= 5

        # Violations (-5 per critical, -2 per high)
        violations = self.metrics.get("violations", {})
        for v in violations.get("violations", []):
            if v.get("severity") == "critical":
                score -= 5
            elif v.get("severity") == "high":
                score -= 2

        return max(0, min(100, score))

    def get_health_status(self, score: int) -> tuple:
        """Get health status and emoji"""
        if score >= 90:
            return ("Excellent", "🟢")
        elif score >= 75:
            return ("Good", "🟡")
        elif score >= 60:
            return ("Fair", "🟠")
        else:
            return ("Poor", "🔴")

    def generate_dashboard(self) -> str:
        """Generate complete health dashboard"""
        # Load all metrics
        self.metrics = {
            "analysis": self.load_analysis_results(),
            "coverage": self.load_coverage_data(),
            "complexity": self.load_complexity_data(),
            "security": self.load_security_data(),
            "violations": self.load_violations(),
        }

        # Calculate health score
        health_score = self.calculate_health_score()
        status, emoji = self.get_health_status(health_score)

        # Generate dashboard
        dashboard = f"""# 📊 Repository Health Dashboard

**Last Updated:** {self.timestamp}  
**Health Score:** {emoji} **{health_score}/100** ({status})

---

## 🎯 Quick Overview

"""

        # Add quick stats
        dashboard += self._generate_quick_stats()
        dashboard += "\n---\n\n"

        # Add detailed sections
        dashboard += self._generate_coverage_section()
        dashboard += self._generate_quality_section()
        dashboard += self._generate_security_section()
        dashboard += self._generate_complexity_section()
        dashboard += self._generate_trends_section()
        dashboard += self._generate_recommendations()

        return dashboard

    def _generate_quick_stats(self) -> str:
        """Generate quick statistics overview"""
        stats = "| Metric | Status | Value |\n"
        stats += "|--------|--------|-------|\n"

        # Coverage
        coverage_pct = (
            self.metrics.get("coverage", {}).get("totals", {}).get("percent_covered", 0)
        )
        coverage_emoji = "✅" if coverage_pct >= 80 else "❌"
        stats += f"| Test Coverage | {coverage_emoji} | {coverage_pct:.1f}% |\n"

        # Analysis
        analysis_passed = self.metrics.get("analysis", {}).get("passed", False)
        analysis_emoji = "✅" if analysis_passed else "❌"
        stats += f"| Code Quality | {analysis_emoji} | {'Passed' if analysis_passed else 'Failed'} |\n"

        # Security
        security_issues = len(self.metrics.get("security", {}).get("results", []))
        security_emoji = "✅" if security_issues == 0 else "❌"
        stats += f"| Security Issues | {security_emoji} | {security_issues} |\n"

        # Violations
        violations = len(self.metrics.get("violations", {}).get("violations", []))
        violations_emoji = "✅" if violations == 0 else "❌"
        stats += f"| Violations | {violations_emoji} | {violations} |\n"

        return stats + "\n"

    def _generate_coverage_section(self) -> str:
        """Generate coverage section"""
        coverage = self.metrics.get("coverage", {})
        if not coverage:
            return "## 📊 Test Coverage\n\n*No coverage data available*\n\n"

        totals = coverage.get("totals", {})

        section = "## 📊 Test Coverage\n\n"
        section += f"**Overall Coverage:** {totals.get('percent_covered', 0):.2f}%\n\n"

        section += "| Metric | Covered | Total | Percentage |\n"
        section += "|--------|---------|-------|------------|\n"
        section += f"| Statements | {totals.get('covered_lines', 0)} | {totals.get('num_statements', 0)} | {totals.get('percent_covered', 0):.1f}% |\n"
        section += f"| Branches | {totals.get('covered_branches', 0)} | {totals.get('num_branches', 0)} | {totals.get('percent_covered_display', 'N/A')} |\n"
        section += f"| Functions | {totals.get('covered_functions', 0)} | {totals.get('num_functions', 0)} | N/A |\n"

        section += "\n"
        return section

    def _generate_quality_section(self) -> str:
        """Generate code quality section"""
        analysis = self.metrics.get("analysis", {})
        if not analysis:
            return "## 🔍 Code Quality\n\n*No analysis data available*\n\n"

        section = "## 🔍 Code Quality\n\n"
        section += (
            f"**Status:** {'✅ Passed' if analysis.get('passed') else '❌ Failed'}\n"
        )
        section += f"**Duration:** {analysis.get('elapsed_seconds', 0):.2f}s\n\n"

        section += "### Tool Results\n\n"
        for tool, data in analysis.get("tools", {}).items():
            emoji = "✅" if data["status"] == "passed" else "❌"
            section += f"- {emoji} **{tool.upper()}**: {data['status']}\n"

        section += "\n"
        return section

    def _generate_security_section(self) -> str:
        """Generate security section"""
        security = self.metrics.get("security", {})
        if not security:
            return "## 🔒 Security\n\n*No security scan data available*\n\n"

        results = security.get("results", [])

        section = "## 🔒 Security\n\n"
        section += f"**Total Issues:** {len(results)}\n\n"

        if results:
            severity_counts = {}
            for issue in results:
                severity = issue.get("issue_severity", "UNKNOWN")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            section += "### Issues by Severity\n\n"
            for severity, count in sorted(severity_counts.items()):
                emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
                section += f"- {emoji} **{severity}:** {count}\n"
        else:
            section += "✅ No security issues detected!\n"

        section += "\n"
        return section

    def _generate_complexity_section(self) -> str:
        """Generate complexity section"""
        complexity = self.metrics.get("complexity", {})
        if not complexity:
            return "## 🔧 Code Complexity\n\n*No complexity data available*\n\n"

        section = "## 🔧 Code Complexity\n\n"

        # Cyclomatic complexity
        cc_data = complexity.get("cyclomatic", {})
        if cc_data:
            total_functions = 0
            total_complexity = 0
            high_complexity = 0

            for _filepath, functions in cc_data.items():
                for func in functions:
                    total_functions += 1
                    cc = func.get("complexity", 0)
                    total_complexity += cc
                    if cc > 10:
                        high_complexity += 1

            avg_complexity = (
                total_complexity / total_functions if total_functions > 0 else 0
            )

            section += f"**Average Complexity:** {avg_complexity:.2f}\n"
            section += f"**High Complexity Functions:** {high_complexity}\n\n"

        # Maintainability
        mi_data = complexity.get("maintainability", {})
        if mi_data:
            scores = [
                v if isinstance(v, (int, float)) else v.get("mi", 100)
                for v in mi_data.values()
            ]
            if scores:
                avg_mi = sum(scores) / len(scores)
                section += f"**Average Maintainability Index:** {avg_mi:.2f}/100\n"

        section += "\n"
        return section

    def _generate_trends_section(self) -> str:
        """Generate trends section (placeholder for historical data)"""
        return """## 📈 Trends

*Historical trend tracking will be available after multiple dashboard generations*

"""

    def _generate_recommendations(self) -> str:
        """Generate actionable recommendations"""
        recommendations = []

        # Coverage recommendations
        coverage_pct = (
            self.metrics.get("coverage", {}).get("totals", {}).get("percent_covered", 0)
        )
        if coverage_pct < 80:
            recommendations.append(
                f"📊 **Increase test coverage** from {coverage_pct:.1f}% to 80%+"
            )

        # Security recommendations
        security_issues = len(self.metrics.get("security", {}).get("results", []))
        if security_issues > 0:
            recommendations.append(
                f"🔒 **Fix {security_issues} security issues** detected by Bandit"
            )

        # Complexity recommendations
        violations = self.metrics.get("violations", {}).get("violations", [])
        complexity_issues = [v for v in violations if v.get("type") == "complexity"]
        if complexity_issues:
            recommendations.append(
                f"🔧 **Refactor {len(complexity_issues)} high-complexity functions**"
            )

        # Quality recommendations
        if not self.metrics.get("analysis", {}).get("passed", True):
            recommendations.append("🔍 **Fix code quality issues** reported by linters")

        section = "## 💡 Recommendations\n\n"

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                section += f"{i}. {rec}\n"
        else:
            section += (
                "✅ No critical recommendations at this time. Keep up the great work!\n"
            )

        section += "\n---\n\n*This dashboard is automatically generated by the CI/CD pipeline.*\n"

        return section

    def save_dashboard(self, content: str, path: str = "docs/HEALTH_DASHBOARD.md"):
        """Save dashboard to file"""
        dashboard_path = Path(path)
        dashboard_path.parent.mkdir(parents=True, exist_ok=True)

        with open(dashboard_path, "w") as f:
            f.write(content)

        print(f"✅ Dashboard saved to {path}")


def main():
    """Main entry point"""
    print("📊 Generating health dashboard...")

    generator = HealthDashboardGenerator()
    dashboard = generator.generate_dashboard()

    print(dashboard)
    print("\n" + "=" * 80 + "\n")

    generator.save_dashboard(dashboard)

    print("✅ Dashboard generation complete")


if __name__ == "__main__":
    main()
