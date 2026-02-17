"""Commit Summarization System

This module generates intelligent summaries of commits and repository changes
using NLP techniques and pattern matching (simplified version without heavy models).
"""

import re
import logging
from typing import Dict, List, Any, Set, Tuple
from collections import Counter, defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class CommitSummarizer:
    """Generate intelligent summaries of commits and changes."""
    
    def __init__(self):
        """Initialize the commit summarizer."""
        # Action verbs for categorization
        self.action_verbs = {
            'add': 'additions',
            'create': 'additions',
            'implement': 'additions',
            'introduce': 'additions',
            'remove': 'removals',
            'delete': 'removals',
            'drop': 'removals',
            'fix': 'fixes',
            'resolve': 'fixes',
            'patch': 'fixes',
            'correct': 'fixes',
            'update': 'updates',
            'modify': 'updates',
            'change': 'updates',
            'refactor': 'refactoring',
            'restructure': 'refactoring',
            'reorganize': 'refactoring',
            'improve': 'improvements',
            'optimize': 'improvements',
            'enhance': 'improvements',
            'test': 'testing',
            'doc': 'documentation',
            'document': 'documentation',
        }
        
        # Component patterns
        self.component_patterns = [
            (r'\b(api|endpoint|route)s?\b', 'API'),
            (r'\b(ui|interface|frontend)\b', 'UI'),
            (r'\b(database|db|schema|migration)s?\b', 'Database'),
            (r'\b(test|spec)s?\b', 'Tests'),
            (r'\b(doc|documentation|readme)\b', 'Documentation'),
            (r'\b(auth|authentication|authorization)\b', 'Authentication'),
            (r'\b(security|vulnerability|exploit)\b', 'Security'),
            (r'\b(performance|optimization|speed)\b', 'Performance'),
            (r'\b(config|configuration|setting)s?\b', 'Configuration'),
            (r'\b(deploy|deployment|release)\b', 'Deployment'),
        ]
    
    def generate_summary(self, commits: List[Any]) -> Dict[str, Any]:
        """Generate intelligent summary from commits.
        
        Args:
            commits: List of commit objects
            
        Returns:
            Dictionary with summary and insights
        """
        if not commits:
            return self._empty_summary()
        
        # Extract information from commits
        messages = []
        authors = set()
        files_changed = set()
        total_additions = 0
        total_deletions = 0
        
        for commit in commits:
            # Get commit message
            commit_obj = getattr(commit, 'commit', commit)
            message = getattr(commit_obj, 'message', '')
            messages.append(message)
            
            # Get author
            author = getattr(commit_obj, 'author', None)
            if author:
                author_name = getattr(author, 'name', None)
                if author_name:
                    authors.add(author_name)
            
            # Get stats
            stats = getattr(commit, 'stats', {})
            if isinstance(stats, dict):
                total_additions += stats.get('additions', 0)
                total_deletions += stats.get('deletions', 0)
            else:
                total_additions += getattr(stats, 'additions', 0)
                total_deletions += getattr(stats, 'deletions', 0)
            
            # Get files
            files = getattr(commit, 'files', [])
            for f in (files if hasattr(files, '__iter__') else []):
                filename = getattr(f, 'filename', str(f))
                files_changed.add(filename)
        
        # Analyze commits
        themes = self._extract_themes(messages)
        actions = self._categorize_actions(messages)
        components = self._identify_components(messages)
        
        # Generate summary text
        summary_text = self._generate_summary_text(
            len(commits), authors, themes, actions, components,
            total_additions, total_deletions, len(files_changed)
        )
        
        # Generate insights
        insights = self._generate_insights(
            commits, themes, actions, components
        )
        
        # Recommend actions
        recommended_actions = self._recommend_actions(insights, themes, actions)
        
        return {
            'summary': summary_text,
            'key_themes': themes,
            'action_breakdown': actions,
            'components_affected': components,
            'statistics': {
                'commit_count': len(commits),
                'author_count': len(authors),
                'files_changed': len(files_changed),
                'lines_added': total_additions,
                'lines_deleted': total_deletions,
                'net_change': total_additions - total_deletions
            },
            'insights': insights,
            'recommended_actions': recommended_actions
        }
    
    def _extract_themes(self, messages: List[str]) -> List[Dict[str, Any]]:
        """Extract key themes from commit messages.
        
        Args:
            messages: List of commit messages
            
        Returns:
            List of theme dictionaries
        """
        # Combine all messages
        combined = ' '.join(messages).lower()
        
        # Extract words
        words = re.findall(r'\b[a-z]{4,}\b', combined)
        
        # Count frequencies
        word_counts = Counter(words)
        
        # Filter common words
        stop_words = {
            'this', 'that', 'with', 'from', 'have', 'been',
            'were', 'their', 'there', 'would', 'could', 'should'
        }
        
        themes = []
        for word, count in word_counts.most_common(10):
            if word not in stop_words and count > 1:
                themes.append({
                    'theme': word,
                    'frequency': count,
                    'importance': min(count / len(messages), 1.0)
                })
        
        return themes[:5]  # Top 5 themes
    
    def _categorize_actions(self, messages: List[str]) -> Dict[str, int]:
        """Categorize commit actions.
        
        Args:
            messages: List of commit messages
            
        Returns:
            Dictionary of action categories and counts
        """
        actions = defaultdict(int)
        
        for message in messages:
            message_lower = message.lower()
            
            # Check each action verb
            for verb, category in self.action_verbs.items():
                if verb in message_lower:
                    actions[category] += 1
        
        return dict(actions)
    
    def _identify_components(self, messages: List[str]) -> Dict[str, int]:
        """Identify affected components.
        
        Args:
            messages: List of commit messages
            
        Returns:
            Dictionary of components and mention counts
        """
        components = defaultdict(int)
        
        for message in messages:
            message_lower = message.lower()
            
            # Check each component pattern
            for pattern, component_name in self.component_patterns:
                if re.search(pattern, message_lower):
                    components[component_name] += 1
        
        return dict(sorted(components.items(), key=lambda x: x[1], reverse=True))
    
    def _generate_summary_text(self, commit_count: int, authors: Set[str],
                               themes: List[Dict], actions: Dict[str, int],
                               components: Dict[str, int],
                               additions: int, deletions: int,
                               files_changed: int) -> str:
        """Generate human-readable summary text.
        
        Args:
            commit_count: Number of commits
            authors: Set of author names
            themes: List of themes
            actions: Action breakdown
            components: Component breakdown
            additions: Lines added
            deletions: Lines deleted
            files_changed: Number of files changed
            
        Returns:
            Summary text
        """
        parts = []
        
        # Overall stats
        parts.append(f"{commit_count} commit{'s' if commit_count != 1 else ''}")
        
        if authors:
            author_count = len(authors)
            parts.append(f"by {author_count} author{'s' if author_count != 1 else ''}")
        
        parts.append(f"affecting {files_changed} file{'s' if files_changed != 1 else ''}")
        
        summary = " ".join(parts) + "."
        
        # Code changes
        if additions > 0 or deletions > 0:
            summary += f" Total changes: +{additions} -{deletions} lines."
        
        # Main actions
        if actions:
            top_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)[:3]
            action_text = ", ".join([f"{count} {action}" for action, count in top_actions])
            summary += f" Primary actions: {action_text}."
        
        # Components
        if components:
            top_components = list(components.keys())[:3]
            component_text = ", ".join(top_components)
            summary += f" Components affected: {component_text}."
        
        # Themes
        if themes:
            top_themes = [t['theme'] for t in themes[:3]]
            theme_text = ", ".join(top_themes)
            summary += f" Key themes: {theme_text}."
        
        return summary
    
    def _generate_insights(self, commits: List[Any], themes: List[Dict],
                          actions: Dict[str, int], 
                          components: Dict[str, int]) -> List[str]:
        """Generate actionable insights.
        
        Args:
            commits: List of commits
            themes: Extracted themes
            actions: Action breakdown
            components: Component breakdown
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Check for high activity
        if len(commits) > 20:
            insights.append(f"High activity period with {len(commits)} commits")
        
        # Check for fixes
        fix_count = actions.get('fixes', 0)
        if fix_count > len(commits) * 0.3:
            insights.append(f"Significant bug fixing activity ({fix_count} fixes)")
        
        # Check for refactoring
        refactor_count = actions.get('refactoring', 0)
        if refactor_count > 0:
            insights.append(f"Code quality improvements through refactoring")
        
        # Check for security
        if 'Security' in components:
            insights.append("Security-related changes detected - review recommended")
        
        # Check for breaking changes
        for commit in commits:
            message = getattr(getattr(commit, 'commit', commit), 'message', '')
            if 'breaking' in message.lower() or 'BREAKING' in message:
                insights.append("Breaking changes detected - version bump may be needed")
                break
        
        # Check for test coverage
        if 'Tests' in components:
            insights.append("Test coverage maintained or improved")
        else:
            test_count = actions.get('testing', 0)
            if test_count == 0 and len(commits) > 5:
                insights.append("No test updates detected - consider adding tests")
        
        # Check for documentation
        if 'Documentation' in components:
            insights.append("Documentation updated")
        else:
            if len(commits) > 10:
                insights.append("Consider updating documentation for recent changes")
        
        return insights
    
    def _recommend_actions(self, insights: List[str], themes: List[Dict],
                          actions: Dict[str, int]) -> List[str]:
        """Recommend follow-up actions.
        
        Args:
            insights: Generated insights
            themes: Extracted themes
            actions: Action breakdown
            
        Returns:
            List of recommended actions
        """
        recommendations = []
        
        # Based on insights
        for insight in insights:
            if 'security' in insight.lower():
                recommendations.append("Run security audit and update dependencies")
            elif 'breaking' in insight.lower():
                recommendations.append("Update CHANGELOG and increment major version")
            elif 'test' in insight.lower() and 'no test' in insight.lower():
                recommendations.append("Add test coverage for new changes")
            elif 'documentation' in insight.lower() and 'consider' in insight.lower():
                recommendations.append("Update README and API documentation")
        
        # Based on action types
        if actions.get('fixes', 0) > 5:
            recommendations.append("Consider investigating root causes of bugs")
        
        if actions.get('additions', 0) > 10:
            recommendations.append("Review new code for quality and performance")
        
        # Default recommendations
        if not recommendations:
            recommendations.append("Review changes and update changelog")
            recommendations.append("Run full test suite before release")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary for no commits."""
        return {
            'summary': 'No commits to summarize',
            'key_themes': [],
            'action_breakdown': {},
            'components_affected': {},
            'statistics': {
                'commit_count': 0,
                'author_count': 0,
                'files_changed': 0,
                'lines_added': 0,
                'lines_deleted': 0,
                'net_change': 0
            },
            'insights': [],
            'recommended_actions': []
        }
    
    def summarize_by_author(self, commits: List[Any]) -> Dict[str, Dict]:
        """Generate per-author summaries.
        
        Args:
            commits: List of commits
            
        Returns:
            Dictionary of author -> summary
        """
        by_author = defaultdict(list)
        
        for commit in commits:
            commit_obj = getattr(commit, 'commit', commit)
            author = getattr(commit_obj, 'author', None)
            
            if author:
                author_name = getattr(author, 'name', 'Unknown')
                by_author[author_name].append(commit)
        
        summaries = {}
        for author, author_commits in by_author.items():
            summaries[author] = self.generate_summary(author_commits)
        
        return summaries


