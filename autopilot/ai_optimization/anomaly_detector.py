"""Anomaly Detection for Change Significance

This module detects unusual patterns and significant changes in commits,
helping to identify important updates and potential issues.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detect significant changes and anomalies in repository activity."""
    
    def __init__(self, contamination: float = 0.1):
        """Initialize anomaly detector.
        
        Args:
            contamination: Expected proportion of outliers (0-0.5)
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.baseline = None
        self.trained = False
        
        # Feature names for explanation
        self.feature_names = [
            'files_changed',
            'lines_added',
            'lines_deleted',
            'total_changes',
            'complexity_score',
            'test_file_ratio',
            'documentation_ratio'
        ]
    
    def establish_baseline(self, commits: List[Any]):
        """Establish baseline metrics from historical commits.
        
        Args:
            commits: List of commit objects
        """
        if not commits:
            logger.warning("No commits provided for baseline")
            return
        
        features_list = []
        for commit in commits:
            features = self._extract_commit_features(commit)
            if features is not None:
                features_list.append(features)
        
        if not features_list:
            logger.warning("No valid features extracted for baseline")
            return
        
        # Calculate baseline statistics
        features_array = np.array(features_list)
        self.baseline = {
            'mean': np.mean(features_array, axis=0),
            'std': np.std(features_array, axis=0),
            'median': np.median(features_array, axis=0),
            'min': np.min(features_array, axis=0),
            'max': np.max(features_array, axis=0),
            'count': len(features_list)
        }
        
        # Train the model
        if len(features_list) >= 10:
            try:
                scaled_features = self.scaler.fit_transform(features_array)
                self.model.fit(scaled_features)
                self.trained = True
                logger.info(f"Baseline established with {len(features_list)} commits")
            except Exception as e:
                logger.error(f"Failed to train model: {e}")
        else:
            logger.warning(f"Insufficient data for training: {len(features_list)} commits")
    
    def _extract_commit_features(self, commit: Any) -> Optional[np.ndarray]:
        """Extract features from a commit object.
        
        Args:
            commit: Commit object (PyGithub Commit)
            
        Returns:
            Feature array or None if extraction fails
        """
        try:
            # Get commit stats
            stats = getattr(commit, 'stats', {})
            if isinstance(stats, dict):
                additions = stats.get('additions', 0)
                deletions = stats.get('deletions', 0)
                total = stats.get('total', additions + deletions)
            else:
                additions = getattr(stats, 'additions', 0)
                deletions = getattr(stats, 'deletions', 0)
                total = getattr(stats, 'total', additions + deletions)
            
            # Get files changed
            files = getattr(commit, 'files', [])
            if hasattr(files, '__len__'):
                files_changed = len(list(files))
            else:
                files_changed = 0
            
            # Calculate complexity score (simplified)
            complexity = self._calculate_complexity(additions, deletions, files_changed)
            
            # Count test files
            test_count = 0
            doc_count = 0
            for file in (files if hasattr(files, '__iter__') else []):
                filename = getattr(file, 'filename', str(file)).lower()
                if 'test' in filename or 'spec' in filename:
                    test_count += 1
                if 'readme' in filename or 'doc' in filename or '.md' in filename:
                    doc_count += 1
            
            test_ratio = test_count / files_changed if files_changed > 0 else 0
            doc_ratio = doc_count / files_changed if files_changed > 0 else 0
            
            features = np.array([
                files_changed,
                additions,
                deletions,
                total,
                complexity,
                test_ratio,
                doc_ratio
            ])
            
            return features
            
        except Exception as e:
            logger.debug(f"Failed to extract features from commit: {e}")
            return None
    
    def _calculate_complexity(self, additions: int, deletions: int, 
                            files: int) -> float:
        """Calculate complexity score for a commit.
        
        Args:
            additions: Lines added
            deletions: Lines deleted
            files: Files changed
            
        Returns:
            Complexity score
        """
        # Simple complexity metric
        churn = additions + deletions
        file_factor = files * 10
        
        return (churn + file_factor) / 100.0
    
    def detect_significant_changes(self, commit: Any) -> Dict[str, Any]:
        """Detect if a commit represents a significant change.
        
        Args:
            commit: Commit object to analyze
            
        Returns:
            Dictionary with detection results
        """
        features = self._extract_commit_features(commit)
        
        if features is None:
            return {
                'is_significant': False,
                'anomaly_score': 0.0,
                'confidence': 0.0,
                'explanation': 'Unable to extract features'
            }
        
        # Use ML model if trained
        if self.trained and self.baseline is not None:
            try:
                scaled_features = self.scaler.transform(features.reshape(1, -1))
                anomaly_score = self.model.decision_function(scaled_features)[0]
                is_anomaly = self.model.predict(scaled_features)[0] == -1
                
                # Convert score to confidence (0-1)
                confidence = 1.0 / (1.0 + np.exp(anomaly_score))  # Sigmoid
                
            except Exception as e:
                logger.warning(f"ML detection failed: {e}")
                is_anomaly, anomaly_score, confidence = self._rule_based_detection(features)
        else:
            # Use rule-based detection
            is_anomaly, anomaly_score, confidence = self._rule_based_detection(features)
        
        # Generate explanation
        explanation = self._explain_anomaly(features, self.baseline)
        
        # Determine change type
        change_type = self._classify_change(features)
        
        return {
            'is_significant': is_anomaly,
            'anomaly_score': float(abs(anomaly_score)),
            'confidence': float(confidence),
            'explanation': explanation,
            'change_type': change_type,
            'features': {
                name: float(value) 
                for name, value in zip(self.feature_names, features)
            }
        }
    
    def _rule_based_detection(self, features: np.ndarray) -> Tuple[bool, float, float]:
        """Rule-based anomaly detection as fallback.
        
        Args:
            features: Feature array
            
        Returns:
            Tuple of (is_anomaly, score, confidence)
        """
        if self.baseline is None:
            # No baseline, use absolute thresholds
            files_changed, additions, deletions, total, complexity, test_ratio, doc_ratio = features
            
            is_anomaly = (
                files_changed > 50 or
                total > 1000 or
                complexity > 5.0
            )
            
            score = max(files_changed / 50, total / 1000, complexity / 5.0)
            confidence = 0.6
            
        else:
            # Compare to baseline
            deviations = []
            for i, (value, mean, std) in enumerate(zip(
                features, 
                self.baseline['mean'], 
                self.baseline['std']
            )):
                if std > 0:
                    z_score = abs((value - mean) / std)
                    deviations.append(z_score)
                else:
                    deviations.append(0)
            
            max_deviation = max(deviations)
            is_anomaly = max_deviation > 3.0  # 3 standard deviations
            score = max_deviation
            confidence = min(0.9, max_deviation / 5.0)
        
        return is_anomaly, score, confidence
    
    def _explain_anomaly(self, features: np.ndarray, 
                        baseline: Optional[Dict]) -> str:
        """Generate human-readable explanation of anomaly.
        
        Args:
            features: Feature array
            baseline: Baseline statistics
            
        Returns:
            Explanation string
        """
        explanations = []
        
        files_changed, additions, deletions, total, complexity, test_ratio, doc_ratio = features
        
        # Check each feature
        if files_changed > 20:
            explanations.append(f"Large number of files changed ({int(files_changed)})")
        
        if additions > 500:
            explanations.append(f"Extensive additions ({int(additions)} lines)")
        
        if deletions > 500:
            explanations.append(f"Extensive deletions ({int(deletions)} lines)")
        
        if complexity > 3.0:
            explanations.append(f"High complexity score ({complexity:.1f})")
        
        if test_ratio > 0.5:
            explanations.append(f"Primarily test changes ({test_ratio*100:.0f}% test files)")
        
        if doc_ratio > 0.5:
            explanations.append(f"Primarily documentation ({doc_ratio*100:.0f}% doc files)")
        
        # Compare to baseline if available
        if baseline is not None:
            if files_changed > baseline['mean'][0] * 3:
                explanations.append("Files changed 3x above average")
            
            if total > baseline['mean'][3] * 3:
                explanations.append("Total changes 3x above average")
        
        if not explanations:
            return "Standard commit within normal parameters"
        
        return "; ".join(explanations)
    
    def _classify_change(self, features: np.ndarray) -> str:
        """Classify the type of change.
        
        Args:
            features: Feature array
            
        Returns:
            Change type string
        """
        files_changed, additions, deletions, total, complexity, test_ratio, doc_ratio = features
        
        # Determine primary change type
        if doc_ratio > 0.7:
            return 'documentation'
        elif test_ratio > 0.7:
            return 'testing'
        elif deletions > additions * 2:
            return 'refactoring'
        elif additions > deletions * 2 and files_changed > 10:
            return 'feature_addition'
        elif files_changed > 50:
            return 'mass_update'
        elif complexity > 5.0:
            return 'complex_change'
        else:
            return 'standard_update'
    
    def analyze_commit_batch(self, commits: List[Any]) -> Dict[str, Any]:
        """Analyze a batch of commits for patterns.
        
        Args:
            commits: List of commit objects
            
        Returns:
            Analysis summary
        """
        results = []
        for commit in commits:
            result = self.detect_significant_changes(commit)
            if result['is_significant']:
                results.append({
                    'sha': getattr(commit, 'sha', 'unknown')[:7],
                    'message': getattr(commit, 'commit', commit).message.split('\n')[0][:60],
                    **result
                })
        
        # Summary statistics
        total_commits = len(commits)
        significant_count = len(results)
        
        change_types = {}
        for r in results:
            change_type = r['change_type']
            change_types[change_type] = change_types.get(change_type, 0) + 1
        
        return {
            'total_commits': total_commits,
            'significant_commits': significant_count,
            'significance_rate': significant_count / total_commits if total_commits > 0 else 0,
            'significant_changes': results,
            'change_type_distribution': change_types
        }


# Global detector instance
_global_detector = None

def get_detector() -> AnomalyDetector:
    """Get global detector instance."""
    global _global_detector
    if _global_detector is None:
        _global_detector = AnomalyDetector()
    return _global_detector


if __name__ == "__main__":
    # Example usage
    print("Anomaly Detector - Example Usage\n")
    print("="*70)
    
    # Mock commit class
    class MockCommit:
        def __init__(self, files, additions, deletions):
            self.stats = {
                'additions': additions,
                'deletions': deletions,
                'total': additions + deletions
            }
            self.files = [type('File', (), {'filename': f}) for f in files]
            self.sha = 'abc123'
            self.commit = type('CommitData', (), {
                'message': f'Example commit with {len(files)} files'
            })
    
    detector = AnomalyDetector()
    
    # Create baseline data (normal commits)
    baseline_commits = [
        MockCommit(['src/main.py', 'src/utils.py'], 25, 10),
        MockCommit(['src/api.py'], 15, 5),
        MockCommit(['tests/test_api.py'], 30, 8),
        MockCommit(['README.md'], 5, 2),
        MockCommit(['src/models.py', 'src/views.py'], 40, 15),
    ]
    
    detector.establish_baseline(baseline_commits)
    
    # Test commits (including anomalies)
    test_commits = [
        ('Normal', MockCommit(['src/helper.py'], 20, 8)),
        ('Large refactor', MockCommit([f'src/file{i}.py' for i in range(30)], 500, 300)),
        ('Massive feature', MockCommit([f'feature/file{i}.py' for i in range(50)], 2000, 100)),
        ('Doc update', MockCommit(['README.md', 'CONTRIBUTING.md'], 50, 10)),
    ]
    
    print("\nAnalyzing test commits:\n")
    for name, commit in test_commits:
        result = detector.detect_significant_changes(commit)
        
        print(f"{name}:")
        print(f"  Significant: {result['is_significant']}")
        print(f"  Score: {result['anomaly_score']:.3f}")
        print(f"  Change Type: {result['change_type']}")
        print(f"  Explanation: {result['explanation']}")
        print()
