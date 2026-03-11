"""NLP-Based Relevance Filtering

This module uses Natural Language Processing to analyze and filter
repository content for relevance and importance.
"""

import logging
import re
import threading
from collections import Counter
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class NLPRelevanceFilter:
    """NLP-based content analysis for relevance filtering."""

    def __init__(self):
        """Initialize the NLP relevance filter."""
        # Urgency indicators
        self.urgency_keywords = {
            "critical",
            "urgent",
            "asap",
            "immediately",
            "emergency",
            "blocker",
            "blocking",
            "broken",
            "crash",
            "security",
            "vulnerability",
            "exploit",
            "breach",
            "regression",
            "production",
            "prod",
            "down",
            "outage",
            "failure",
        }

        # Importance indicators
        self.importance_keywords = {
            "important",
            "priority",
            "critical",
            "essential",
            "required",
            "must",
            "need",
            "necessary",
            "breaking",
            "major",
        }

        # Technical action keywords
        self.action_keywords = {
            "fix",
            "resolve",
            "implement",
            "add",
            "remove",
            "update",
            "refactor",
            "optimize",
            "improve",
            "investigate",
            "debug",
            "test",
            "deploy",
            "release",
            "merge",
            "review",
        }

        # Noise indicators (low relevance)
        self.noise_keywords = {
            "typo",
            "formatting",
            "whitespace",
            "comment",
            "documentation",
            "readme",
            "style",
            "lint",
            "minor",
            "trivial",
            "cosmetic",
        }

        # Question indicators
        self.question_patterns = [
            r"\?$",  # Ends with ?
            r"^(how|what|why|when|where|who|can|should|would|could|is|are|do|does)",
            r"(help|question|wondering|confused|understand)",
        ]

    def analyze_relevance(self, text: str, context: str = "") -> dict[str, Any]:
        """Analyze text relevance using NLP techniques.

        Args:
            text: Text to analyze (issue/PR body, commit message, etc.)
            context: Additional context (e.g., repository description)

        Returns:
            Dictionary with relevance scores and analysis
        """
        if not text:
            return self._default_analysis()

        text_lower = text.lower()

        # Extract key information
        entities = self._extract_entities(text)
        keywords = self._extract_keywords(text_lower)

        # Calculate scores
        urgency_score = self._calculate_urgency(text_lower, keywords)
        importance_score = self._calculate_importance(text_lower, keywords)
        action_score = self._calculate_action_required(text_lower, keywords)
        noise_score = self._calculate_noise_level(text_lower, keywords)

        # Semantic similarity (simplified without external models)
        similarity = self._calculate_similarity(
            text_lower, context.lower() if context else ""
        )

        # Overall relevance score
        relevance_score = self._calculate_relevance_score(
            urgency_score, importance_score, action_score, noise_score, similarity
        )

        # Determine if action is required
        requires_action = action_score > 0.5 or urgency_score > 0.6

        # Check if it's a question
        is_question = self._is_question(text_lower)

        return {
            "relevance_score": round(relevance_score, 3),
            "urgency": round(urgency_score, 3),
            "importance": round(importance_score, 3),
            "action_required": requires_action,
            "is_question": is_question,
            "noise_level": round(noise_score, 3),
            "key_entities": entities,
            "top_keywords": keywords[:10],
            "sentiment": self._analyze_sentiment(text_lower),
        }

    def _extract_entities(self, text: str) -> list[str]:
        """Extract entities from text (simplified without spaCy).

        Args:
            text: Input text

        Returns:
            List of extracted entities
        """
        entities = []

        # Extract mentions (@username)
        mentions = re.findall(r"@(\w+)", text)
        entities.extend([f"@{m}" for m in mentions[:5]])

        # Extract issue/PR references (#123, GH-123)
        refs = re.findall(r"#(\d+)|GH-(\d+)", text)
        entities.extend([f"#{r[0] or r[1]}" for r in refs[:5]])

        # Extract URLs
        urls = re.findall(r"https?://[^\s]+", text)
        if urls:
            entities.append(f"{len(urls)} URLs")

        # Extract version numbers
        versions = re.findall(r"v?\d+\.\d+(?:\.\d+)?", text)
        entities.extend(versions[:3])

        return entities

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract important keywords from text.

        Args:
            text: Input text (lowercased)

        Returns:
            List of keywords sorted by importance
        """
        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "we",
            "they",
            "it",
        }

        # Extract words
        words = re.findall(r"\b[a-z]{3,}\b", text)

        # Filter and count
        filtered_words = [w for w in words if w not in stop_words]
        word_counts = Counter(filtered_words)

        # Return most common
        return [word for word, _ in word_counts.most_common(20)]

    def _calculate_urgency(self, text: str, keywords: list[str]) -> float:
        """Calculate urgency score.

        Args:
            text: Input text
            keywords: Extracted keywords

        Returns:
            Urgency score (0-1)
        """
        score = 0.0

        # Check for urgency keywords
        for keyword in self.urgency_keywords:
            if keyword in text:
                score += 0.2

        # Check for exclamation marks (indicates urgency)
        exclamations = text.count("!")
        score += min(exclamations * 0.1, 0.3)

        # Check for "asap", "urgent" in all caps
        if "URGENT" in text or "ASAP" in text:
            score += 0.3

        return min(score, 1.0)

    def _calculate_importance(self, text: str, keywords: list[str]) -> float:
        """Calculate importance score.

        Args:
            text: Input text
            keywords: Extracted keywords

        Returns:
            Importance score (0-1)
        """
        score = 0.0

        # Check for importance keywords
        for keyword in self.importance_keywords:
            if keyword in text:
                score += 0.15

        # Check for priority labels in text
        priority_patterns = [
            r"priority[:\s]*(high|critical|1|p0|p1)",
            r"(high|critical)\s*priority",
            r"severity[:\s]*(high|critical)",
        ]

        for pattern in priority_patterns:
            if re.search(pattern, text):
                score += 0.25

        return min(score, 1.0)

    def _calculate_action_required(self, text: str, keywords: list[str]) -> float:
        """Calculate action required score.

        Args:
            text: Input text
            keywords: Extracted keywords

        Returns:
            Action score (0-1)
        """
        score = 0.0

        # Check for action keywords
        for keyword in self.action_keywords:
            if keyword in text:
                score += 0.1

        # Check for imperative mood (commands)
        imperative_patterns = [
            r"^(please\s+)?(fix|resolve|implement|add|remove|update)",
            r"(need to|should|must|have to)\s+\w+",
        ]

        for pattern in imperative_patterns:
            if re.search(pattern, text):
                score += 0.2

        return min(score, 1.0)

    def _calculate_noise_level(self, text: str, keywords: list[str]) -> float:
        """Calculate noise level (inverse of signal quality).

        Args:
            text: Input text
            keywords: Extracted keywords

        Returns:
            Noise score (0-1, higher = more noise)
        """
        score = 0.0

        # Check for noise keywords
        for keyword in self.noise_keywords:
            if keyword in text:
                score += 0.15

        # Very short text is often noise
        if len(text) < 50:
            score += 0.2

        # Too many special characters or emojis
        special_chars = len(re.findall(r"[^a-zA-Z0-9\s]", text))
        if special_chars > len(text) * 0.2:
            score += 0.15

        return min(score, 1.0)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between texts (simplified).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0

        # Extract word sets
        words1 = set(re.findall(r"\b[a-z]{3,}\b", text1))
        words2 = set(re.findall(r"\b[a-z]{3,}\b", text2))

        # Jaccard similarity
        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _calculate_relevance_score(
        self,
        urgency: float,
        importance: float,
        action: float,
        noise: float,
        similarity: float,
    ) -> float:
        """Calculate overall relevance score.

        Args:
            urgency: Urgency score
            importance: Importance score
            action: Action required score
            noise: Noise level
            similarity: Semantic similarity

        Returns:
            Overall relevance score (0-1)
        """
        # Weighted combination
        score = (
            urgency * 0.25
            + importance * 0.25
            + action * 0.20
            + similarity * 0.15
            + (1 - noise) * 0.15  # Inverse noise
        )

        return max(0.0, min(1.0, score))

    def _is_question(self, text: str) -> bool:
        """Check if text is a question.

        Args:
            text: Input text

        Returns:
            True if text appears to be a question
        """
        for pattern in self.question_patterns:
            if re.search(pattern, text.strip(), re.IGNORECASE):
                return True
        return False

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment (simplified).

        Args:
            text: Input text

        Returns:
            Sentiment string (positive/negative/neutral)
        """
        positive_words = {
            "great",
            "good",
            "excellent",
            "awesome",
            "perfect",
            "thanks",
            "thank",
            "appreciate",
            "love",
            "nice",
            "helpful",
            "works",
        }

        negative_words = {
            "bad",
            "broken",
            "wrong",
            "error",
            "fail",
            "issue",
            "problem",
            "bug",
            "crash",
            "doesn't",
            "not working",
            "horrible",
            "terrible",
        }

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"

    def _default_analysis(self) -> dict[str, Any]:
        """Return default analysis for empty/invalid input."""
        return {
            "relevance_score": 0.0,
            "urgency": 0.0,
            "importance": 0.0,
            "action_required": False,
            "is_question": False,
            "noise_level": 1.0,
            "key_entities": [],
            "top_keywords": [],
            "sentiment": "neutral",
        }

    def filter_items(
        self,
        items: list[Any],
        min_relevance: float = 0.3,
        get_text: Callable[..., Any] | None = None,
    ) -> list[tuple[Any, dict]]:
        """Filter items by relevance.

        Args:
            items: List of items to filter
            min_relevance: Minimum relevance score
            get_text: Function to extract text from item

        Returns:
            List of (item, analysis) tuples for relevant items
        """
        if get_text is None:

            def get_text(x):
                return str(x)

        relevant_items = []

        for item in items:
            text = get_text(item)
            analysis = self.analyze_relevance(text)

            if analysis["relevance_score"] >= min_relevance:
                relevant_items.append((item, analysis))

        # Sort by relevance score
        relevant_items.sort(key=lambda x: x[1]["relevance_score"], reverse=True)

        return relevant_items


