"""Compute and save feature baseline statistics for drift detection."""
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import torch

BASELINE_PATH = Path("ml/feature_baseline.json")


def compute_baseline(features_dir: str) -> dict:
    """Compute mean, std, min, max for each feature dimension.

    Args:
        features_dir: Path to directory of saved feature .pt files

    Returns:
        dict with keys: mean, std, min, max (each a list of floats), n_samples
    """
    all_features = []
    for f in Path(features_dir).rglob("*.pt"):
        tensor = torch.load(f, weights_only=True)
        all_features.append(tensor.mean(dim=0).numpy())

    if not all_features:
        raise ValueError(f"No .pt files found in {features_dir}")

    stacked = np.stack(all_features)
    baseline = {
        "mean": stacked.mean(axis=0).tolist(),
        "std": stacked.std(axis=0).tolist(),
        "min": stacked.min(axis=0).tolist(),
        "max": stacked.max(axis=0).tolist(),
        "n_samples": len(all_features),
    }
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2))
    print(f"Baseline saved to {BASELINE_PATH} ({len(all_features)} samples)")
    return baseline


def load_baseline() -> Optional[dict]:
    """Load saved baseline stats. Returns None if baseline file not found."""
    if not BASELINE_PATH.exists():
        return None
    return json.loads(BASELINE_PATH.read_text())


if __name__ == "__main__":
    compute_baseline(sys.argv[1] if len(sys.argv) > 1 else "data/features")
