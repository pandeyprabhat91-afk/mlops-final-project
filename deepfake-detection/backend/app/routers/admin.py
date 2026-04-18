"""Admin endpoints: rollback, model info."""
import logging

from fastapi import APIRouter, HTTPException

from backend.app.model_loader import (
    get_model_version,
    get_run_id,
    is_model_loaded,
    reload_to_version,
)
from backend.app.metrics import MODEL_RELOADS
from backend.app.schemas import ModelInfoResponse, ReloadResponse, RollbackRequest

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
