# tests/unit/test_schemas.py
import pytest
from pydantic import ValidationError
from backend.app.schemas import (
    PredictResponse,
    HealthResponse,
    ReadyResponse,
    ReloadResponse,
    ErrorResponse,
)

def test_predict_response_fields():
    r = PredictResponse(
        prediction="fake",
        confidence=0.94,
        inference_latency_ms=143,
        gradcam_image="base64string",
        mlflow_run_id="abc123",
        frames_analyzed=30,
    )
    assert r.prediction in ("real", "fake")
    assert 0.0 <= r.confidence <= 1.0

def test_health_response():
    r = HealthResponse(status="ok", model_loaded=True)
    assert r.status == "ok"
    assert r.model_loaded is True

def test_ready_response():
    r = ReadyResponse(status="ready", model_version="1.0.0")
    assert r.status == "ready"
    assert r.model_version == "1.0.0"

def test_reload_response():
    r = ReloadResponse(status="reloaded", model_version="2.0.0")
    assert r.status == "reloaded"
    assert r.model_version == "2.0.0"

def test_error_response():
    r = ErrorResponse(error="NotFound", detail="Resource not found")
    assert r.error == "NotFound"
    assert r.detail == "Resource not found"

def test_predict_response_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        PredictResponse(
            prediction="fake",
            confidence=1.5,
            inference_latency_ms=100,
            gradcam_image="base64string",
            mlflow_run_id="abc123",
            frames_analyzed=30,
        )

def test_predict_response_rejects_invalid_prediction():
    with pytest.raises(ValidationError):
        PredictResponse(
            prediction="invalid",
            confidence=0.9,
            inference_latency_ms=100,
            gradcam_image="base64string",
            mlflow_run_id="abc123",
            frames_analyzed=30,
        )
