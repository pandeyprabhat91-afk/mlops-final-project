"""Log ground-truth labels for model performance tracking over time."""
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
FEEDBACK_LOG = Path("data/feedback/feedback_log.jsonl")


def log_feedback(request_id: str, predicted: str, ground_truth: str) -> None:
    """Append a ground-truth label entry to the feedback log.

    Args:
        request_id: Unique identifier for the original prediction
        predicted: Model prediction ('real' or 'fake')
        ground_truth: Actual label provided by user/system
    """
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "predicted": predicted,
        "ground_truth": ground_truth,
        "correct": predicted == ground_truth,
    }
    with FEEDBACK_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    logger.info("feedback_logged", extra=entry)