# Global summarizer instance
_global_summarizer = None

def get_summarizer() -> CommitSummarizer:
    """Get global summarizer instance."""
    global _global_summarizer
    if _global_summarizer is None:
        _global_summarizer = CommitSummarizer()
    return _global_summarizer


if __name__ == "__main__":
    # Example usage
    print("Commit Summarizer - Example Usage\n")
    print("="*70)
    
    # Mock commits
    class MockCommit:
        def __init__(self, message, author, additions, deletions):
            self.commit = type('CommitData', (), {
                'message': message,
                'author': type('Author', (), {'name': author})
            })
            self.stats = {'additions': additions, 'deletions': deletions}
            self.files = []
    
    commits = [
        MockCommit("Fix critical security vulnerability in auth", "Alice", 10, 5),
        MockCommit("Add new API endpoint for user management", "Bob", 150, 20),
        MockCommit("Update documentation for API changes", "Alice", 30, 5),
        MockCommit("Refactor database connection pooling", "Charlie", 80, 60),
        MockCommit("Add tests for new API endpoint", "Bob", 100, 0),
        MockCommit("Fix bug in user authentication flow", "Alice", 15, 8),
        MockCommit("Optimize database queries for performance", "Charlie", 40, 25),
    ]
    
    summarizer = CommitSummarizer()
    summary = summarizer.generate_summary(commits)
    
    print("Summary:")
    print(f"  {summary['summary']}\n")
    
    print("Key Themes:")
    for theme in summary['key_themes']:
        print(f"  - {theme['theme']} (frequency: {theme['frequency']})")
    
    print("\nAction Breakdown:")
    for action, count in summary['action_breakdown'].items():
        print(f"  - {action}: {count}")
    
    print("\nComponents Affected:")
    for component, count in summary['components_affected'].items():
        print(f"  - {component}: {count} mentions")
    
    print("\nStatistics:")
    for key, value in summary['statistics'].items():
        print(f"  - {key}: {value}")
    
    print("\nInsights:")
    for insight in summary['insights']:
        print(f"  • {insight}")
    
    print("\nRecommended Actions:")
    for i, action in enumerate(summary['recommended_actions'], 1):
        print(f"  {i}. {action}")
