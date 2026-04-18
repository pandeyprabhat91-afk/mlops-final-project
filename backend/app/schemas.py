"""Pydantic request/response models for all API endpoints."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class PredictResponse(BaseModel):
    """Response from POST /predict."""
    prediction: Literal["real", "fake"] = Field(..., description="'real' or 'fake'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    inference_latency_ms: float
    gradcam_image: str = Field(..., description="Base64-encoded Grad-CAM PNG")
    mlflow_run_id: str
    frames_analyzed: int


class HealthResponse(BaseModel):
    """Response from GET /health."""
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_loaded: bool


class ReadyResponse(BaseModel):
    """Response from GET /ready."""
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_version: str


class ReloadResponse(BaseModel):
    """Response from POST /admin/reload-model."""
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_version: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str


class FeedbackRequest(BaseModel):
    """Body for POST /feedback."""
    request_id: str
    predicted: Literal["real", "fake"]
    ground_truth: Literal["real", "fake"]


class FeedbackResponse(BaseModel):
    """Response from POST /feedback."""
    status: str
    request_id: str


class RollbackRequest(BaseModel):
    """Body for POST /admin/rollback."""
    version: str = Field(..., description="MLflow model version number to roll back to, e.g. '2'")


class ModelInfoResponse(BaseModel):
    """Response from GET /admin/model-info."""
    model_config = ConfigDict(protected_namespaces=())

    model_version: str
    run_id: str
    model_loaded: bool


class SingleBatchResult(BaseModel):
    """Result for one file in a batch prediction."""
    filename: str
    prediction: Literal["real", "fake"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    inference_latency_ms: float
    error: str = ""


class BatchPredictResponse(BaseModel):
    """Response from POST /predict/batch."""
    results: list[SingleBatchResult]
    total: int
    succeeded: int
    failed: int


class TicketCreate(BaseModel):
    """Body for POST /support/tickets."""
    subject: str = Field(..., min_length=1, description="Short summary of the issue")
    description: str = Field(..., min_length=1, description="Full description of the problem")


class TicketResponse(BaseModel):
    """A support ticket as returned by the API."""
    id: str
    username: str
    subject: str
    description: str
    status: Literal["open", "resolved"]
    resolution: str = ""
    created_at: str
    resolved_at: str = ""


class ResolveRequest(BaseModel):
    """Body for PATCH /support/tickets/{ticket_id}/resolve."""
    resolution: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    """Body for POST /support/chat."""
    message: str = Field(..., min_length=1)
    last_detail: str | None = None      # detail from previous bot turn (for yes/more flow)
    last_escalate: bool = False         # whether last entry had escalate=True


class ChatResponse(BaseModel):
    """Response from POST /support/chat."""
    reply: str
    follow_up: str | None = None          # question the bot asks back
    suggestions: list[str] | None = None  # quick-reply button labels
    detail: str | None = None             # extra detail served on demand


class HistoryRecord(BaseModel):
    """One entry in a user's prediction history."""
    id: str
    username: str
    filename: str
    prediction: Literal["real", "fake"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    inference_latency_ms: float
    timestamp: str
