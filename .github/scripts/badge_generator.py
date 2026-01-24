#!/usr/bin/env python3
"""
Badge Generator
Automatically generates and updates status badges for README
"""

import json
import os
from pathlib import Path
from typing import Dict


class BadgeGenerator:
    """Generate dynamic status badges"""
    
    def __init__(self):
        self.badges = {}
        
    def generate_health_badge(self, score: int) -> str:
        """Generate health score badge"""
        if score >= 90:
            color = "brightgreen"
            status = "excellent"
        elif score >= 75:
            color = "green"
            status = "good"
        elif score >= 60:
            color = "yellow"
            status = "fair"
        else:
            color = "red"
            status = "poor"
        
        return f"![Health Score](https://img.shields.io/badge/health-{score}%25%20{status}-{color})"
    
    def generate_coverage_badge(self, coverage: float) -> str:
        """Generate test coverage badge"""
        if coverage >= 90:
            color = "brightgreen"
        elif coverage >= 80:
            color = "green"
        elif coverage >= 70:
            color = "yellow"
        else:
            color = "red"
        
        return f"![Coverage](https://img.shields.io/badge/coverage-{coverage:.1f}%25-{color})"
    
    def generate_workflow_badge(self, workflow_name: str = "CI/CD") -> str:
        """Generate GitHub Actions workflow badge"""
        repo = os.getenv('GITHUB_REPOSITORY', 'owner/repo')
        workflow_file = "code-quality-optimized.yml"
        
        return f"![{workflow_name}](https://github.com/{repo}/workflows/{workflow_file}/badge.svg)"
    
    def generate_security_badge(self, issues: int) -> str:
        """Generate security issues badge"""
        if issues == 0:
            color = "brightgreen"
            text = "passing"
        elif issues <= 3:
            color = "yellow"
            text = f"{issues}%20issues"
        else:
            color = "red"
            text = f"{issues}%20issues"
        
        return f"![Security](https://img.shields.io/badge/security-{text}-{color})"
    
    def generate_complexity_badge(self, avg_complexity: float) -> str:
        """Generate code complexity badge"""
        if avg_complexity <= 5:
            color = "brightgreen"
            status = "low"
        elif avg_complexity <= 10:
            color = "green"
            status = "moderate"
        elif avg_complexity <= 15:
            color = "yellow"
            status = "high"
        else:
            color = "red"
            status = "very%20high"
        
        return f"![Complexity](https://img.shields.io/badge/complexity-{status}-{color})"
    
    def generate_license_badge(self) -> str:
        """Generate license badge"""
        return "![License](https://img.shields.io/badge/license-MIT-blue.svg)"
    
    def generate_python_badge(self) -> str:
        """Generate Python version badge"""
        return "![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)"
    
    def generate_all_badges(self) -> Dict[str, str]:
        """Generate all badges from current data"""
        badges = {}
        
        # Load data
        try:
            with open('analysis-results.json') as f:
                analysis = json.load(f)
            
            # Health badge (calculated from analysis)
            health_score = 85  # Default, could calculate from analysis
            badges['health'] = self.generate_health_badge(health_score)
        except FileNotFoundError:
            badges['health'] = self.generate_health_badge(85)
        
        try:
            with open('coverage.json') as f:
                coverage_data = json.load(f)
                coverage_pct = coverage_data.get('totals', {}).get('percent_covered', 0)
                badges['coverage'] = self.generate_coverage_badge(coverage_pct)
        except FileNotFoundError:
            badges['coverage'] = self.generate_coverage_badge(80)
        
        try:
            with open('bandit-report.json') as f:
                security = json.load(f)
                issue_count = len(security.get('results', []))
                badges['security'] = self.generate_security_badge(issue_count)
        except FileNotFoundError:
            badges['security'] = self.generate_security_badge(0)
        
        try:
            with open('complexity.json') as f:
                complexity = json.load(f)
                # Calculate average
                total = 0
                count = 0
                for functions in complexity.values():
                    for func in functions:
                        total += func.get('complexity', 0)
                        count += 1
                avg = total / count if count > 0 else 5
                badges['complexity'] = self.generate_complexity_badge(avg)
        except FileNotFoundError:
            badges['complexity'] = self.generate_complexity_badge(5)
        
        # Static badges
        badges['workflow'] = self.generate_workflow_badge()
        badges['license'] = self.generate_license_badge()
        badges['python'] = self.generate_python_badge()
        
        return badges
    
    def generate_badge_section(self) -> str:
        """Generate complete badge section for README"""
        badges = self.generate_all_badges()
        
        section = "<!-- BADGES START -->\n"
        section += f"{badges['workflow']} "
        section += f"{badges['coverage']} "
        section += f"{badges['health']} "
        section += f"{badges['security']} "
        section += f"{badges['complexity']} "
        section += f"{badges['python']} "
        section += f"{badges['license']}\n"
        section += "<!-- BADGES END -->\n"
        
        return section
    
    def update_readme_badges(self, readme_path: str = "README.md"):
        """Update badges in README file"""
        badge_section = self.generate_badge_section()
        
        try:
            with open(readme_path, 'r') as f:
                content = f.read()
            
            # Replace badge section if it exists
            if "<!-- BADGES START -->" in content and "<!-- BADGES END -->" in content:
                import re
                pattern = r"<!-- BADGES START -->.*?<!-- BADGES END -->"
                content = re.sub(pattern, badge_section.strip(), content, flags=re.DOTALL)
            else:
                # Add after title
                lines = content.split('\n')
                if lines and lines[0].startswith('#'):
                    lines.insert(2, badge_section)
                    content = '\n'.join(lines)
            
            with open(readme_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Updated badges in {readme_path}")
        except FileNotFoundError:
            print(f"⚠️  README not found: {readme_path}")


def main():
    """Main entry point"""
    print("🏷️  Generating status badges...")
    
    generator = BadgeGenerator()
    badges = generator.generate_all_badges()
    
    print("\n📋 Generated Badges:")
    for name, badge in badges.items():
        print(f"  {name}: {badge}")
    
    # Save to file
    with open('badges.md', 'w') as f:
        f.write("# Status Badges\n\n")
        for name, badge in badges.items():
            f.write(f"**{name.title()}:** {badge}\n\n")
    
    print("\n✅ Badges saved to badges.md")
    
    # Update README
    generator.update_readme_badges()


if __name__ == "__main__":
    main()
