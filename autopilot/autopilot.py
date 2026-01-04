#!/usr/bin/env python3
"""
GitHub Autopilot v0 - Automated Daily Repository Summary

Generates a comprehensive daily summary of GitHub repository activity including:
- Open issues and PRs
- Recent commits (last 24h)
- Priority-ranked "Top 3" action items

Usage:
    python autopilot.py [--config config.yaml] [--output DAILY_SUMMARY.md]

Requires:
    GITHUB_TOKEN environment variable for API access
"""

import os
import sys
import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from github import Github, GithubException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GitHubAutopilot:
    """Main autopilot orchestrator for GitHub repository summaries"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize autopilot with configuration"""
        self.start_time = time.time()
        self.config = self._load_config(config_path)
        self.github = self._init_github_client()
        self.repo_data = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        config_file = Path(__file__).parent / config_path
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _init_github_client(self) -> Github:
        """Initialize GitHub API client with authentication"""
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        return Github(token)
    
    def fetch_repo_data(self, owner: str, name: str) -> Dict[str, Any]:
        """Fetch issues, PRs, and recent commits for a single repository"""
        try:
            repo = self.github.get_repo(f"{owner}/{name}")
            since_time = datetime.now() - timedelta(hours=self.config['analysis']['lookback']['commits'])
            
            # Fetch data
            issues = list(repo.get_issues(state='open', sort='updated', direction='desc'))
            pulls = list(repo.get_pulls(state='open', sort='updated', direction='desc'))
            commits = list(repo.get_commits(since=since_time))
            
            # Filter out PRs from issues (GitHub API includes PRs in issues)
            issues = [i for i in issues if not i.pull_request]
            
            return {
                'name': name,
                'owner': owner,
                'issues': issues,
                'pulls': pulls,
                'commits': commits,
                'repo_obj': repo
            }
        except GithubException as e:
            print(f"Error fetching {owner}/{name}: {e}", file=sys.stderr)
            return None
    
    def fetch_all_repos(self) -> Dict[str, Dict]:
        """Fetch data for all configured repositories"""
        print(f"Fetching data for {len(self.config['repos'])} repositories...")
        
        for repo_config in self.config['repos']:
            owner = repo_config['owner']
            name = repo_config['name']
            priority = repo_config.get('priority', 'medium')
            
            print(f"  - {owner}/{name} ({priority})...")
            data = self.fetch_repo_data(owner, name)
            
            if data:
                data['priority'] = priority
                data['config'] = repo_config
                self.repo_data[f"{owner}/{name}"] = data
        
        print(f"Successfully fetched {len(self.repo_data)} repositories.\n")
        return self.repo_data
    
    def analyze_priorities(self) -> List[Dict]:
        """Analyze and score all items to generate top priorities"""
        weights = self.config['analysis']['priority_weights']
        all_items = []
        
        for repo_key, data in self.repo_data.items():
            priority_bonus = {
                'critical': weights.get('critical_repo', 5),
                'medium': 2,
                'low': 0
            }.get(data['priority'], 0)
            
            # Score issues
            for issue in data['issues']:
                score = weights.get('issue_count', 1) + priority_bonus
                
                # Check labels
                labels = [l.name.lower() for l in issue.labels]
                if 'urgent' in labels:
                    score += weights.get('urgent_label', 10)
                if 'enhancement' in labels:
                    score += weights.get('enhancement_label', 5)
                
                # Recent activity bonus
                if (datetime.now() - issue.updated_at.replace(tzinfo=None)).days < 1:
                    score += weights.get('recent_activity', 3)
                
                all_items.append({
                    'type': 'issue',
                    'repo': repo_key,
                    'number': issue.number,
                    'title': issue.title,
                    'url': issue.html_url,
                    'labels': labels,
                    'updated': issue.updated_at,
                    'score': score
                })
            
            # Score PRs
            for pr in data['pulls']:
                days_open = (datetime.now() - pr.created_at.replace(tzinfo=None)).days
                score = (days_open * weights.get('pr_age_days', 2)) + priority_bonus
                
                # Check labels
                labels = [l.name.lower() for l in pr.labels]
                if 'urgent' in labels:
                    score += weights.get('urgent_label', 10)
                
                all_items.append({
                    'type': 'pr',
                    'repo': repo_key,
                    'number': pr.number,
                    'title': pr.title,
                    'url': pr.html_url,
                    'labels': labels,
                    'age_days': days_open,
                    'updated': pr.updated_at,
                    'score': score
                })
        
        # Sort by score and return top N
        all_items.sort(key=lambda x: x['score'], reverse=True)
        return all_items[:self.config['analysis']['top_priorities']]
    
    def generate_summary(self, priorities: List[Dict]) -> str:
        """Generate markdown summary of repository activity"""
        runtime = time.time() - self.start_time
        now = datetime.now()
        
        summary = []
        summary.append("# GitHub Autopilot Daily Summary")
        summary.append(f"**Date:** {now.strftime('%Y-%m-%d')}")
        summary.append(f"**Time:** {now.strftime('%H:%M:%S GMT')}")
        summary.append(f"**Repos Scanned:** {len(self.repo_data)}")
        summary.append(f"**Runtime:** {runtime:.1f}s\n")
        summary.append("---\n")
        
        # Top Priorities
        summary.append("## 🚨 Top 3 Priorities\n")
        for i, item in enumerate(priorities, 1):
            item_type = "PR" if item['type'] == 'pr' else "Issue"
            summary.append(f"{i}. **[{item['repo']}]** {item_type} #{item['number']}: {item['title']}")
            if item.get('age_days'):
                summary.append(f"   - Open for {item['age_days']} days")
            if item.get('labels'):
                summary.append(f"   - Labels: {', '.join(item['labels'])}")
            summary.append(f"   - {item['url']}\n")
        
        summary.append("---\n")
        
        # Per-Repository Details
        summary.append("## 📊 Repository Activity\n")
        
        # Group by priority
        critical_repos = [(k, v) for k, v in self.repo_data.items() if v['priority'] == 'critical']
        medium_repos = [(k, v) for k, v in self.repo_data.items() if v['priority'] == 'medium']
        low_repos = [(k, v) for k, v in self.repo_data.items() if v['priority'] == 'low']
        
        for group_name, repos in [("Critical Repos", critical_repos), ("Medium Priority", medium_repos), ("Low Priority (Paused)", low_repos)]:
            if not repos:
                continue
            
            summary.append(f"### {group_name}\n")
            
            for repo_key, data in repos:
                issue_count = len(data['issues'])
                pr_count = len(data['pulls'])
                commit_count = len(data['commits'])
                
                summary.append(f"#### {repo_key} ({issue_count} issues, {pr_count} PRs)\n")
                
                if commit_count > 0:
                    summary.append(f"- **Recent Activity:** {commit_count} commits in last 24h")
                
                if pr_count > 0:
                    summary.append(f"- **Open PRs:**")
                    for pr in data['pulls'][:3]:  # Show max 3
                        summary.append(f"  - #{pr.number}: {pr.title}")
                
                if issue_count > 0:
                    urgent_issues = [i for i in data['issues'] if any('urgent' in l.name.lower() for l in i.labels)]
                    if urgent_issues:
                        summary.append(f"- **Urgent Issues:** {len(urgent_issues)} urgent")
                        for issue in urgent_issues[:3]:
                            summary.append(f"  - #{issue.number}: {issue.title}")
                    else:
                        summary.append(f"- **Open Issues:** {issue_count} total")
                
                notes = data['config'].get('notes')
                if notes:
                    summary.append(f"- **Notes:** {notes}")
                
                summary.append("")  # Blank line
        
        summary.append("---\n")
        summary.append(f"*Generated by GitHub Autopilot v0 - {now.strftime('%Y-%m-%d %H:%M:%S GMT')}*")
        
        return "\n".join(summary)
    
    def run(self, output_file: str = None) -> str:
        """Main execution: fetch data, analyze, generate summary"""
        print("=" * 60)
        print("GitHub Autopilot v0 - Daily Summary Generator")
        print("=" * 60 + "\n")
        
        # Fetch all repository data
        self.fetch_all_repos()
        
        # Analyze priorities
        print("Analyzing priorities...")
        priorities = self.analyze_priorities()
        
        # Generate summary
        print("Generating summary...\n")
        summary = self.generate_summary(priorities)
        
        # Output
        if self.config['output'].get('console', True):
            print("=" * 60)
            print(summary)
            print("=" * 60 + "\n")
        
        # Write to file
        output_path = output_file or self.config['output'].get('file', 'DAILY_SUMMARY.md')
        if output_path:
            output_file_path = Path(__file__).parent.parent / output_path
            with open(output_file_path, 'w') as f:
                f.write(summary)
            print(f"✅ Summary written to: {output_file_path}")
        
        runtime = time.time() - self.start_time
        print(f"\n✅ Complete in {runtime:.1f}s")
        
        return summary

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Autopilot - Daily Repository Summary')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--output', help='Output file path (default: from config)')
    
    args = parser.parse_args()
    
    try:
        autopilot = GitHubAutopilot(config_path=args.config)
        autopilot.run(output_file=args.output)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
