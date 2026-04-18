"""Tests for the prediction history store."""
import pytest
import backend.app.history_store as hs


@pytest.fixture(autouse=True)
def tmp_history(tmp_path, monkeypatch):
    """Redirect HISTORY_PATH to a temp file for each test."""
    monkeypatch.setattr(hs, "HISTORY_PATH", str(tmp_path / "history.json"))
    yield


def test_save_prediction_returns_record():
    from backend.app.history_store import save_prediction
    record = save_prediction("alice", "clip.mp4", {
        "prediction": "fake", "confidence": 0.87,
        "inference_latency_ms": 123.4,
        "mlflow_run_id": "abc123", "frames_analyzed": 30,
    })
    assert record["id"].startswith("HR-")
    assert record["username"] == "alice"
    assert record["filename"] == "clip.mp4"
    assert record["prediction"] == "fake"
    assert abs(record["confidence"] - 0.87) < 0.001
    assert record["inference_latency_ms"] == pytest.approx(123.4)
    assert "timestamp" in record


def test_save_prediction_persists():
    from backend.app.history_store import save_prediction, get_history
    save_prediction("bob", "test.mp4", {
        "prediction": "real", "confidence": 0.12,
        "inference_latency_ms": 55.0,
        "mlflow_run_id": "run1", "frames_analyzed": 20,
    })
    records = get_history("bob")
    assert len(records) == 1
    assert records[0]["filename"] == "test.mp4"


def test_get_history_filters_by_username():
    from backend.app.history_store import save_prediction, get_history
    save_prediction("alice", "a.mp4", {"prediction": "fake", "confidence": 0.9,
        "inference_latency_ms": 100.0, "mlflow_run_id": "r1", "frames_analyzed": 30})
    save_prediction("bob", "b.mp4", {"prediction": "real", "confidence": 0.1,
        "inference_latency_ms": 90.0, "mlflow_run_id": "r2", "frames_analyzed": 30})
    assert len(get_history("alice")) == 1
    assert len(get_history("bob")) == 1
    assert get_history("alice")[0]["filename"] == "a.mp4"


def test_get_history_newest_first():
    from backend.app.history_store import save_prediction, get_history
    save_prediction("alice", "first.mp4", {"prediction": "fake", "confidence": 0.9,
        "inference_latency_ms": 100.0, "mlflow_run_id": "r1", "frames_analyzed": 30})
    save_prediction("alice", "second.mp4", {"prediction": "real", "confidence": 0.1,
        "inference_latency_ms": 80.0, "mlflow_run_id": "r2", "frames_analyzed": 30})
    records = get_history("alice")
    assert records[0]["filename"] == "second.mp4"


def test_get_history_max_50():
    from backend.app.history_store import save_prediction, get_history
    for i in range(60):
        save_prediction("alice", f"v{i}.mp4", {"prediction": "fake", "confidence": 0.9,
            "inference_latency_ms": 10.0, "mlflow_run_id": "r", "frames_analyzed": 30})
    assert len(get_history("alice")) == 50


def test_get_history_returns_empty_for_unknown_user():
    from backend.app.history_store import get_history
    assert get_history("nobody") == []
