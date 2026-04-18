# tests/unit/test_preprocessing.py
import torch
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from backend.app.preprocessing import extract_frames, preprocess_video, detect_faces


def test_extract_frames_returns_list():
    """extract_frames should return a list of numpy arrays."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 30.0  # total frame count
    mock_cap.read.side_effect = [
        (True, np.zeros((480, 640, 3), dtype=np.uint8))
    ] * 30 + [(False, None)]

    with patch("backend.app.preprocessing.cv2.VideoCapture", return_value=mock_cap):
        frames = extract_frames("/fake/video.mp4", num_frames=10)

    assert isinstance(frames, list)
    assert len(frames) == 10


def test_preprocess_video_output_shape():
    """preprocess_video should return tensor (num_frames, 3, 224, 224)."""
    fake_frames = [np.zeros((224, 224, 3), dtype=np.uint8)] * 30
    with patch("backend.app.preprocessing.extract_frames", return_value=fake_frames):
        with patch("backend.app.preprocessing.detect_faces", return_value=fake_frames):
            result = preprocess_video("/fake/video.mp4", num_frames=30)
    assert isinstance(result, torch.Tensor)
    assert result.shape == (30, 3, 224, 224)


def test_extract_frames_raises_on_unopenable_video():
    """extract_frames should raise ValueError when video cannot be opened."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    with patch("backend.app.preprocessing.cv2.VideoCapture", return_value=mock_cap):
        with pytest.raises(ValueError, match="Cannot open video"):
            extract_frames("/fake/video.mp4")


def test_extract_frames_raises_on_zero_frames():
    """extract_frames should raise ValueError when video reports no frames."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 0.0
    with patch("backend.app.preprocessing.cv2.VideoCapture", return_value=mock_cap):
        with pytest.raises(ValueError, match="Video has no frames"):
            extract_frames("/fake/video.mp4")


def test_detect_faces_fallback_returns_correct_shape():
    """detect_faces should return list of (224, 224, 3) arrays when no face detected."""
    # Provide a 224x224 BGR frame; MTCNN will be mocked to return None (no face)
    frames = [np.zeros((224, 224, 3), dtype=np.uint8)]
    with patch("backend.app.preprocessing.get_mtcnn") as mock_get_mtcnn:
        mock_mtcnn = MagicMock()
        mock_mtcnn.return_value = None  # no face detected
        mock_get_mtcnn.return_value = mock_mtcnn
        result = detect_faces(frames)
    assert len(result) == 1
    assert result[0].shape == (224, 224, 3)
