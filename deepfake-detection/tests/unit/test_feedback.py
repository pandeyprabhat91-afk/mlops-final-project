# tests/unit/test_feedback.py
import pytest
from unittest.mock import patch, MagicMock


def test_feedback_endpoint_success(client):
    with patch("backend.app.routers.predict.log_feedback") as mock_log:
        resp = client.post("/feedback", json={
            "request_id": "abc-123",
            "predicted": "fake",
            "ground_truth": "real",
        })
    assert resp.status_code == 200
    assert resp.json()["status"] == "logged"
    mock_log.assert_called_once_with("abc-123", "fake", "real")


def test_feedback_endpoint_invalid_label(client):
    resp = client.post("/feedback", json={
        "request_id": "abc-123",
        "predicted": "unknown",
        "ground_truth": "real",
    })
    assert resp.status_code == 422
