"""Prediction, health, ready, metrics, and admin endpoints."""
import logging
import os
import tempfile
import time
import uuid

import numpy as np
import torch
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from backend.app import explainability, model_loader
from backend.app.feedback_logger import log_feedback
from backend.app.drift_detector import compute_drift_score, is_drifted, load_baseline
from backend.app.metrics import (
    ACTIVE_REQUESTS,
    CONFIDENCE_SCORE,
    DRIFT_DETECTED,
    DRIFT_SCORE,
    ERROR_COUNTER,
    FRAME_COUNT,
    FRAMES_EXTRACTED,
    IMAGES_PROCESSED,
    INFERENCE_DURATION_SUMMARY,
    INFERENCE_LATENCY,
    LAST_CONFIDENCE,
    MODEL_MEMORY_MB,
    MODEL_RELOADS,
    PREDICTION_COUNTER,
    PREPROCESSING_DURATION_SUMMARY,
    PREPROCESSING_LATENCY,
    REQUEST_COUNT,
    REQUEST_DURATION_SUMMARY,
    REQUEST_LATENCY,
    VIDEO_SIZE_BYTES,
)
from backend.app.preprocessing import preprocess_video
from typing import List, Literal

from backend.app.demo_store import has_used_demo, record_demo_use
from backend.app.history_store import (
    HISTORY_PATH,  # noqa: F401  imported so tests can monkeypatch it
    save_prediction,
    get_history,
)
from backend.app.schemas import (
    BatchPredictResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    HistoryRecord,
    PredictResponse,
    ReadyResponse,
    ReloadResponse,
    SingleBatchResult,
)
from fastapi import Header

router = APIRouter()
logger = logging.getLogger(__name__)


def _update_model_memory_gauge() -> None:
    """Estimate model parameter memory and update the gauge."""
    try:
        pt_model = model_loader.get_pytorch_model()
        if pt_model is not None:
            param_bytes = sum(p.numel() * p.element_size() for p in pt_model.parameters())
            MODEL_MEMORY_MB.set(param_bytes / (1024 * 1024))
    except Exception:
        pass


def _source_type(request: Request) -> str:
    """Derive caller category from User-Agent header."""
    ua = (request.headers.get("user-agent") or "").lower()
    if any(k in ua for k in ("mozilla", "chrome", "safari", "firefox")):
        return "web"
    if ua:
        return "api"
    return "unknown"


