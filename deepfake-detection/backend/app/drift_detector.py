"""Feature drift detection: compare incoming features against stored baseline."""
import json
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

BASELINE_PATH = Path(os.getenv("DRIFT_BASELINE_PATH", "ml/feature_baseline.json"))
DEFAULT_DRIFT_THRESHOLD = 3.0  # z-score threshold


def load_baseline() -> Optional[dict]:
    """Load baseline statistics. Returns None if baseline not found."""
    if not BASELINE_PATH.exists():
        logger.warning("drift_baseline_not_found", extra={"path": str(BASELINE_PATH)})
        return None
    return json.loads(BASELINE_PATH.read_text())


def compute_drift_score(features: np.ndarray, baseline: dict) -> float:
    """Compute mean absolute z-score between features and baseline.

    Args:
        features: 1-D feature vector from current inference
        baseline: dict with 'mean' and 'std' keys (lists of floats)

    Returns:
        Mean absolute z-score across all dimensions
    """
    mean = np.array(baseline["mean"])
    std = np.array(baseline["std"])
    std = np.where(std == 0, 1e-8, std)  # avoid division by zero
    z_scores = np.abs((features - mean) / std)
    return float(z_scores.mean())


def is_drifted(drift_score: float, threshold: float = DEFAULT_DRIFT_THRESHOLD) -> bool:
    """Return True if drift score exceeds threshold."""
    return drift_score > threshold