# Global filter instance
_global_filter: NLPRelevanceFilter | None = None
_global_filter_lock = threading.Lock()


def get_filter() -> NLPRelevanceFilter:
    """Get global filter instance (thread-safe)."""
    global _global_filter
    if _global_filter is None:
        with _global_filter_lock:
            if _global_filter is None:
                _global_filter = NLPRelevanceFilter()
    return _global_filter


if __name__ == "__main__":
    # Example usage
    filter_obj = NLPRelevanceFilter()

    test_texts = [
        "URGENT: Production is down! Critical security vulnerability found.",
        "Fix typo in README.md",
        "Add new feature for user authentication with OAuth2 support",
        "How do I configure the database connection?",
        "This is great! Thanks for the awesome work!",
        "Major breaking change: API v2 implementation required",
    ]

    print("NLP Relevance Analysis Examples:\n")
    print("=" * 70)

    for text in test_texts:
        analysis = filter_obj.analyze_relevance(text)
        print(f"\nText: {text[:60]}...")
        print(f"Relevance: {analysis['relevance_score']:.2f}")
        print(f"Urgency: {analysis['urgency']:.2f}")
        print(f"Importance: {analysis['importance']:.2f}")
        print(f"Action Required: {analysis['action_required']}")
        print(f"Sentiment: {analysis['sentiment']}")
        print(
            f"Key Entities: {', '.join(analysis['key_entities']) if analysis['key_entities'] else 'None'}"  # noqa: E501
        )
