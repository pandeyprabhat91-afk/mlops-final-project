"""Integration tests for POST /predict endpoint."""
import numpy as np
from unittest.mock import MagicMock, patch


def test_predict_rejects_non_mp4(client, sample_mp4_bytes):
    """POST /predict should reject non-MP4 files."""
    resp = client.post(
        "/predict",
        files={"file": ("test.avi", sample_mp4_bytes, "video/x-msvideo")},
    )
    assert resp.status_code == 400


def test_predict_returns_valid_schema(client, mock_frames_tensor, sample_mp4_bytes):
    """POST /predict should return a valid PredictResponse."""
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.85]])

    with patch(
        "backend.app.routers.predict.preprocess_video", return_value=mock_frames_tensor
    ):
        with patch("backend.app.model_loader.get_model", return_value=mock_model):
            with patch(
                "backend.app.routers.predict.explainability.generate_gradcam",
                return_value="base64img",
            ):
                resp = client.post(
                    "/predict",
                    files={"file": ("test.mp4", sample_mp4_bytes, "video/mp4")},
                )

    assert resp.status_code == 200
    data = resp.json()
    assert data["prediction"] in ("real", "fake")
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["frames_analyzed"] == 30
    assert "gradcam_image" in data


def test_predict_fake_confidence(client, mock_frames_tensor, sample_mp4_bytes):
    """Confidence >= 0.5 → prediction='fake'."""
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.9]])

    with patch(
        "backend.app.routers.predict.preprocess_video", return_value=mock_frames_tensor
    ):
        with patch("backend.app.model_loader.get_model", return_value=mock_model):
            resp = client.post(
                "/predict",
                files={"file": ("test.mp4", sample_mp4_bytes, "video/mp4")},
            )

    assert resp.status_code == 200
    assert resp.json()["prediction"] == "fake"


def test_predict_real_confidence(client, mock_frames_tensor, sample_mp4_bytes):
    """Confidence < 0.5 → prediction='real'."""
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.1]])

    with patch(
        "backend.app.routers.predict.preprocess_video", return_value=mock_frames_tensor
    ):
        with patch("backend.app.model_loader.get_model", return_value=mock_model):
            resp = client.post(
                "/predict",
                files={"file": ("test.mp4", sample_mp4_bytes, "video/mp4")},
            )

    assert resp.status_code == 200
    assert resp.json()["prediction"] == "real"
