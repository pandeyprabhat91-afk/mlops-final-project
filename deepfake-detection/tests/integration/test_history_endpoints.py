# tests/integration/test_history_endpoints.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def history_client(tmp_path, monkeypatch):
    import backend.app.history_store as hs
    history_path = str(tmp_path / "history.json")
    monkeypatch.setattr(hs, "HISTORY_PATH", history_path)
    # Also patch the functions imported into predict.py so the router uses the
    # same module object (test_history_store.py can reload history_store, which
    # would leave predict.py holding a stale reference to the old module).
    import backend.app.routers.predict as predict_mod
    monkeypatch.setattr(predict_mod, "get_history", hs.get_history)
    monkeypatch.setattr(predict_mod, "save_prediction", hs.save_prediction)
    monkeypatch.setattr(predict_mod, "HISTORY_PATH", history_path)
    from backend.app.main import app
    return TestClient(app)


def test_get_history_empty(history_client):
    response = history_client.get("/history", headers={"X-Username": "alice"})
    assert response.status_code == 200
    assert response.json() == []


def test_get_history_returns_user_records(history_client):
    import backend.app.history_store as hs
    hs.save_prediction("alice", "clip.mp4", {
        "prediction": "fake", "confidence": 0.87,
        "inference_latency_ms": 100.0,
    })
    response = history_client.get("/history", headers={"X-Username": "alice"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["filename"] == "clip.mp4"
    assert data[0]["prediction"] == "fake"


def test_get_history_missing_header(history_client):
    # No X-Username header — defaults to "anonymous", returns empty list
    response = history_client.get("/history")
    assert response.status_code == 200
    assert response.json() == []