def _client_ip(request: Request) -> str:
    """Return client IP, preferring X-Forwarded-For when behind a proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/predict", response_model=PredictResponse)
async def predict(request: Request, file: UploadFile = File(...)):
    """Accept an MP4 video and return real/fake prediction with Grad-CAM."""
    request_id = str(uuid.uuid4())
    mode = "single"
    source_type = _source_type(request)
    client_ip = _client_ip(request)
    start = time.time()

    ACTIVE_REQUESTS.inc()
    try:
        if not (file.filename or "").lower().endswith(".mp4"):
            ERROR_COUNTER.labels(endpoint="/predict", error_type="validation").inc()
            IMAGES_PROCESSED.labels(mode=mode, status="error").inc()
            raise HTTPException(status_code=400, detail="Only MP4 files are accepted")

        raw = await file.read()
        VIDEO_SIZE_BYTES.observe(len(raw))

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(raw)
            tmp_path = tmp.name

        # ── Preprocessing ─────────────────────────────────────────────────────
        preproc_start = time.time()
        try:
            frames_tensor = preprocess_video(tmp_path)
        except Exception as exc:
            ERROR_COUNTER.labels(endpoint="/predict", error_type="preprocessing").inc()
            IMAGES_PROCESSED.labels(mode=mode, status="error").inc()
            raise HTTPException(status_code=422, detail=f"Preprocessing failed: {exc}")
        finally:
            os.unlink(tmp_path)

        preproc_ms = (time.time() - preproc_start) * 1000
        PREPROCESSING_LATENCY.labels(mode=mode).observe(preproc_ms)
        PREPROCESSING_DURATION_SUMMARY.labels(mode=mode).observe(preproc_ms / 1000)

        num_frames = frames_tensor.shape[0]
        FRAME_COUNT.observe(num_frames)
        FRAMES_EXTRACTED.labels(mode=mode).inc(num_frames)

        # ── Inference ─────────────────────────────────────────────────────────
        infer_start = time.time()
        try:
            model = model_loader.get_model()
            input_data = frames_tensor.unsqueeze(0).numpy()
            result = model.predict(input_data)
            confidence = float(result[0][0])
        except Exception as exc:
            ERROR_COUNTER.labels(endpoint="/predict", error_type="inference").inc()
            IMAGES_PROCESSED.labels(mode=mode, status="error").inc()
            raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")

        infer_ms = (time.time() - infer_start) * 1000
        INFERENCE_LATENCY.labels(mode=mode).observe(infer_ms)
        INFERENCE_DURATION_SUMMARY.labels(mode=mode).observe(infer_ms / 1000)

        prediction = "fake" if confidence >= 0.5 else "real"

        # ── Drift detection ───────────────────────────────────────────────────
        feature_vec = frames_tensor.mean(dim=0).numpy()  # (3, 224, 224) — matches baseline shape
        baseline = load_baseline()
        drift_score = 0.0
        if baseline:
            drift_score = compute_drift_score(feature_vec, baseline)
            DRIFT_SCORE.set(drift_score)
            if is_drifted(drift_score):
                DRIFT_DETECTED.inc()
                logger.warning(
                    "drift_detected",
                    extra={"score": drift_score, "request_id": request_id},
                )

        # ── Grad-CAM ──────────────────────────────────────────────────────────
        gradcam_b64 = ""
        pytorch_model = model_loader.get_pytorch_model()
        if pytorch_model is not None:
            gradcam_b64 = explainability.generate_gradcam(pytorch_model, frames_tensor) or ""

        # ── Record outcome metrics ─────────────────────────────────────────────
        total_s = time.time() - start
        CONFIDENCE_SCORE.labels(prediction=prediction, mode=mode).observe(confidence)
        LAST_CONFIDENCE.labels(label=prediction).set(confidence)
        PREDICTION_COUNTER.labels(label=prediction, mode=mode, source_type=source_type).inc()
        IMAGES_PROCESSED.labels(mode=mode, status="success").inc()
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="200", mode=mode).inc()
        REQUEST_LATENCY.labels(endpoint="/predict", mode=mode).observe(total_s)
        REQUEST_DURATION_SUMMARY.labels(endpoint="/predict", mode=mode).observe(total_s)

        logger.info(
            "prediction_complete",
            extra={
                "request_id": request_id,
                "prediction": prediction,
                "confidence": confidence,
                "infer_ms": infer_ms,
                "drift_score": drift_score,
                "source_type": source_type,
                "client_ip": client_ip,
                "frames": num_frames,
            },
        )

        # ── Save to history ────────────────────────────────────────────────
        x_username = request.headers.get("x-username", "anonymous")
        save_prediction(x_username, file.filename or "upload.mp4", {
            "prediction": prediction,
            "confidence": confidence,
            "inference_latency_ms": infer_ms,
        })

        return PredictResponse(
            prediction=prediction,
            confidence=confidence,
            inference_latency_ms=infer_ms,
            gradcam_image=gradcam_b64,
            mlflow_run_id=model_loader.get_run_id(),
            frames_analyzed=num_frames,
        )

    except HTTPException:
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="4xx", mode=mode).inc()
        raise
    except Exception as e:
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="500", mode=mode).inc()
        ERROR_COUNTER.labels(endpoint="/predict", error_type="unknown").inc()
        logger.error(
            "prediction_failed", extra={"error": str(e), "request_id": request_id}
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_REQUESTS.dec()


@router.get("/health", response_model=HealthResponse)
def health():
    """Liveness check."""
    return HealthResponse(status="ok", model_loaded=model_loader.is_model_loaded())


@router.get("/ready", response_model=ReadyResponse)
def ready():
    """Readiness check — fails if model not loaded."""
    if not model_loader.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    return ReadyResponse(status="ready", model_version=model_loader.get_model_version())


@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    _update_model_memory_gauge()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.post("/admin/reload-model", response_model=ReloadResponse)
def reload_model_endpoint():
    """Force reload model from MLflow registry (used during rollback)."""
    try:
        version = model_loader.reload_model()
        MODEL_RELOADS.labels(trigger="admin").inc()
        _update_model_memory_gauge()
        logger.info("model_reloaded", extra={"version": version})
        return ReloadResponse(status="reloaded", model_version=version)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(body: FeedbackRequest):
    """Record a ground-truth label for a prior prediction.

    Appends an entry to the feedback JSONL log so real-world performance
    decay can be computed as ground-truth labels become available.
    """
    try:
        log_feedback(body.request_id, body.predicted, body.ground_truth)
        logger.info("feedback_logged", extra={"request_id": body.request_id})
        return FeedbackResponse(status="logged", request_id=body.request_id)
    except Exception as e:
        ERROR_COUNTER.labels(endpoint="/feedback", error_type="logging").inc()
        logger.error("feedback_log_failed", extra={"error": str(e), "request_id": body.request_id})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch", response_model=BatchPredictResponse)
async def predict_batch(request: Request, files: List[UploadFile] = File(...)):
    """Accept up to 10 MP4 videos and return predictions for all of them."""
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per batch request")

    x_username = request.headers.get("x-username", "anonymous")
    results = []
    for file in files:
        filename = file.filename or "unknown"
        try:
            if not filename.lower().endswith(".mp4"):
                results.append(SingleBatchResult(
                    filename=filename, prediction="real", confidence=0.0,
                    inference_latency_ms=0.0, error="Only MP4 files are accepted",
                ))
                continue

            raw = await file.read()
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp.write(raw)
                tmp_path = tmp.name

            try:
                frames_tensor = preprocess_video(tmp_path)
            finally:
                os.unlink(tmp_path)

            infer_start = time.time()
            model = model_loader.get_model()
            result_arr = model.predict(frames_tensor.unsqueeze(0).numpy())
            confidence = float(result_arr[0][0])
            infer_ms = (time.time() - infer_start) * 1000
            prediction: Literal["real", "fake"] = "fake" if confidence >= 0.5 else "real"

            results.append(SingleBatchResult(
                filename=filename,
                prediction=prediction,
                confidence=confidence,
                inference_latency_ms=infer_ms,
            ))
            save_prediction(x_username, filename, {
                "prediction": prediction,
                "confidence": confidence,
                "inference_latency_ms": infer_ms,
            })
        except Exception as exc:
            results.append(SingleBatchResult(
                filename=filename, prediction="real", confidence=0.0,
                inference_latency_ms=0.0, error=str(exc),
            ))

    succeeded = sum(1 for r in results if not r.error)
    failed = len(results) - succeeded
    return BatchPredictResponse(
        results=results, total=len(results), succeeded=succeeded, failed=failed
    )


@router.post("/demo/start")
async def demo_start(request: Request):
    """Grant a one-time demo session per IP. Returns 403 if already used."""
    ip = _client_ip(request)
    if has_used_demo(ip):
        raise HTTPException(status_code=403, detail="Demo already used from this IP address")
    record_demo_use(ip)
    return {"status": "ok", "username": "demo"}


@router.get("/history", response_model=list[HistoryRecord])
def prediction_history(x_username: str = Header(default="anonymous")):
    """Return the calling user's prediction history, newest first (max 50)."""
    return get_history(x_username)
