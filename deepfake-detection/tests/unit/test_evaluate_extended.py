# tests/unit/test_evaluate_extended.py
import numpy as np
import pytest


def test_find_best_threshold_returns_float():
    from ml.evaluate import find_best_threshold
    probs = np.array([0.1, 0.4, 0.6, 0.9])
    labels = np.array([0, 0, 1, 1])
    threshold, f1 = find_best_threshold(probs, labels)
    assert 0.0 < threshold < 1.0
    assert 0.0 <= f1 <= 1.0


def test_compute_extended_metrics_keys():
    from ml.evaluate import compute_extended_metrics
    probs = np.array([0.1, 0.4, 0.6, 0.9])
    labels = np.array([0, 0, 1, 1])
    metrics = compute_extended_metrics(probs, labels)
    for key in ["pr_auc", "precision_real", "recall_real", "precision_fake", "recall_fake", "best_threshold", "best_f1"]:
        assert key in metrics, f"Missing metric: {key}"
