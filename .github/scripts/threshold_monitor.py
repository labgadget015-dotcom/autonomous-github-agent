#!/usr/bin/env python3
"""
Threshold Monitor & Auto-Issue Creator
Monitors code quality metrics and automatically creates GitHub issues when thresholds are violated
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class ThresholdMonitor:
    """Monitor code quality thresholds and create issues for violations"""

    def __init__(self, config_path: str = ".github/config/analysis-config.yml"):
        self.config = self._load_config(config_path)
        self.violations = []

    def _load_config(self, path: str) -> Dict:
        """Load configuration file"""
        config_file = Path(path)
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        return self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            "thresholds": {
                "pylint": 8.0,
                "coverage": 80,
                "complexity": 10,
                "maintainability": 65,
                "security": "medium",
            },
            "escalation": {
                "enabled": True,
                "create_issue_on_failure": True,
                "severity_labels": {
                    "critical": "priority: critical",
                    "high": "priority: high",
                    "medium": "priority: medium",
                    "low": "priority: low",
                },
            },
        }

    def check_analysis_results(
        self, results_path: str = "analysis-results.json"
    ) -> List[Dict]:
        """Check analysis results against thresholds"""
        results_file = Path(results_path)
        if not results_file.exists():
            print(f"⚠️  Results file not found: {results_path}")
            return []

        with open(results_file) as f:
            results = json.load(f)

        violations = []

        # Check each tool's results
        for tool, data in results.get("tools", {}).items():
            if data["status"] == "failed":
                violations.append(
                    {
                        "type": "tool_failure",
                        "tool": tool,
                        "severity": "high",
                        "message": f"{tool} checks failed",
                        "details": data.get("errors", ""),
                    }
                )

        return violations

    def check_coverage(self, coverage_path: str = "coverage.json") -> Optional[Dict]:
        """Check test coverage against threshold"""
        coverage_file = Path(coverage_path)
        if not coverage_file.exists():
            return None

        with open(coverage_file) as f:
            coverage = json.load(f)

        total_coverage = coverage.get("totals", {}).get("percent_covered", 0)
        threshold = self.config["thresholds"]["coverage"]

        if total_coverage < threshold:
            return {
                "type": "coverage",
                "severity": "high" if total_coverage < threshold - 10 else "medium",
                "message": f"Test coverage below threshold: {total_coverage:.1f}% < {threshold}%",
                "current": total_coverage,
                "threshold": threshold,
            }

        return None

    def check_complexity(self, complexity_path: str = "complexity.json") -> List[Dict]:
        """Check code complexity against threshold"""
        complexity_file = Path(complexity_path)
        if not complexity_file.exists():
            return []

        with open(complexity_file) as f:
            complexity = json.load(f)

        violations = []
        threshold = self.config["thresholds"]["complexity"]

        for filepath, functions in complexity.items():
            for func in functions:
                if func.get("complexity", 0) > threshold:
                    violations.append(
                        {
                            "type": "complexity",
                            "severity": "medium",
                            "message": f"High complexity in {func['name']}",
                            "file": filepath,
                            "function": func["name"],
                            "complexity": func["complexity"],
                            "threshold": threshold,
                            "line": func.get("lineno", 0),
                        }
                    )

        return violations

    def check_security(self, bandit_path: str = "bandit-report.json") -> List[Dict]:
        """Check security scan results"""
        bandit_file = Path(bandit_path)
        if not bandit_file.exists():
            return []

        with open(bandit_file) as f:
            report = json.load(f)

        violations = []

        for issue in report.get("results", []):
            severity_map = {"HIGH": "critical", "MEDIUM": "high", "LOW": "medium"}

            severity = severity_map.get(issue.get("issue_severity", "LOW"), "low")

            violations.append(
                {
                    "type": "security",
                    "severity": severity,
                    "message": issue.get("issue_text", "Security issue"),
                    "file": issue.get("filename", "unknown"),
                    "line": issue.get("line_number", 0),
                    "confidence": issue.get("issue_confidence", "UNKNOWN"),
                    "cwe": issue.get("issue_cwe", {}).get("id", "N/A"),
                }
            )

        return violations

    def create_github_issue(self, violation: Dict) -> Dict:
        """Create GitHub issue data for violation"""
        severity = violation.get("severity", "medium")
        labels = [
            "code-quality",
            self.config["escalation"]["severity_labels"].get(
                severity, "priority: medium"
            ),
        ]

        # Add type-specific labels
        if violation["type"] == "security":
            labels.append("security")
        elif violation["type"] == "coverage":
            labels.append("testing")
        elif violation["type"] == "complexity":
            labels.append("refactoring")

        # Generate title
        title_map = {
            "security": f"🚨 Security Issue: {violation.get('message', 'Unknown')}",
            "coverage": f"📊 Low Test Coverage: {violation.get('current', 0):.1f}%",
            "complexity": f"🔧 High Complexity: {violation.get('function', 'Unknown')}",
            "tool_failure": f"❌ Code Quality Check Failed: {violation.get('tool', 'Unknown')}",
        }

        title = title_map.get(
            violation["type"], f"Code Quality Issue: {violation.get('message', '')}"
        )

        # Generate body
        body = self._generate_issue_body(violation)

        return {"title": title, "body": body, "labels": labels}

    def _generate_issue_body(self, violation: Dict) -> str:
        """Generate detailed issue body"""
        body = f"""## {violation.get('message', 'Code quality issue detected')}

