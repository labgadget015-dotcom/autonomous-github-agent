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
        coverage_pct = self.metrics.get("coverage", {}).get("totals", {}).get("percent_covered", 0)
        coverage_emoji = "✅" if coverage_pct >= 80 else "❌"
        stats += f"| Test Coverage | {coverage_emoji} | {coverage_pct:.1f}% |\n"

        # Analysis
        analysis_passed = self.metrics.get("analysis", {}).get("passed", False)
        analysis_emoji = "✅" if analysis_passed else "❌"
        stats += (
            f"| Code Quality | {analysis_emoji} | {'Passed' if analysis_passed else 'Failed'} |\n"
        )

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
        section += f"**Status:** {'✅ Passed' if analysis.get('passed') else '❌ Failed'}\n"
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

            avg_complexity = total_complexity / total_functions if total_functions > 0 else 0

            section += f"**Average Complexity:** {avg_complexity:.2f}\n"
            section += f"**High Complexity Functions:** {high_complexity}\n\n"

        # Maintainability
        mi_data = complexity.get("maintainability", {})
        if mi_data:
            scores = [
                v if isinstance(v, (int, float)) else v.get("mi", 100) for v in mi_data.values()
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
        coverage_pct = self.metrics.get("coverage", {}).get("totals", {}).get("percent_covered", 0)
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
            section += "✅ No critical recommendations at this time. Keep up the great work!\n"

        section += "\n---\n\n*This dashboard is automatically generated by the CI/CD pipeline.*\n"

        return section

    def generate_html_dashboard(self) -> str:
        """Generate a self-contained HTML health dashboard with Chart.js charts."""
        self.metrics = {
            "analysis": self.load_analysis_results(),
            "coverage": self.load_coverage_data(),
            "complexity": self.load_complexity_data(),
            "security": self.load_security_data(),
            "violations": self.load_violations(),
        }

        health_score = self.calculate_health_score()
        status, _emoji = self.get_health_status(health_score)

        coverage_pct = round(
            self.metrics.get("coverage", {}).get("totals", {}).get("percent_covered", 0),
            1,
        )

        sec_counts: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for result in self.metrics.get("security", {}).get("results", []):
            sev = result.get("issue_severity", "LOW")
            sec_counts[sev] = sec_counts.get(sev, 0) + 1

        tools = self.metrics.get("analysis", {}).get("tools", {})
        tool_labels = list(tools.keys()) or ["(no data)"]
        tool_scores = [1 if t.get("status") == "passed" else 0 for t in tools.values()] or [0]

        score_color = (
            "#22c55e"
            if health_score >= 90
            else "#eab308" if health_score >= 75 else "#f97316" if health_score >= 60 else "#ef4444"
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Repository Health Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  body {{font-family: system-ui, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0;}}
  header {{background: #1e293b; padding: 1.5rem 2rem; border-bottom: 1px solid #334155;}}
  h1 {{margin: 0; font-size: 1.5rem;}}
  .sub {{color: #94a3b8; font-size: 0.875rem; margin-top: 0.25rem;}}
  .grid {{display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 1.5rem; padding: 1.5rem 2rem; max-width: 1200px; margin: 0 auto;}}
  .card {{background: #1e293b; border-radius: 0.75rem; padding: 1.25rem;
          border: 1px solid #334155;}}
  .card h2 {{margin: 0 0 1rem; font-size: 1rem; color: #94a3b8; text-transform: uppercase;
             letter-spacing: 0.05em;}}
  .score-big {{font-size: 3.5rem; font-weight: 700; color: {score_color};
               text-align: center; padding: 0.5rem 0;}}
  .score-label {{text-align: center; color: #94a3b8; margin-bottom: 1rem;}}
  canvas {{max-height: 220px;}}
  .note {{font-size: 0.75rem; color: #64748b; margin-top: 0.75rem;}}
</style>
</head>
<body>
<header>
  <h1>Repository Health Dashboard</h1>
  <div class="sub">Generated: {self.timestamp} &nbsp;|&nbsp; Score: {health_score}/100 — {status}</div>
</header>
<div class="grid">

  <div class="card">
    <h2>Health Score</h2>
    <div class="score-big">{health_score}</div>
    <div class="score-label">out of 100 &mdash; {status}</div>
    <canvas id="scoreChart"></canvas>
  </div>

  <div class="card">
    <h2>Test Coverage</h2>
    <canvas id="coverageChart"></canvas>
    <p class="note">Current: {coverage_pct}% &nbsp;|&nbsp; Target: 80%</p>
  </div>

  <div class="card">
    <h2>Security Issues</h2>
    <canvas id="secChart"></canvas>
    <p class="note">Total: {sum(sec_counts.values())} issues from Bandit scan</p>
  </div>

  <div class="card">
    <h2>Quality Tools</h2>
    <canvas id="qualityChart"></canvas>
    <p class="note">1 = passed, 0 = failed</p>
  </div>

</div>

<script>
const scoreCtx = document.getElementById('scoreChart');
new Chart(scoreCtx, {{
  type: 'doughnut',
  data: {{
    datasets: [{{
      data: [{health_score}, {100 - health_score}],
      backgroundColor: ['{score_color}', '#334155'],
      borderWidth: 0,
    }}]
  }},
  options: {{plugins: {{legend: {{display: false}}}}, cutout: '75%'}}
}});

const covCtx = document.getElementById('coverageChart');
new Chart(covCtx, {{
  type: 'bar',
  data: {{
    labels: ['Coverage', 'Target'],
    datasets: [{{
      data: [{coverage_pct}, 80],
      backgroundColor: [
        {coverage_pct} >= 80 ? '#22c55e' : '#ef4444',
        '#334155'
      ],
      borderRadius: 4,
    }}]
  }},
  options: {{
    scales: {{
      y: {{min: 0, max: 100, ticks: {{color: '#94a3b8'}}, grid: {{color: '#1e293b'}}}},
      x: {{ticks: {{color: '#94a3b8'}}, grid: {{display: false}}}}
    }},
    plugins: {{legend: {{display: false}}}}
  }}
}});

const secCtx = document.getElementById('secChart');
new Chart(secCtx, {{
  type: 'bar',
  data: {{
    labels: ['HIGH', 'MEDIUM', 'LOW'],
    datasets: [{{
      data: [{sec_counts['HIGH']}, {sec_counts['MEDIUM']}, {sec_counts['LOW']}],
      backgroundColor: ['#ef4444', '#eab308', '#22c55e'],
      borderRadius: 4,
    }}]
  }},
  options: {{
    scales: {{
      y: {{ticks: {{color: '#94a3b8', stepSize: 1}}, grid: {{color: '#1e293b'}}}},
      x: {{ticks: {{color: '#94a3b8'}}, grid: {{display: false}}}}
    }},
    plugins: {{legend: {{display: false}}}}
  }}
}});

const qualCtx = document.getElementById('qualityChart');
new Chart(qualCtx, {{
  type: 'bar',
  data: {{
    labels: {tool_labels!r},
    datasets: [{{
      data: {tool_scores!r},
      backgroundColor: {tool_scores!r}.map(v => v === 1 ? '#22c55e' : '#ef4444'),
      borderRadius: 4,
    }}]
  }},
  options: {{
    scales: {{
      y: {{min: 0, max: 1, ticks: {{color: '#94a3b8', stepSize: 1}}, grid: {{color: '#1e293b'}}}},
      x: {{ticks: {{color: '#94a3b8'}}, grid: {{display: false}}}}
    }},
    plugins: {{legend: {{display: false}}}}
  }}
}});
</script>
</body>
</html>"""

    def save_dashboard(self, content: str, path: str = "docs/HEALTH_DASHBOARD.md"):
        """Save dashboard to file (works for both markdown and HTML content)."""
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

    html = generator.generate_html_dashboard()
    generator.save_dashboard(html, "docs/HEALTH_DASHBOARD.html")

    print("✅ Dashboard generation complete")


if __name__ == "__main__":
    main()
