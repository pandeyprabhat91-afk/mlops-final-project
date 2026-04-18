"""CLI entry point for DVC pipeline stages.

Usage: python ml/preprocessing_pipeline.py <stage>
Stages: extract_frames | detect_faces | compute_features
"""
import logging
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torchvision.transforms.functional as TF
from efficientnet_pytorch import EfficientNet
from facenet_pytorch import MTCNN
from PIL import Image
from torchvision import transforms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {DEVICE}")

RAW_DIR = Path("data/raw")
FRAMES_DIR = Path("data/frames")
FACES_DIR = Path("data/faces")
FEATURES_DIR = Path("data/features")


def extract_frames():
    """Extract 30 evenly-sampled frames from each MP4 in data/raw/."""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    for mp4 in RAW_DIR.glob("*.mp4"):
        cap = cv2.VideoCapture(str(mp4))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total == 0:
            logger.warning(f"Skipping empty video: {mp4}")
            continue
        indices = np.linspace(0, total - 1, 30, dtype=int)
        out_dir = FRAMES_DIR / mp4.stem
        out_dir.mkdir(exist_ok=True)
        for i, idx in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(str(out_dir / f"frame_{i:03d}.jpg"), frame)
        cap.release()
        logger.info(f"Extracted frames for {mp4.name}")


def detect_faces():
    """Run MTCNN face detection on extracted frames. Falls back to original frame if no face found."""
    mtcnn = MTCNN(image_size=224, margin=20, keep_all=False, device=DEVICE)
    FACES_DIR.mkdir(parents=True, exist_ok=True)
    detected, total = 0, 0
    for video_dir in FRAMES_DIR.iterdir():
        if not video_dir.is_dir():
            continue
        out_dir = FACES_DIR / video_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for jpg in sorted(video_dir.glob("*.jpg")):
            total += 1
            img = Image.open(jpg).convert("RGB")
            face = mtcnn(img)
            if face is not None:
                detected += 1
                TF.to_pil_image(((face + 1) / 2).clamp(0, 1)).save(out_dir / jpg.name)
            else:
                shutil.copy(jpg, out_dir / jpg.name)
    logger.info(f"Face detection: {detected}/{total} detected")


def compute_features():
    """Save face crops as image tensors [num_frames, 3, 224, 224] for model input.

    The DeepfakeDetector model contains EfficientNet internally and expects raw
    frames — not pre-extracted embeddings.
    """
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    for video_dir in FACES_DIR.iterdir():
        if not video_dir.is_dir():
            continue
        tensors = [
            transform(Image.open(j).convert("RGB"))
            for j in sorted(video_dir.glob("*.jpg"))
        ]
        if tensors:
            stacked = torch.stack(tensors)  # [num_frames, 3, 224, 224]
            torch.save(stacked, FEATURES_DIR / f"{video_dir.name}.pt")
    logger.info(f"Saved {len(list(FACES_DIR.iterdir()))} face-crop tensors to {FEATURES_DIR}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else ""
    if stage == "extract_frames":
        extract_frames()
    elif stage == "detect_faces":
        detect_faces()
    elif stage == "compute_features":
        compute_features()
    else:
        print(f"Unknown stage: {stage}. Use: extract_frames | detect_faces | compute_features")
        sys.exit(1)
