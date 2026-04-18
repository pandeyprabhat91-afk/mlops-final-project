"""Pipeline status endpoints for the frontend Pipeline Dashboard."""
import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter

pipeline_router = APIRouter()
logger = logging.getLogger(__name__)

# MLflow HTTP server — SQL-backed, supports all UI tabs
MLFLOW_SERVER_URL = os.getenv("MLFLOW_SERVER_URL", "http://mlflow-server:5000")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "deepfake-detection")

AIRFLOW_URL = os.getenv("AIRFLOW_URL", "http://airflow-webserver:8080")
AIRFLOW_USER = os.getenv("AIRFLOW_USER", "airflow")
AIRFLOW_PASS = os.getenv("AIRFLOW_PASS", "airflow")


async def _get_experiment_id(client: httpx.AsyncClient) -> str | None:
    """Resolve experiment name → ID via the MLflow REST API."""
    try:
        resp = await client.get(
            f"{MLFLOW_SERVER_URL}/api/2.0/mlflow/experiments/get-by-name",
            params={"experiment_name": EXPERIMENT_NAME},
        )
        if resp.status_code == 200:
            return resp.json()["experiment"]["experiment_id"]
    except Exception:
        pass
    return None


@pipeline_router.get("/mlflow-runs")
async def get_mlflow_runs() -> list[dict[str, Any]]:
    """Return recent MLflow runs via the MLflow REST API (SQL-backed)."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            experiment_id = await _get_experiment_id(client)
            if experiment_id is None:
                logger.warning("mlflow_experiment_not_found", extra={"name": EXPERIMENT_NAME})
                return []

            resp = await client.post(
                f"{MLFLOW_SERVER_URL}/api/2.0/mlflow/runs/search",
                json={
                    "experiment_ids": [experiment_id],
                    "max_results": 20,
                    "order_by": ["start_time DESC"],
                },
            )
            resp.raise_for_status()

        result = []
        for run in resp.json().get("runs", []):
            info = run.get("info", {})
            data = run.get("data", {})

            metrics = {m["key"]: m["value"] for m in data.get("metrics", [])}
            tags = {t["key"]: t["value"] for t in data.get("tags", [])}
            params = {p["key"]: p["value"] for p in data.get("params", [])}

            result.append({
                "run_id": info.get("run_id", ""),
                "run_name": info.get("run_name", ""),
                "status": info.get("status", ""),
                "start_time": info.get("start_time", 0),
                "metrics": metrics,
                "params": params,
                "tags": tags,
            })
        return result

    except Exception as exc:
        logger.warning("mlflow_runs_fetch_failed", extra={"error": str(exc)})
        return []


@pipeline_router.get("/airflow-runs")
async def get_airflow_runs() -> list[dict[str, Any]]:
    """Return recent Airflow DAG runs (empty list if Airflow is not running)."""
    try:
        async with httpx.AsyncClient(
            timeout=5.0,
            auth=(AIRFLOW_USER, AIRFLOW_PASS),
        ) as client:
            resp = await client.get(
                f"{AIRFLOW_URL}/api/v1/dags/deepfake_pipeline/dagRuns",
                params={"limit": 10, "order_by": "-start_date"},
            )
            resp.raise_for_status()
            runs = resp.json().get("dag_runs", [])

        return [
            {
                "dag_id": r.get("dag_id", ""),
                "state": r.get("state", ""),
                "start_date": r.get("start_date", ""),
                "end_date": r.get("end_date"),
            }
            for r in runs
        ]

    except Exception as exc:
        logger.warning("airflow_runs_fetch_failed", extra={"error": str(exc)})
        return []


@pipeline_router.get("/throughput")
async def get_throughput() -> dict[str, float]:
    """Return videos-per-minute from the last successful Airflow pipeline run."""
    try:
        async with httpx.AsyncClient(
            timeout=5.0,
            auth=(AIRFLOW_USER, AIRFLOW_PASS),
        ) as client:
            resp = await client.get(
                f"{AIRFLOW_URL}/api/v1/dags/deepfake_pipeline/dagRuns",
                params={"limit": 1, "state": "success", "order_by": "-start_date"},
            )
            resp.raise_for_status()
            runs = resp.json().get("dag_runs", [])
            if not runs:
                return {"videos_per_minute": 0.0}

            run = runs[0]
            run_id = run["dag_run_id"]
            xcom_resp = await client.get(
                f"{AIRFLOW_URL}/api/v1/dags/deepfake_pipeline/dagRuns/{run_id}"
                "/taskInstances/ingest_videos/xcomEntries/video_count",
            )
            video_count = 0
            if xcom_resp.status_code == 200:
                video_count = xcom_resp.json().get("value", 0) or 0

            from datetime import datetime
            start = datetime.fromisoformat(run["start_date"].replace("Z", "+00:00"))
            end_str = run.get("end_date")
            if end_str:
                end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                duration_min = (end - start).total_seconds() / 60
                if duration_min > 0 and video_count > 0:
                    return {"videos_per_minute": video_count / duration_min}

        return {"videos_per_minute": 0.0}

    except Exception as exc:
        logger.warning("throughput_fetch_failed", extra={"error": str(exc)})
        return {"videos_per_minute": 0.0}
