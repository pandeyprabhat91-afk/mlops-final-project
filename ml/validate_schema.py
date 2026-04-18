"""Data schema validation for the features DVC stage.

Validates that each .pt file in data/features/:
  - Is a 4-D tensor of shape (num_frames, 3, 224, 224)
  - Has num_frames between 1 and 120
  - Has filename encoding a label ('real' or 'fake' in stem)
"""
import sys
from pathlib import Path
from typing import List

import torch

sys.path.insert(0, str(Path(__file__).parent.parent))

EXPECTED_CHANNELS = 3
EXPECTED_HEIGHT = 224
EXPECTED_WIDTH = 224
MIN_FRAMES = 1
MAX_FRAMES = 120


def validate_feature_file(path: str) -> List[str]:
    """Validate a single .pt feature file. Returns list of error strings (empty = valid).

    Args:
        path: Path to a .pt tensor file

    Returns:
        List of human-readable error strings. Empty list means file is valid.
    """
    errors: List[str] = []
    p = Path(path)

    try:
        tensor = torch.load(path, weights_only=True)
    except Exception as e:
        return [f"Cannot load file {p.name}: {e}"]

    if tensor.dim() != 4:
        errors.append(f"{p.name}: expected 4D tensor, got {tensor.dim()}D")
        return errors  # can't check further

    num_frames, C, H, W = tensor.shape

    if not (MIN_FRAMES <= num_frames <= MAX_FRAMES):
        errors.append(f"{p.name}: num_frames={num_frames} outside [{MIN_FRAMES}, {MAX_FRAMES}]")
    if C != EXPECTED_CHANNELS:
        errors.append(f"{p.name}: channels={C}, expected {EXPECTED_CHANNELS}")
    if H != EXPECTED_HEIGHT or W != EXPECTED_WIDTH:
        errors.append(f"{p.name}: spatial dims=({H},{W}), expected ({EXPECTED_HEIGHT},{EXPECTED_WIDTH})")

    stem = p.stem.lower()
    if "real" not in stem and "fake" not in stem:
        errors.append(f"{p.name}: filename must contain 'real' or 'fake' to encode label")

    return errors


def validate_features_dir(features_dir: str = "data/features") -> int:
    """Validate all .pt files in features_dir. Prints errors and returns exit code.

    Returns:
        0 if all files valid, 1 if any errors found
    """
    features_path = Path(features_dir)
    pt_files = list(features_path.rglob("*.pt"))
    if not pt_files:
        print(f"No .pt files found in {features_dir}")
        return 1

    total_errors = 0
    for pt_file in pt_files:
        errors = validate_feature_file(str(pt_file))
        for err in errors:
            print(f"SCHEMA ERROR: {err}")
            total_errors += 1

    if total_errors > 0:
        print(f"\nValidation FAILED: {total_errors} error(s) in {len(pt_files)} files")
        return 1

    print(f"Validation PASSED: {len(pt_files)} files all valid")
    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--features_dir", default="data/features")
    args = parser.parse_args()
    sys.exit(validate_features_dir(args.features_dir))
