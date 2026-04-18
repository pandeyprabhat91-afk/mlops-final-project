"""JSON-backed prediction history store. Records stored in data/history.json."""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

HISTORY_PATH = str(Path(__file__).parent.parent.parent / "data" / "history.json")


def _load() -> list[dict]:
    path = Path(HISTORY_PATH)
    if not path.exists():
        return []
    try:
        with path.open() as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(records: list[dict]) -> None:
    path = Path(HISTORY_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(records, f, indent=2)


def save_prediction(username: str, filename: str, result_dict: dict) -> dict:
    """Append a prediction record for a user. Returns the saved record."""
    record = {
        "id": f"HR-{uuid.uuid4().hex[:8].upper()}",
        "username": username,
        "filename": filename,
        "prediction": result_dict.get("prediction", "real"),
        "confidence": result_dict.get("confidence", 0.0),
        "inference_latency_ms": result_dict.get("inference_latency_ms", 0.0),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    records = _load()
    records.append(record)
    _save(records)
    return record


def get_history(username: str, limit: int = 50) -> list[dict]:
    """Return the most recent `limit` records for a user, newest first.

    50 is the UI page size — enough history to be useful without large responses.
    """
    records = _load()
    user_records = [r for r in records if r["username"] == username]
    user_records.sort(key=lambda r: r["timestamp"], reverse=True)
    return user_records[:limit]