**Type:** {violation['type'].upper()}  
**Severity:** {violation['severity'].upper()}  
**Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

"""

        if violation["type"] == "security":
            body += f"""### Security Details
- **File:** `{violation.get('file', 'unknown')}`
- **Line:** {violation.get('line', 'N/A')}
- **Confidence:** {violation.get('confidence', 'UNKNOWN')}
- **CWE:** {violation.get('cwe', 'N/A')}

### Remediation
Please review and fix this security vulnerability before merging.
"""

        elif violation["type"] == "coverage":
            body += f"""### Coverage Details
- **Current Coverage:** {violation.get('current', 0):.1f}%
- **Required Threshold:** {violation.get('threshold', 80)}%
- **Gap:** {violation.get('threshold', 80) - violation.get('current', 0):.1f}%

### Action Required
Add tests to improve coverage to meet the required threshold.
"""

        elif violation["type"] == "complexity":
            body += f"""### Complexity Details
- **File:** `{violation.get('file', 'unknown')}`
- **Function:** `{violation.get('function', 'unknown')}`
- **Line:** {violation.get('line', 'N/A')}
- **Complexity:** {violation.get('complexity', 0)}
- **Threshold:** {violation.get('threshold', 10)}

### Refactoring Suggestions
1. Break the function into smaller, focused functions
2. Extract complex conditional logic
3. Use early returns to reduce nesting
4. Consider using design patterns (Strategy, Command, etc.)
"""

        body += """
---
*This issue was automatically created by the code quality monitoring system.*
"""

        return body

    def save_violations(
        self, violations: List[Dict], path: str = "threshold-violations.json"
    ):
        """Save violations to file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_violations": len(violations),
            "violations": violations,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Saved {len(violations)} violations to {path}")

    def generate_summary_report(self, violations: List[Dict]) -> str:
        """Generate summary report of all violations"""
        if not violations:
            return "✅ No threshold violations detected!"

        report = f"""## 🚨 Threshold Violations Report

**Total Violations:** {len(violations)}

### Breakdown by Severity
"""

        severity_counts = {}
        for v in violations:
            severity = v.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        for severity, count in sorted(severity_counts.items()):
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                severity, "⚪"
            )
            report += f"- {emoji} **{severity.upper()}:** {count}\n"

        report += "\n### Breakdown by Type\n"

        type_counts = {}
        for v in violations:
            vtype = v.get("type", "unknown")
            type_counts[vtype] = type_counts.get(vtype, 0) + 1

        for vtype, count in sorted(type_counts.items()):
            report += f"- **{vtype}:** {count}\n"

        return report


def main():
    """Main entry point"""
    monitor = ThresholdMonitor()

    all_violations = []

    # Check analysis results
    print("🔍 Checking analysis results...")
    violations = monitor.check_analysis_results()
    all_violations.extend(violations)

    # Check coverage
    print("📊 Checking test coverage...")
    coverage_violation = monitor.check_coverage()
    if coverage_violation:
        all_violations.append(coverage_violation)

    # Check complexity
    print("🔧 Checking code complexity...")
    complexity_violations = monitor.check_complexity()
    all_violations.extend(complexity_violations)

    # Check security
    print("🔒 Checking security scan...")
    security_violations = monitor.check_security()
    all_violations.extend(security_violations)

    # Generate report
    report = monitor.generate_summary_report(all_violations)
    print("\n" + report)

    # Save violations
    if all_violations:
        monitor.save_violations(all_violations)

        # Create issue data for CI to use
        if monitor.config["escalation"]["create_issue_on_failure"]:
            issues = []
            for violation in all_violations:
                if violation["severity"] in ["critical", "high"]:
                    issues.append(monitor.create_github_issue(violation))

            with open("issues-to-create.json", "w") as f:
                json.dump(issues, f, indent=2)

            print(f"\n📝 Created {len(issues)} issue templates")

    # Exit with error if critical violations
    critical_count = len([v for v in all_violations if v["severity"] == "critical"])
    if critical_count > 0:
        print(f"\n❌ Found {critical_count} critical violations!")
        sys.exit(1)

    print("\n✅ Threshold monitoring complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
