"""Load and reload model from checkpoint or MLflow Model Registry."""
import logging
import os

import mlflow.pyfunc
import mlflow.pytorch
import torch

logger = logging.getLogger(__name__)

_model = None
_pytorch_model = None
_current_version: str = "unknown"
_run_id: str = "unknown"


def _load_pytorch_from_checkpoint(checkpoint_path: str):
    """Load DeepfakeDetector directly from a .pt state-dict checkpoint."""
    from ml.model import DeepfakeDetector
    model = DeepfakeDetector(num_frames=30, lstm_hidden=256, lstm_layers=2, dropout=0.3)
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model


def load_model() -> None:
    """Load model into module-level singletons.

    Priority:
    1. MODEL_CHECKPOINT_PATH env var — load raw PyTorch state dict (bypasses MLflow registry)
    2. MLflow registry URI (models:/{name}/{stage})
    """
    global _model, _pytorch_model, _current_version, _run_id

    checkpoint_path = os.getenv("MODEL_CHECKPOINT_PATH")
    if checkpoint_path:
        logger.info("loading_model_from_checkpoint", extra={"path": checkpoint_path})
        pt_model = _load_pytorch_from_checkpoint(checkpoint_path)
        _pytorch_model = pt_model
        # Wrap in a thin callable so the rest of the code can call _model.predict()
        _model = _PyTorchWrapper(pt_model)
        _current_version = "checkpoint"
        _run_id = os.getenv("MLFLOW_RUN_ID", "unknown")
        logger.info("model_loaded_from_checkpoint")
        return

    model_name = os.getenv("MODEL_NAME", "deepfake")
    model_stage = os.getenv("MODEL_STAGE", "Production")
    model_uri = f"models:/{model_name}/{model_stage}"

    logger.info("loading_model", extra={"uri": model_uri})
    _model = mlflow.pyfunc.load_model(model_uri)
    _current_version = f"{model_name}/{model_stage}"

    try:
        _run_id = _model.metadata.run_id
    except Exception:
        _run_id = "unknown"

    try:
        _pytorch_model = mlflow.pytorch.load_model(model_uri)
    except Exception:
        _pytorch_model = None
        logger.warning("pytorch_model_load_failed", extra={"uri": model_uri})

    logger.info("model_loaded", extra={"version": _current_version})


class _PyTorchWrapper:
    """Minimal wrapper so checkpoint-loaded models look like mlflow.pyfunc models."""

    def __init__(self, model):
        self._model = model

    def predict(self, data):
        """Run inference. Returns ndarray of shape (batch, 1) matching mlflow pyfunc convention."""
        frames = data.get("frames") if isinstance(data, dict) else data
        if not isinstance(frames, torch.Tensor):
            frames = torch.tensor(frames, dtype=torch.float32)
        with torch.no_grad():
            preds = self._model(frames).numpy()  # shape (batch, 1)
        return preds


def get_model():
    """Return loaded model. Raises RuntimeError if not loaded."""
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")
    return _model


def get_pytorch_model():
    """Return loaded PyTorch model, or None if unavailable."""
    return _pytorch_model


def get_model_version() -> str:
    """Return current model version string."""
    return _current_version


def get_run_id() -> str:
    """Return MLflow run_id for the loaded model."""
    return _run_id


def is_model_loaded() -> bool:
    """Return True if model is loaded."""
    return _model is not None


def reload_model() -> str:
    """Force reload model from registry. Returns new version string."""
    load_model()
    return _current_version


def reload_to_version(version: str) -> str:
    """Load a specific registered model version by version number.

    Args:
        version: MLflow model version string, e.g. "2"

    Returns:
        Loaded version string, e.g. "deepfake/2"
    """
    global _model, _pytorch_model, _current_version, _run_id

    model_name = os.getenv("MODEL_NAME", "deepfake")
    model_uri = f"models:/{model_name}/{version}"

    logger.info("rolling_back_model", extra={"uri": model_uri})
    _model = mlflow.pyfunc.load_model(model_uri)
    _current_version = f"{model_name}/{version}"

    try:
        _run_id = _model.metadata.run_id
    except Exception:
        _run_id = "unknown"

    try:
        _pytorch_model = mlflow.pytorch.load_model(model_uri)
    except Exception:
        _pytorch_model = None

    logger.info("model_rolled_back", extra={"version": _current_version})
    return _current_version
