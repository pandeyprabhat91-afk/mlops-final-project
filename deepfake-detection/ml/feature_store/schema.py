"""Versioned feature schema definitions.

Each schema version documents the expected tensor shape and preprocessing
logic applied at that version. Feature engineering logic is kept separate
from model logic per MLOps guideline section B (Feature Store Concept).
"""
from dataclasses import dataclass
from typing import Dict, List

import torch


@dataclass
class FeatureSchema:
    """Describes the shape and provenance of a feature tensor version.

    Attributes:
        version: Schema version string, e.g. 'v1'
        num_frames: Expected number of frames per video
        channels: Expected number of colour channels
        height: Expected spatial height
        width: Expected spatial width
        preprocessing: Human-readable description of preprocessing applied
    """
    version: str
    num_frames: int
    channels: int
    height: int
    width: int
    preprocessing: str

    def validate(self, tensor: torch.Tensor) -> List[str]:
        """Validate a tensor against this schema. Returns list of error strings."""
        errors: List[str] = []
        if tensor.dim() != 4:
            errors.append(f"Expected 4D tensor, got {tensor.dim()}D")
            return errors
        F, C, H, W = tensor.shape
        if F != self.num_frames:
            errors.append(f"num_frames={F}, expected {self.num_frames}")
        if C != self.channels:
            errors.append(f"channels={C}, expected {self.channels}")
        if H != self.height:
            errors.append(f"height={H}, expected {self.height}")
        if W != self.width:
            errors.append(f"width={W}, expected {self.width}")
        return errors


# Version Registry — add new entries when preprocessing logic changes.
# Old entries MUST NOT be removed — they document historical feature versions.

FEATURE_VERSIONS: Dict[str, FeatureSchema] = {
    "v1": FeatureSchema(
        version="v1",
        num_frames=30,
        channels=3,
        height=224,
        width=224,
        preprocessing=(
            "MTCNN face detection (image_size=224, margin=20), "
            "torchvision Resize(224,224) + ToTensor(). "
            "Raw pixel tensors — EfficientNet normalisation applied inside model."
        ),
    ),
}

CURRENT_VERSION = "v1"
