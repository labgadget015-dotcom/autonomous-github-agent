#!/usr/bin/env python3
"""
CHANGELOG Generator
Automatically generates CHANGELOG.md from git commit history.
"""

import re
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Tuple


class ChangelogGenerator:
    """Generate changelog from git history."""
    
    # Conventional commit types
    COMMIT_TYPES = {
        'feat': ('Features', '✨'),
        'fix': ('Bug Fixes', '🐛'),
        'docs': ('Documentation', '📚'),
        'style': ('Code Style', '💎'),
        'refactor': ('Code Refactoring', '♻️'),
        'perf': ('Performance Improvements', '⚡'),
        'test': ('Tests', '✅'),
        'build': ('Build System', '🔧'),
        'ci': ('CI/CD', '👷'),
        'chore': ('Chores', '🔨'),
        'revert': ('Reverts', '⏪'),
        'security': ('Security', '🔒'),
    }
    
    def __init__(self):
        self.commits = []
        
    def get_git_tags(self) -> List[str]:
        """Get all git tags sorted by date."""
        try:
            result = subprocess.run(
                ['git', 'tag', '-l', '--sort=-version:refname'],
                capture_output=True,
                text=True,
                check=True
            )
            return [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
        except subprocess.CalledProcessError:
            return []
            
    def get_commits_between(self, from_ref: str = None, to_ref: str = 'HEAD') -> List[Dict]:
        """Get commits between two refs."""
        cmd = ['git', 'log', '--pretty=format:%H|%s|%an|%ae|%ad', '--date=short']
        
        if from_ref:
            cmd.append(f'{from_ref}..{to_ref}')
        else:
            cmd.append(to_ref)
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = []
            
            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue
                    
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        'hash': parts[0][:7],
                        'message': parts[1],
                        'author': parts[2],
                        'email': parts[3],
                        'date': parts[4]
                    })
                    
            return commits
        except subprocess.CalledProcessError:
            return []
            
    def parse_commit_type(self, message: str) -> Tuple[str, str, str, bool]:
        """Parse conventional commit message."""
        # Pattern: type(scope): message
        pattern = r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$'
        match = re.match(pattern, message)
        
        if match:
            commit_type = match.group(1)
            scope = match.group(2) or ''
            breaking = match.group(3) == '!'
            msg = match.group(4)
            return commit_type, scope, msg, breaking
        else:
            return 'other', '', message, False
            
    def group_commits(self, commits: List[Dict]) -> Dict[str, List[Dict]]:
        """Group commits by type."""
        groups = {}
        
        for commit in commits:
            commit_type, scope, message, breaking = self.parse_commit_type(commit['message'])
            
            # Add breaking change indicator
            if breaking:
                message = f"**BREAKING:** {message}"
                
            commit['parsed_type'] = commit_type
            commit['scope'] = scope
            commit['parsed_message'] = message
            commit['breaking'] = breaking
            
            if commit_type not in groups:
                groups[commit_type] = []
            groups[commit_type].append(commit)
            
        return groups
        
    def format_section(self, type_name: str, commits: List[Dict]) -> str:
        """Format a section of the changelog."""
        if type_name not in self.COMMIT_TYPES:
            return ''
            
        section_name, emoji = self.COMMIT_TYPES[type_name]
        lines = [f'\n### {emoji} {section_name}\n']
        
        for commit in commits:
            scope = f"**{commit['scope']}**: " if commit['scope'] else ''
            lines.append(f"- {scope}{commit['parsed_message']} ({commit['hash']})")
            
        return '\n'.join(lines)
        
    def generate_version_section(
        self,
        version: str,
        date: str,
        commits: List[Dict]
    ) -> str:
        """Generate changelog section for a version."""
        groups = self.group_commits(commits)
        
        sections = [f'\n## [{version}] - {date}\n']
        
        # Order by importance
        ordered_types = ['feat', 'fix', 'security', 'perf', 'refactor', 'docs', 'test', 'ci', 'build', 'chore']
        
        for commit_type in ordered_types:
            if commit_type in groups:
                section = self.format_section(commit_type, groups[commit_type])
                if section:
                    sections.append(section)
                    
        # Add any other types
        for commit_type in groups:
            if commit_type not in ordered_types:
                section = self.format_section(commit_type, groups[commit_type])
                if section:
                    sections.append(section)
                    
        return '\n'.join(sections)
        
    def generate_changelog(self, output_file: str = 'CHANGELOG.md') -> str:
        """Generate complete changelog."""
        tags = self.get_git_tags()
        
        changelog = [
            '# Changelog\n',
            'All notable changes to this project will be documented in this file.\n',
            'The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),',
            'and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n'
        ]
        
        if not tags:
            # No tags, show unreleased commits
            commits = self.get_commits_between()
            if commits:
                section = self.generate_version_section(
                    'Unreleased',
                    datetime.now().strftime('%Y-%m-%d'),
                    commits
                )
                changelog.append(section)
        else:
            # Unreleased changes
            unreleased = self.get_commits_between(tags[0])
            if unreleased:
                section = self.generate_version_section(
                    'Unreleased',
                    datetime.now().strftime('%Y-%m-%d'),
                    unreleased
                )
                changelog.append(section)
                
            # Tagged versions
            for i, tag in enumerate(tags):
                # Get date of tag
                try:
                    result = subprocess.run(
                        ['git', 'log', '-1', '--format=%ad', '--date=short', tag],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    tag_date = result.stdout.strip()
                except subprocess.CalledProcessError:
                    tag_date = datetime.now().strftime('%Y-%m-%d')
                    
                # Get commits for this tag
                from_ref = tags[i + 1] if i + 1 < len(tags) else None
                commits = self.get_commits_between(from_ref, tag)
                
                if commits:
                    section = self.generate_version_section(tag, tag_date, commits)
                    changelog.append(section)
                    
        changelog_text = '\n'.join(changelog)
        
        # Save to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(changelog_text)
            print(f"✅ Changelog generated: {output_file}")
        except Exception as e:
            print(f"❌ Error saving changelog: {e}")
            
        return changelog_text


def main():
    """Main execution."""
    generator = ChangelogGenerator()
    
    print("📝 Generating CHANGELOG...")
    changelog = generator.generate_changelog()
    
    print("\n✅ CHANGELOG generation complete!")
    

if __name__ == '__main__':
    main()
