"""ML-Based Priority Scoring System

This module implements a machine learning model to predict issue/PR importance
and priority based on various features like age, activity, labels, and more.
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class MLPriorityScorer:
    """Machine learning model to predict issue/PR importance and priority."""

    def __init__(self):
        """Initialize the ML priority scorer."""
        self.classifier = RandomForestClassifier(
            n_estimators=100, max_depth=15, random_state=42, min_samples_split=5
        )
        self.regressor = GradientBoostingRegressor(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.scaler = StandardScaler()
        self.trained = False
        self.feature_names = [
            "issue_age_days",
            "comment_count",
            "reaction_count",
            "author_contributions",
            "label_severity_score",
            "linked_prs_count",
            "mention_count",
            "activity_trend",
            "is_stale",
            "has_milestone",
            "assignee_count",
        ]

        # Priority keywords and their weights
        self.priority_keywords = {
            "critical": 5.0,
            "urgent": 4.5,
            "high": 4.0,
            "bug": 3.5,
            "security": 5.0,
            "breaking": 4.5,
            "regression": 4.0,
            "medium": 2.5,
            "low": 1.5,
            "enhancement": 2.0,
            "feature": 2.5,
            "documentation": 1.5,
            "good first issue": 1.0,
            "help wanted": 2.0,
        }

    def extract_features(self, item: Any) -> np.ndarray:
        """Extract features from an issue or PR object.

        Args:
            item: GitHub issue or PR object

        Returns:
            Feature vector as numpy array
        """
        try:
            # Calculate issue age
            created_at = item.created_at
            age_days = (datetime.now() - created_at.replace(tzinfo=None)).days

            # Count reactions
            reactions = getattr(item, "reactions", {})
            if isinstance(reactions, dict):
                reaction_count = sum(reactions.values())
            else:
                # For PyGithub ReactionsSummary object
                reaction_count = getattr(reactions, "total_count", 0)

            # Count comments
            comment_count = getattr(item, "comments", 0)

            # Label severity score
            labels = getattr(item, "labels", [])
            label_severity = self._calculate_label_severity(labels)

            # Activity trend (comments in last 7 days vs total)
            activity_trend = self._calculate_activity_trend(item)

            # Check if stale (no updates in 30 days)
            updated_at = getattr(item, "updated_at", created_at)
            days_since_update = (datetime.now() - updated_at.replace(tzinfo=None)).days
            is_stale = 1 if days_since_update > 30 else 0

            # Milestone
            has_milestone = 1 if getattr(item, "milestone", None) else 0

            # Assignees
            assignees = getattr(item, "assignees", [])
            assignee_count = len(list(assignees)) if assignees else 0

            # Linked PRs (for issues)
            linked_prs = 0
            if hasattr(item, "pull_request") and item.pull_request is None:
                # This is an issue, count linked PRs in body
                body = getattr(item, "body", "") or ""
                linked_prs = body.count("#") + body.count("pull/")

            # Mentions
            body = getattr(item, "body", "") or ""
            mention_count = body.count("@")

            # Author contributions (placeholder - would need API call)
            author_contributions = 10  # Default value

            features = np.array(
                [
                    age_days,
                    comment_count,
                    reaction_count,
                    author_contributions,
                    label_severity,
                    linked_prs,
                    mention_count,
                    activity_trend,
                    is_stale,
                    has_milestone,
                    assignee_count,
                ]
            )

            return features.reshape(1, -1)

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            # Return default features on error
            return np.zeros((1, len(self.feature_names)))

    def _calculate_label_severity(self, labels: List) -> float:
        """Calculate severity score based on labels.

        Args:
            labels: List of label objects

        Returns:
            Severity score (0-5)
        """
        severity_score = 0.0

        for label in labels:
            label_name = (
                label.name.lower() if hasattr(label, "name") else str(label).lower()
            )

            # Check for priority keywords
            for keyword, weight in self.priority_keywords.items():
                if keyword in label_name:
                    severity_score = max(severity_score, weight)

        return severity_score

    def _calculate_activity_trend(self, item: Any) -> float:
        """Calculate activity trend score.

        Args:
            item: GitHub issue or PR object

        Returns:
            Activity trend score (0-1)
        """
        try:
            comment_count = getattr(item, "comments", 0)
            if comment_count == 0:
                return 0.0

            # In a real implementation, would analyze comment timestamps
            # For now, use a simple heuristic based on update recency
            updated_at = getattr(item, "updated_at", item.created_at)
            days_since_update = (datetime.now() - updated_at.replace(tzinfo=None)).days

            # More recent updates = higher trend
            trend = max(0.0, 1.0 - (days_since_update / 30.0))
            return trend

        except Exception:
            return 0.0

    def score(self, item: Any) -> Dict[str, Any]:
        """Score an issue or PR for priority.

        Args:
            item: GitHub issue or PR object

        Returns:
            Dictionary with score, confidence, and explanation
        """
        features = self.extract_features(item)

        # Calculate base score using rule-based system
        base_score = self._calculate_base_score(features[0])

        # If trained, use ML model
        if self.trained:
            try:
                scaled_features = self.scaler.transform(features)
                ml_score = self.regressor.predict(scaled_features)[0]
                confidence = self.classifier.predict_proba(scaled_features)[0].max()

                # Blend rule-based and ML scores
                final_score = 0.6 * ml_score + 0.4 * base_score
            except Exception as e:
                logger.warning(f"ML scoring failed, using base score: {e}")
                final_score = base_score
                confidence = 0.5
        else:
            final_score = base_score
            confidence = 0.7  # Moderate confidence for rule-based

        # Generate explanation
        explanation = self._explain_score(features[0], final_score)

        return {
            "score": round(final_score, 2),
            "confidence": round(confidence, 2),
            "factors": explanation,
            "priority_level": self._score_to_priority(final_score),
        }

    def _calculate_base_score(self, features: np.ndarray) -> float:
        """Calculate base score using rule-based system.

        Args:
            features: Feature vector

        Returns:
            Base score (0-100)
        """
        (
            age_days,
            comment_count,
            reaction_count,
            author_contrib,
            label_severity,
            linked_prs,
            mentions,
            activity_trend,
            is_stale,
            has_milestone,
            assignee_count,
        ) = features

        score = 0.0

        # Age factor (older = more important, up to a point)
        score += min(age_days * 0.5, 20)

        # Activity factors
        score += comment_count * 2
        score += reaction_count * 1.5
        score += mentions * 1.0

        # Label severity (most important factor)
        score += label_severity * 10

        # Activity trend
        score += activity_trend * 10

        # Milestone bonus
        score += has_milestone * 5

        # Assigned bonus
        score += assignee_count * 3

        # Linked PRs (for issues)
        score += linked_prs * 2

        # Stale penalty
        score -= is_stale * 15

        # Normalize to 0-100
        score = max(0, min(100, score))

        return score

    def _explain_score(self, features: np.ndarray, score: float) -> Dict[str, Any]:
        """Generate explanation for the score.

        Args:
            features: Feature vector
            score: Calculated score

        Returns:
            Dictionary with explanation factors
        """
        (
            age_days,
            comment_count,
            reaction_count,
            author_contrib,
            label_severity,
            linked_prs,
            mentions,
            activity_trend,
            is_stale,
            has_milestone,
            assignee_count,
        ) = features

        factors = {
            "age_days": int(age_days),
            "comment_count": int(comment_count),
            "reaction_count": int(reaction_count),
            "label_severity": round(label_severity, 1),
            "activity_trend": round(activity_trend, 2),
            "is_stale": bool(is_stale),
            "has_milestone": bool(has_milestone),
            "assignee_count": int(assignee_count),
        }

        # Identify key factors
        key_factors = []
        if label_severity >= 4.0:
            key_factors.append("high_severity_labels")
        if activity_trend > 0.7:
            key_factors.append("recent_activity")
        if comment_count > 10:
            key_factors.append("high_engagement")
        if is_stale:
            key_factors.append("stale_issue")
        if has_milestone:
            key_factors.append("has_milestone")

        factors["key_factors"] = key_factors

        return factors

    def _score_to_priority(self, score: float) -> str:
        """Convert numeric score to priority level.

        Args:
            score: Numeric score (0-100)

        Returns:
            Priority level string
        """
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "minimal"

    def train(self, training_data: List[Tuple[Any, float, int]]):
        """Train the ML model with historical data.

        Args:
            training_data: List of (item, score, priority_class) tuples
        """
        if len(training_data) < 50:
            logger.warning(f"Insufficient training data: {len(training_data)} samples")
            return

        try:
            # Extract features and labels
            X = []
            y_reg = []
            y_clf = []

            for item, score, priority_class in training_data:
                features = self.extract_features(item)
                X.append(features[0])
                y_reg.append(score)
                y_clf.append(priority_class)

            X = np.array(X)
            y_reg = np.array(y_reg)
            y_clf = np.array(y_clf)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train models
            self.regressor.fit(X_scaled, y_reg)
            self.classifier.fit(X_scaled, y_clf)

            self.trained = True
            logger.info(f"ML priority scorer trained on {len(training_data)} samples")

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise


# Global scorer instance
_global_scorer = None


def get_scorer() -> MLPriorityScorer:
    """Get global scorer instance."""
    global _global_scorer
    if _global_scorer is None:
        _global_scorer = MLPriorityScorer()
    return _global_scorer


if __name__ == "__main__":
    # Example usage
    print("ML Priority Scorer - Example Usage")

    # Mock issue object
    class MockIssue:
        def __init__(self):
            self.created_at = datetime.now() - timedelta(days=15)
            self.updated_at = datetime.now() - timedelta(days=2)
            self.comments = 8
            self.reactions = {"total_count": 12}
            self.labels = [
                type("Label", (), {"name": "bug"}),
                type("Label", (), {"name": "high priority"}),
            ]
            self.milestone = None
            self.assignees = []
            self.body = "This is a critical issue @user1 @user2 #123"
            self.pull_request = None

    scorer = get_scorer()
    issue = MockIssue()

    result = scorer.score(issue)
    print(f"\nPriority Score: {result['score']}")
    print(f"Priority Level: {result['priority_level']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Key Factors: {result['factors']['key_factors']}")
    print("\nDetailed Factors:")
    for factor, value in result["factors"].items():
        if factor != "key_factors":
            print(f"  {factor}: {value}")
