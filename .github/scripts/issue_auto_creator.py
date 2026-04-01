#!/usr/bin/env python3
"""
Issue Auto-Creator for Code Quality Escalation
Automatically creates GitHub issues when code quality, coverage, or security metrics
fall below configured thresholds.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests


class IssueAutoCreator:
    """Auto-creates GitHub issues for quality degradation."""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo = os.getenv('GITHUB_REPOSITORY')
        self.run_id = os.getenv('GITHUB_RUN_ID', 'unknown')
        self.workflow_url = f"https://github.com/{self.repo}/actions/runs/{self.run_id}"
        self.api_base = 'https://api.github.com'
        
        # Thresholds
        self.quality_threshold = float(os.getenv('QUALITY_THRESHOLD', '7.0'))
        self.coverage_threshold = float(os.getenv('COVERAGE_THRESHOLD', '80.0'))
        self.complexity_threshold = int(os.getenv('COMPLEXITY_THRESHOLD', '10'))
        
        if not all([self.github_token, self.repo]):
            print("⚠️  Missing required environment variables")
            sys.exit(0)
    
    def _make_request(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make authenticated POST request to GitHub API."""
        url = f"{self.api_base}/repos/{self.repo}/{endpoint}"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️  API request failed: {e}")
            return None
    
    def check_quality_metrics(self, summary_path: Path) -> List[Dict]:
        """Check quality metrics and generate issues."""
        issues_to_create = []
        
        if not summary_path.exists():
            print(f"⚠️  Summary file not found: {summary_path}")
            return issues_to_create
        
        try:
            with open(summary_path) as f:
                data = json.load(f)
            
            # Check quality score
            quality_score = data.get('quality_score', 10.0)
            if quality_score < self.quality_threshold:
                issues_to_create.append({
                    'title': f'⚠️  Code Quality Below Threshold ({quality_score:.1f}/{self.quality_threshold})',
                    'body': self._generate_quality_issue_body(data, quality_score),
                    'labels': ['code-quality', 'automated', 'urgent']
                })
            
            # Check for critical security vulnerabilities
            security_issues = data.get('security', {})
            high_severity = security_issues.get('high', 0)
            if high_severity > 0:
                issues_to_create.append({
                    'title': f'🔴 {high_severity} High-Severity Security Vulnerabilities Detected',
                    'body': self._generate_security_issue_body(security_issues),
                    'labels': ['security', 'automated', 'critical']
                })
            
            # Check complexity
            high_complexity_functions = data.get('high_complexity_functions', [])
            if len(high_complexity_functions) > 5:
                issues_to_create.append({
                    'title': f'🟡 {len(high_complexity_functions)} High-Complexity Functions Detected',
                    'body': self._generate_complexity_issue_body(high_complexity_functions),
                    'labels': ['code-complexity', 'automated', 'refactoring-needed']
                })
        
        except Exception as e:
            print(f"⚠️  Error checking metrics: {e}")
        
        return issues_to_create
    
    def _generate_quality_issue_body(self, data: Dict, score: float) -> str:
        """Generate issue body for quality degradation."""
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        body = f"""## Code Quality Alert
        
**Date**: {date}
**Quality Score**: {score:.1f}/{self.quality_threshold} ⚠️  
**Status**: Below threshold

### Summary

Code quality has fallen below the acceptable threshold. This requires immediate attention.

### Metrics

"""
        
        # Add specific metrics if available
        if 'pylint_issues' in data:
            body += f"- **Pylint Issues**: {data['pylint_issues']}\\n"
        if 'flake8_issues' in data:
            body += f"- **Flake8 Issues**: {data['flake8_issues']}\\n"
        if 'mypy_issues' in data:
            body += f"- **MyPy Errors**: {data['mypy_issues']}\\n"
        
        body += f"""

### Action Required

1. Review the [workflow run]({self.workflow_url}) for detailed analysis
2. Address high-priority issues first
3. Run local analysis: `python .github/scripts/async_parallel_analyzer.py`
4. Ensure all checks pass before merging new code

### Resources

- [Code Quality Workflow]({self.workflow_url})
- Pre-commit hooks: `pre-commit run --all-files`
"""
        
        return body
    
    def _generate_security_issue_body(self, security_data: Dict) -> str:
        """Generate issue body for security vulnerabilities."""
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        body = f"""## 🔒 Security Alert
        
**Date**: {date}
**Severity**: HIGH 🔴

### Vulnerability Summary

| Severity | Count |
|----------|-------|
| HIGH     | {security_data.get('high', 0)} |
| MEDIUM   | {security_data.get('medium', 0)} |
| LOW      | {security_data.get('low', 0)} |

### Immediate Actions Required

1. **Review all HIGH severity issues immediately**
2. Check [security scan results]({self.workflow_url})
3. Update dependencies if applicable
4. Run: `bandit -r .github/scripts` locally

### Resources

- [Security Workflow]({self.workflow_url})
- [Bandit Documentation](https://bandit.readthedocs.io/)
"""
        
        return body
    
    def _generate_complexity_issue_body(self, functions: List[Dict]) -> str:
        """Generate issue body for high complexity."""
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        body = f"""## 🔧 Code Complexity Alert
        
**Date**: {date}
**High-Complexity Functions**: {len(functions)}

### Functions Requiring Refactoring

"""
        
        # List top 10 most complex functions
        for func in functions[:10]:
            body += f"- `{func.get('name', 'unknown')}` (Complexity: {func.get('complexity', 0)})\\n"
        
        body += f"""

### Recommended Actions

1. Refactor functions with complexity > {self.complexity_threshold}
2. Split large functions into smaller, focused units
3. Add unit tests for complex logic
4. Review the [complexity report]({self.workflow_url})

### Resources

- [Radon Documentation](https://radon.readthedocs.io/)
- [Cyclomatic Complexity Guide](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
"""
        
        return body
    
    def create_issues(self, issues: List[Dict]) -> None:
        """Create GitHub issues."""
        if not issues:
            print("✅ No issues to create")
            return
        
        for issue_data in issues:
            result = self._make_request('issues', issue_data)
            if result:
                issue_number = result.get('number', 'unknown')
                print(f"✅ Created issue #{issue_number}: {issue_data['title']}")
            else:
                print(f"❌ Failed to create issue: {issue_data['title']}")
    
    def run(self, summary_path: Path) -> None:
        """Main execution."""
        print("\\n🔍 Checking for quality degradation...\\n")
        
        issues = self.check_quality_metrics(summary_path)
        
        if issues:
            print(f"\\n📋 Creating {len(issues)} issue(s)...\\n")
            self.create_issues(issues)
        else:
            print("✅ All metrics within acceptable ranges\\n")


def main():
    """Main entry point."""
    summary_path = Path(os.getenv('SUMMARY_PATH', 'reports/analysis-summary.json'))
    
    creator = IssueAutoCreator()
    creator.run(summary_path)


if __name__ == '__main__':
    main()
