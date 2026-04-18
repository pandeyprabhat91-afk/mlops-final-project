"""Video preprocessing: MP4 → sampled frames → MTCNN face crops → tensors."""
import logging
from typing import List, Optional

import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN
from PIL import Image
from torchvision import transforms

logger = logging.getLogger(__name__)

FRAME_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    # No ImageNet normalization — training pipeline (preprocessing_pipeline.py compute_features)
    # uses only ToTensor(), so inference must match to avoid train-serve distribution skew.
])

_mtcnn: Optional[MTCNN] = None


def get_mtcnn() -> MTCNN:
    """Lazy-load MTCNN face detector (singleton)."""
    global _mtcnn
    if _mtcnn is None:
        _mtcnn = MTCNN(
            image_size=224,
            margin=20,
            keep_all=False,
            device="cpu",
        )
    return _mtcnn


def extract_frames(video_path: str, num_frames: int = 30) -> List[np.ndarray]:
    """Sample num_frames evenly from an MP4 video.

    Args:
        video_path: Path to .mp4 file
        num_frames: Number of frames to sample

    Returns:
        List of BGR numpy arrays (H, W, 3)

    Raises:
        ValueError: If video cannot be opened or has no frames
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        raise ValueError(f"Video has no frames: {video_path}")

    indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    cap.release()

    if not frames:
        raise ValueError(f"Could not extract frames from {video_path}")

    logger.info("extracted_frames", extra={"count": len(frames), "path": video_path})
    return frames


def detect_faces(frames: List[np.ndarray]) -> List[np.ndarray]:
    """Run MTCNN face detection on each frame.

    Falls back to resized original frame if no face detected.

    Args:
        frames: List of BGR numpy arrays

    Returns:
        List of RGB numpy arrays (224, 224, 3)
    """
    mtcnn = get_mtcnn()
    face_crops = []
    detected = 0

    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        face_tensor = mtcnn(pil_img)

        if face_tensor is not None:
            # Convert MTCNN output (C,H,W) range [-1,1] → numpy (H,W,C) range [0,255]
            face_np = face_tensor.permute(1, 2, 0).numpy()
            face_np = ((face_np + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
            face_crops.append(face_np)
            detected += 1
        else:
            # Fallback: resize full frame
            fallback = cv2.resize(rgb, (224, 224))
            face_crops.append(fallback)

    logger.info("face_detection", extra={
        "detected": detected,
        "total": len(frames),
        "detection_rate": detected / len(frames) if frames else 0,
    })
    return face_crops


def preprocess_video(video_path: str, num_frames: int = 30) -> torch.Tensor:
    """Full preprocessing pipeline: MP4 → tensor ready for model.

    Args:
        video_path: Path to .mp4 file
        num_frames: Number of frames to use

    Returns:
        Tensor of shape (num_frames, 3, 224, 224)
    """
    frames = extract_frames(video_path, num_frames)
    face_crops = detect_faces(frames)

    tensors = []
    for crop in face_crops:
        pil = Image.fromarray(crop.astype(np.uint8))
        tensors.append(FRAME_TRANSFORM(pil))

    # Pad if fewer frames were extracted than requested
    if len(tensors) < num_frames:
        logger.warning(
            "padding_frames",
            extra={"extracted": len(tensors), "requested": num_frames, "path": video_path}
        )
    while len(tensors) < num_frames:
        tensors.append(tensors[-1].clone())

    return torch.stack(tensors[:num_frames])
