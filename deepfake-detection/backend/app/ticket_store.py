"""JSON-backed ticket store. Tickets are stored in data/tickets.json."""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

TICKETS_PATH = str(Path(__file__).parent.parent.parent / "data" / "tickets.json")


def _load() -> list[dict]:
    path = Path(TICKETS_PATH)
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f)


def _save(tickets: list[dict]) -> None:
    path = Path(TICKETS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(tickets, f, indent=2)


def create_ticket(username: str, subject: str, description: str) -> dict:
    """Create a new open ticket and persist it. Returns the ticket dict."""
    ticket_id = f"TK-{uuid.uuid4().hex[:8].upper()}"
    ticket = {
        "id": ticket_id,
        "username": username,
        "subject": subject,
        "description": description,
        "status": "open",
        "resolution": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": "",
    }
    tickets = _load()
    tickets.append(ticket)
    _save(tickets)
    return ticket


def get_tickets(username: str | None = None) -> list[dict]:
    """Return all tickets, or only those for a given username."""
    tickets = _load()
    if username:
        return [t for t in tickets if t["username"] == username]
    return tickets


def resolve_ticket(ticket_id: str, resolution: str) -> dict | None:
    """Mark a ticket as resolved. Returns updated ticket or None if not found."""
    tickets = _load()
    for t in tickets:
        if t["id"] == ticket_id:
            t["status"] = "resolved"
            t["resolution"] = resolution
            t["resolved_at"] = datetime.now(timezone.utc).isoformat()
            _save(tickets)
            return t
    return None
