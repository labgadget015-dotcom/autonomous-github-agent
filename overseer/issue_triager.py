#!/usr/bin/env python3
"""
Issue Triager Module

Automates issue triaging, labeling, and prioritization based on
detected code patterns and content analysis.
"""

import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class IssueTriager:
    """
    Intelligent issue triager that automatically labels and prioritizes
    issues based on patterns and content analysis.
    """

    def __init__(self, repo_path: Path, config: dict):
        self.repo_path = repo_path
        self.config = config

        # Define label patterns
        self.label_patterns = {
            "bug": [
                r"\bbug\b",
                r"\berror\b",
                r"\bcrash\b",
                r"\bfail(s|ed|ure)?\b",
                r"\bbroken\b",
                r"\bnot working\b",
                r"\bissue\b",
            ],
            "enhancement": [
                r"\bfeature\b",
                r"\benhancement\b",
                r"\bimprovement\b",
                r"\badd\b",
                r"\bwould be nice\b",
                r"\brequest\b",
            ],
            "documentation": [
                r"\bdoc(s|umentation)?\b",
                r"\breadme\b",
                r"\bguide\b",
                r"\btutorial\b",
                r"\bexample\b",
            ],
            "performance": [
                r"\bperformance\b",
                r"\bslow\b",
                r"\boptimiz(e|ation)\b",
                r"\bspeed\b",
                r"\bfaster\b",
            ],
            "security": [
                r"\bsecurity\b",
                r"\bvulnerability\b",
                r"\bexploit\b",
                r"\bCVE\b",
                r"\bXSS\b",
                r"\bSQL injection\b",
            ],
            "dependencies": [
                r"\bdependenc(y|ies)\b",
                r"\bpackage\b",
                r"\bupgrade\b",
                r"\bversion\b",
                r"\brequirements\b",
            ],
            "ci/cd": [
                r"\bCI\b",
                r"\bCD\b",
                r"\bworkflow\b",
                r"\baction\b",
                r"\bbuild\b",
                r"\bdeploy(ment)?\b",
            ],
            "testing": [
                r"\btest(s|ing)?\b",
                r"\bcoverage\b",
                r"\bunit test\b",
                r"\bintegration test\b",
            ],
        }

        # Define priority patterns
        self.priority_patterns = {
            "critical": [
                r"\bcritical\b",
                r"\bsever(e|ity)\b",
                r"\bproduction\b",
                r"\bdown\b",
                r"\bblocking\b",
                r"\bsecurity\b",
            ],
            "high": [
                r"\burgent\b",
                r"\bimportant\b",
                r"\basap\b",
                r"\bbreaking\b",
                r"\bmajor\b",
            ],
            "medium": [r"\bmoderate\b", r"\bnormal\b", r"\bshould\b"],
            "low": [
                r"\bminor\b",
                r"\bnice to have\b",
                r"\bwould like\b",
                r"\beventually\b",
                r"\bsomeday\b",
            ],
        }

    def process(self) -> dict[str, Any]:
        """
        Process and triage issues.

        Returns:
            Dictionary containing triage results
        """
        logger.info("Processing issue triage...")

        results = {"processed": 0, "labeled": 0, "prioritized": 0, "patterns": []}

        # In a real implementation, this would fetch issues from GitHub API
        # For now, we'll create recommendations for the triaging system

        results["patterns"] = self._detect_common_patterns()

        logger.info(
            f"Issue triage complete. Detected {len(results['patterns'])} patterns"
        )

        return results

    def analyze_issue_content(self, title: str, body: str) -> dict[str, Any]:
        """
        Analyze issue content to suggest labels and priority.

        Handles Unicode text (e.g. Cyrillic, CJK characters) and special
        characters such as ``@#$%^&*()`` safely.  Input strings are
        NFC-normalised before analysis so that visually identical Unicode
        sequences compare equally.

        Args:
            title: Issue title (may contain Unicode or special characters)
            body: Issue body (may contain Unicode or special characters)

        Returns:
            Dictionary with suggested labels and priority
        """
        # NFC normalisation ensures consistent Unicode representation
        # (e.g. combining characters are collapsed to their precomposed form).
        title = unicodedata.normalize("NFC", title)
        body = unicodedata.normalize("NFC", body)
        content = f"{title} {body}".lower()

        suggested_labels = []
        suggested_priority = "medium"  # default

        # Detect labels
        for label, patterns in self.label_patterns.items():
            if self._matches_patterns(content, patterns):
                suggested_labels.append(label)

        # Detect priority
        for priority, patterns in self.priority_patterns.items():
            if self._matches_patterns(content, patterns):
                suggested_priority = priority
                break  # Use first matching priority

        return {
            "labels": suggested_labels,
            "priority": suggested_priority,
            "confidence": self._calculate_confidence(content, suggested_labels),
        }

    def _matches_patterns(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the patterns.

        Uses ``re.UNICODE`` (the Python 3 default) explicitly so that ``\\w``
        and ``\\b`` are Unicode-aware and correctly handle non-ASCII content.
        """
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE | re.UNICODE):
                return True
        return False

    def _calculate_confidence(self, content: str, labels: list[str]) -> float:
        """Calculate confidence score for label suggestions.

        Pattern matching uses ``re.UNICODE`` explicitly so that ``\\w`` / ``\\b``
        behave correctly for non-ASCII content.
        """
        if not labels:
            return 0.0

        # Simple confidence based on number of pattern matches
        match_count = 0
        total_patterns = 0

        for label in labels:
            patterns = self.label_patterns.get(label, [])
            total_patterns += len(patterns)
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE | re.UNICODE):
                    match_count += 1

        return min(1.0, match_count / max(1, len(labels)))

    def _detect_common_patterns(self) -> list[dict]:
        """Detect common patterns in repository for better triaging"""
        patterns = []

        # Check for common issue templates
        issue_template_dir = self.repo_path / ".github" / "ISSUE_TEMPLATE"
        if issue_template_dir.exists():
            templates = list(issue_template_dir.glob("*.md")) + list(
                issue_template_dir.glob("*.yml")
            )

            patterns.append(
                {
                    "type": "issue_templates",
                    "count": len(templates),
                    "recommendation": f"Found {len(templates)} issue templates. These help with auto-labeling.",
                }
            )
        else:
            patterns.append(
                {
                    "type": "missing_templates",
                    "recommendation": "No issue templates found. Consider adding templates for bug reports, feature requests, etc.",
                }
            )

        # Check for CODEOWNERS file
        codeowners = self.repo_path / ".github" / "CODEOWNERS"
        if not codeowners.exists():
            patterns.append(
                {
                    "type": "missing_codeowners",
                    "recommendation": "Add CODEOWNERS file to auto-assign issues based on file paths.",
                }
            )

        return patterns
