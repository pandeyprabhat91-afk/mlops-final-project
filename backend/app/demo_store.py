"""IP-based demo usage tracker. Each IP gets exactly one demo session."""
import json
from datetime import datetime, timezone
from pathlib import Path

DEMO_PATH = str(Path(__file__).parent.parent.parent / "data" / "demo_ips.json")


def _load() -> dict:
    path = Path(DEMO_PATH)
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    path = Path(DEMO_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def has_used_demo(ip: str) -> bool:
    return ip in _load()


def record_demo_use(ip: str) -> None:
    data = _load()
    data[ip] = datetime.now(timezone.utc).isoformat()
    _save(data)
