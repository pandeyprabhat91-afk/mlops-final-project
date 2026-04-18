# tests/unit/test_drift_detector.py
import numpy as np
import pytest
from unittest.mock import patch
from backend.app.drift_detector import compute_drift_score, is_drifted

MOCK_BASELINE = {
    "mean": [0.5] * 10,
    "std": [0.1] * 10,
}

def test_no_drift_within_threshold():
    features = np.array([0.5] * 10)
    score = compute_drift_score(features, MOCK_BASELINE)
    assert score < 1.0  # within 1 std → low drift

def test_drift_detected_far_from_mean():
    features = np.array([5.0] * 10)  # 45 std devs from mean
    score = compute_drift_score(features, MOCK_BASELINE)
    assert score > 3.0

def test_is_drifted_threshold():
    assert is_drifted(4.0, threshold=3.0) is True
    assert is_drifted(1.0, threshold=3.0) is False
