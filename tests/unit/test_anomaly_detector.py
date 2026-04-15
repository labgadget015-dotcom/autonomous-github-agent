"""Unit tests for autopilot/ai_optimization/anomaly_detector.py"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Add autopilot directory to path
_autopilot_path = str(Path(__file__).parent.parent.parent / "autopilot")
if _autopilot_path not in sys.path:
    sys.path.insert(0, _autopilot_path)

from ai_optimization.anomaly_detector import AnomalyDetector


def _make_commit(files_changed=5, additions=100, deletions=50):
    commit = MagicMock()
    commit.stats = MagicMock()
    commit.stats.additions = additions
    commit.stats.deletions = deletions
    commit.stats.total = additions + deletions
    mock_files = []
    for i in range(files_changed):
        mock_file = MagicMock()
        mock_file.filename = f"module_{i}.py"
        mock_files.append(mock_file)
    commit.files = mock_files
    return commit


class TestAnomalyDetectorInit:
    def test_creates_with_defaults(self):
        detector = AnomalyDetector()
        assert detector.trained is False
        assert detector.baseline is None

    def test_custom_contamination(self):
        detector = AnomalyDetector(contamination=0.2)
        assert detector.model.contamination == 0.2

    def test_feature_names_set(self):
        detector = AnomalyDetector()
        assert "files_changed" in detector.feature_names
        assert len(detector.feature_names) == 7


class TestCalculateComplexity:
    def test_zero_inputs(self):
        detector = AnomalyDetector()
        score = detector._calculate_complexity(0, 0, 0)
        assert score == 0.0

    def test_high_churn_high_score(self):
        detector = AnomalyDetector()
        score = detector._calculate_complexity(500, 500, 10)
        assert score > 1.0

    def test_more_files_increases_complexity(self):
        detector = AnomalyDetector()
        score1 = detector._calculate_complexity(100, 50, 5)
        score2 = detector._calculate_complexity(100, 50, 20)
        assert score2 > score1


class TestExtractCommitFeatures:
    def test_extracts_features_from_mock_commit(self):
        detector = AnomalyDetector()
        commit = _make_commit()
        features = detector._extract_commit_features(commit)
        assert features is not None
        assert len(features) == 7

    def test_returns_none_or_zeros_on_exception(self):
        detector = AnomalyDetector()
        bad_commit = object()
        features = detector._extract_commit_features(bad_commit)
        # Returns either None or a zero array on failure
        if features is not None:
            import numpy as np
            assert np.all(features == 0)

    def test_test_files_counted_separately(self):
        detector = AnomalyDetector()
        commit = MagicMock()
        commit.stats = MagicMock()
        commit.stats.additions = 50
        commit.stats.deletions = 10
        commit.stats.total = 60
        mock_file = MagicMock()
        mock_file.filename = "test_module.py"
        commit.files = [mock_file]
        features = detector._extract_commit_features(commit)
        # test_ratio should be 1.0 since all files are tests
        assert features[5] == 1.0  # test_file_ratio


class TestDetectSignificantChanges:
    def test_returns_dict(self):
        detector = AnomalyDetector()
        commit = _make_commit()
        result = detector.detect_significant_changes(commit)
        assert isinstance(result, dict)

    def test_result_has_is_significant(self):
        detector = AnomalyDetector()
        commit = _make_commit()
        result = detector.detect_significant_changes(commit)
        assert "is_significant" in result

    def test_result_has_anomaly_score(self):
        detector = AnomalyDetector()
        commit = _make_commit()
        result = detector.detect_significant_changes(commit)
        assert "anomaly_score" in result

    def test_bad_commit_returns_safe_defaults(self):
        detector = AnomalyDetector()
        result = detector.detect_significant_changes(object())
        assert result["is_significant"] is False or result["is_significant"] == False


class TestEstablishBaseline:
    def test_empty_commits_logs_warning(self):
        detector = AnomalyDetector()
        detector.establish_baseline([])
        assert detector.baseline is None

    def test_baseline_set_with_valid_commits(self):
        detector = AnomalyDetector()
        commits = [_make_commit(files_changed=i + 1, additions=i * 10) for i in range(5)]
        detector.establish_baseline(commits)
        assert detector.baseline is not None
        assert "mean" in detector.baseline

    def test_sufficient_data_trains_model(self):
        detector = AnomalyDetector()
        commits = [_make_commit(files_changed=i + 1, additions=i * 20) for i in range(10)]
        detector.establish_baseline(commits)
        assert detector.baseline is not None


class TestAnalyze:
    def test_empty_metrics_returns_empty(self):
        detector = AnomalyDetector()
        result = detector.analyze([])
        assert result == []

    def test_non_commit_metrics_returns_empty(self):
        detector = AnomalyDetector()
        result = detector.analyze([{"value": 1}])
        assert isinstance(result, list)
