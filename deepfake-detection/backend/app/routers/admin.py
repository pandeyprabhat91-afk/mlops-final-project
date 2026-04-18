"""Admin endpoints: rollback, model info, platform analytics."""
import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from backend.app.model_loader import (
    get_model_version,
    get_run_id,
    is_model_loaded,
    reload_to_version,
)
from backend.app.metrics import MODEL_RELOADS
from backend.app.schemas import ModelInfoResponse, ReloadResponse, RollbackRequest
from backend.app.history_store import HISTORY_PATH

admin_router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@admin_router.post("/rollback", response_model=ReloadResponse)
def rollback_model(body: RollbackRequest):
    """Roll back model to a specific MLflow registered version number."""
    try:
        version = reload_to_version(body.version)
        MODEL_RELOADS.labels(trigger="rollback").inc()
        logger.info("model_rollback_success", extra={"version": version})
        return ReloadResponse(status="rolled_back", model_version=version)
    except Exception as e:
        logger.error("model_rollback_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/model-info", response_model=ModelInfoResponse)
def model_info():
    """Return currently loaded model version, run ID, and load status."""
    return ModelInfoResponse(
        model_version=get_model_version(),
        run_id=get_run_id(),
        model_loaded=is_model_loaded(),
    )


@admin_router.get("/platform-stats")
def platform_stats():
    """Aggregate analytics across all users from history.json and feedback log."""
    # Load all history records
    try:
        records = json.loads(Path(HISTORY_PATH).read_text()) if Path(HISTORY_PATH).exists() else []
    except Exception:
        records = []

    total = len(records)
    fake_count = sum(1 for r in records if r.get("prediction") == "fake")
    real_count = total - fake_count
    detection_rate = (fake_count / total * 100) if total > 0 else 0.0

    latencies = [r["inference_latency_ms"] for r in records if r.get("inference_latency_ms", 0) > 0]
    avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0

    # Unique users (DAU / MAU)
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    month_ago = now - timedelta(days=30)

    def parse_ts(ts: str) -> datetime:
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    dau_users: set[str] = set()
    mau_users: set[str] = set()
    all_users: set[str] = set()
    for r in records:
        u = r.get("username", "anonymous")
        all_users.add(u)
        ts = parse_ts(r.get("timestamp", ""))
        if ts >= day_ago:
            dau_users.add(u)
        if ts >= month_ago:
            mau_users.add(u)

    # Feedback-based accuracy (precision / recall / F1)
    feedback_path = Path("data/feedback/feedback_log.jsonl")
    tp = fp = fn = tn = 0
    if feedback_path.exists():
        for line in feedback_path.read_text().splitlines():
            try:
                e = json.loads(line)
                pred, gt = e.get("predicted"), e.get("ground_truth")
                if pred == "fake" and gt == "fake":
                    tp += 1
                elif pred == "fake" and gt == "real":
                    fp += 1
                elif pred == "real" and gt == "fake":
                    fn += 1
                elif pred == "real" and gt == "real":
                    tn += 1
            except Exception:
                pass

    total_fb = tp + fp + fn + tn
    fb_precision = tp / (tp + fp) if (tp + fp) > 0 else None
    fb_recall    = tp / (tp + fn) if (tp + fn) > 0 else None
    fb_f1        = (2 * fb_precision * fb_recall / (fb_precision + fb_recall)) if fb_precision and fb_recall else None
    fb_fpr       = fp / (fp + tn) if (fp + tn) > 0 else None

    # MLflow training metrics for the currently loaded run
    mlflow_metrics: dict = {}
    run_id = get_run_id()
    if run_id and run_id != "unknown":
        mlflow_url = os.getenv("MLFLOW_SERVER_URL", "http://mlflow-server:5000")
        try:
            resp = httpx.get(f"{mlflow_url}/api/2.0/mlflow/runs/get?run_id={run_id}", timeout=3.0)
            if resp.status_code == 200:
                metrics_list = resp.json().get("run", {}).get("data", {}).get("metrics", [])
                mlflow_metrics = {m["key"]: m["value"] for m in metrics_list}
        except Exception:
            pass

    def pct(v: float | None) -> float | None:
        return round(v * 100, 1) if v is not None else None

    return {
        "total_scans": total,
        "fake_count": fake_count,
        "real_count": real_count,
        "detection_rate": round(detection_rate, 2),
        "avg_inference_ms": round(avg_latency_ms, 1),
        "total_users": len(all_users),
        "dau": len(dau_users),
        "mau": len(mau_users),
        # Feedback-based live metrics (null until users submit ground-truth labels)
        "feedback_samples": total_fb,
        "precision": pct(fb_precision),
        "recall":    pct(fb_recall),
        "f1_score":  pct(fb_f1),
        "fpr":       round(fb_fpr * 100, 2) if fb_fpr is not None else None,
        # MLflow training metrics from the currently loaded run
        "mlflow_val_f1":       pct(mlflow_metrics.get("val_f1")),
        "mlflow_val_accuracy": pct(mlflow_metrics.get("val_accuracy")),
        "mlflow_train_f1":     pct(mlflow_metrics.get("train_f1")),
        "mlflow_val_loss":     round(mlflow_metrics["val_loss"], 4) if "val_loss" in mlflow_metrics else None,
    }
