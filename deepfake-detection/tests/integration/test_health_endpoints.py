"""Integration tests for health, ready, and metrics endpoints."""
from unittest.mock import patch


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data


def test_ready_with_model_loaded(client):
    """ready endpoint returns 200 when model is loaded."""
    with patch("backend.app.model_loader.is_model_loaded", return_value=True):
        with patch(
            "backend.app.model_loader.get_model_version",
            return_value="deepfake/Production/1",
        ):
            resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"


def test_ready_without_model(client):
    """ready endpoint returns 503 when model is not loaded."""
    with patch("backend.app.model_loader.is_model_loaded", return_value=False):
        resp = client.get("/ready")
    assert resp.status_code == 503


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"deepfake" in resp.content or b"python" in resp.content
