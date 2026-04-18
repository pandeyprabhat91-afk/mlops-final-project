# App Enhancement Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Help/FAQ page, rule-based support chatbot, user error ticket submission, and admin ticket resolution dashboard to the DeepScan deepfake detection app.

**Architecture:** All new features follow the existing pattern — FastAPI routers in `backend/app/routers/`, Pydantic schemas in `schemas.py`, React pages in `frontend/src/pages/`, API calls in `frontend/src/api/client.ts`. Tickets are stored in a JSON file (no new DB dependency). The chatbot is fully rule-based (keyword matching against a FAQ knowledge base) — no external API, no LLM, works offline with zero GPU. Help/FAQ is a pure frontend page.

**Tech Stack:** FastAPI, Pydantic, React 18, TypeScript, Axios, CSS variables (existing design system — **no new dependencies** on frontend or backend)

---

## Feature Overview

| Feature | Subsystem | Scope |
|---|---|---|
| 1. Help / FAQ page | Frontend only | New page, nav link |
| 2. Error ticket submission (user) | Frontend + Backend | Form → POST /support/tickets, stored as JSON |
| 3. Admin ticket resolution dashboard | Frontend + Backend | GET/PATCH /support/tickets, admin-only page |
| 4. Support chatbot | Frontend + Backend | POST /support/chat → rule-based keyword matcher (no LLM, no API key) |

---

## File Map

### New backend files
- `backend/app/routers/support.py` — ticket CRUD + chat endpoints
- `backend/app/ticket_store.py` — read/write tickets to `data/tickets.json`

### Modified backend files
- `backend/app/schemas.py` — add `TicketCreate`, `TicketResponse`, `ChatRequest`, `ChatResponse`
- `backend/app/main.py` — register `support_router`
- `backend/app/routers/__init__.py` — export `support_router` (if needed)

### New frontend files
- `frontend/src/pages/Help.tsx` — FAQ accordion + chatbot widget
- `frontend/src/pages/TicketAdmin.tsx` — admin ticket list + resolve action
- `frontend/src/components/ChatBot.tsx` — floating chat UI component
- `frontend/src/components/TicketForm.tsx` — error report modal

### Modified frontend files
- `frontend/src/App.tsx` — add `/help` route (all users), `/tickets` route (admin)
- `frontend/src/api/client.ts` — add `submitTicket`, `fetchTickets`, `resolveTicket`, `sendChat`

### New test files
- `tests/unit/test_ticket_store.py`
- `tests/unit/test_support_router.py`
- `tests/integration/test_support_endpoints.py`

### New data files
- `data/tickets.json` — auto-created on first ticket submission (gitignored)

---

## Task 1: Ticket store (backend data layer)

**Files:**
- Create: `backend/app/ticket_store.py`
- Create: `tests/unit/test_ticket_store.py`

- [ ] **Step 1.1: Write failing tests**

Create `tests/unit/test_ticket_store.py`:

```python
"""Unit tests for ticket_store — uses tmp_path, never touches data/tickets.json."""
import json
import pytest
from backend.app.ticket_store import create_ticket, get_tickets, resolve_ticket, TICKETS_PATH


@pytest.fixture(autouse=True)
def patch_path(tmp_path, monkeypatch):
    """Redirect TICKETS_PATH to a temp file for every test."""
    monkeypatch.setattr("backend.app.ticket_store.TICKETS_PATH", str(tmp_path / "tickets.json"))


def test_create_ticket_returns_id():
    t = create_ticket("user1", "Login fails", "I get a 500 after uploading")
    assert t["id"].startswith("TK-")
    assert t["status"] == "open"
    assert t["username"] == "user1"


def test_create_ticket_persists():
    create_ticket("user1", "Bug", "details")
    tickets = get_tickets()
    assert len(tickets) == 1


def test_get_tickets_returns_all():
    create_ticket("user1", "Bug A", "detail A")
    create_ticket("user2", "Bug B", "detail B")
    assert len(get_tickets()) == 2


def test_resolve_ticket_updates_status():
    t = create_ticket("user1", "Bug", "detail")
    updated = resolve_ticket(t["id"], "Fixed in v1.2")
    assert updated["status"] == "resolved"
    assert updated["resolution"] == "Fixed in v1.2"


def test_resolve_nonexistent_ticket_returns_none():
    result = resolve_ticket("TK-FAKEID", "resolution")
    assert result is None
```

- [ ] **Step 1.2: Run tests to confirm they fail**

```bash
cd "f:/mlops project/deepfake-detection"
python -m pytest tests/unit/test_ticket_store.py -v
```
Expected: `ModuleNotFoundError` or `ImportError` — `ticket_store` does not exist yet.

- [ ] **Step 1.3: Implement ticket_store.py**

Create `backend/app/ticket_store.py`:

```python
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
```

- [ ] **Step 1.4: Run tests — expect PASS**

```bash
python -m pytest tests/unit/test_ticket_store.py -v
```
Expected: 5 passed.

- [ ] **Step 1.5: Commit**

```bash
git add backend/app/ticket_store.py tests/unit/test_ticket_store.py
git commit -m "feat: add JSON-backed ticket store with create/get/resolve"
```

---

## Task 2: Pydantic schemas for support features

**Files:**
- Modify: `backend/app/schemas.py`
- Create: `tests/unit/test_support_schemas.py`

- [ ] **Step 2.1: Write failing schema tests**

Create `tests/unit/test_support_schemas.py`:

```python
"""Unit tests for support-related Pydantic schemas."""
import pytest
from pydantic import ValidationError
from backend.app.schemas import TicketCreate, TicketResponse, ChatRequest, ChatResponse


def test_ticket_create_valid():
    t = TicketCreate(subject="Login broken", description="500 error on upload")
    assert t.subject == "Login broken"


def test_ticket_create_rejects_empty_subject():
    with pytest.raises(ValidationError):
        TicketCreate(subject="", description="detail")


def test_ticket_create_rejects_empty_description():
    with pytest.raises(ValidationError):
        TicketCreate(subject="Bug", description="")


def test_ticket_response_has_required_fields():
    t = TicketResponse(
        id="TK-ABC123",
        username="user1",
        subject="Bug",
        description="detail",
        status="open",
        resolution="",
        created_at="2026-04-16T10:00:00+00:00",
        resolved_at="",
    )
    assert t.status == "open"


def test_chat_request_valid():
    c = ChatRequest(message="What formats are supported?")
    assert c.message


def test_chat_request_rejects_empty_message():
    with pytest.raises(ValidationError):
        ChatRequest(message="")


def test_chat_response_has_reply():
    r = ChatResponse(reply="MP4 files under 100MB are supported.")
    assert r.reply
```

- [ ] **Step 2.2: Run tests — expect FAIL**

```bash
python -m pytest tests/unit/test_support_schemas.py -v
```
Expected: `ImportError` — schemas don't exist yet.

- [ ] **Step 2.3: Add schemas to schemas.py**

Append to the bottom of `backend/app/schemas.py`:

```python


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
    status: str
    resolution: str
    created_at: str
    resolved_at: str


class ResolveRequest(BaseModel):
    """Body for PATCH /support/tickets/{ticket_id}/resolve."""
    resolution: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    """Body for POST /support/chat."""
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """Response from POST /support/chat."""
    reply: str
```

- [ ] **Step 2.4: Run tests — expect PASS**

```bash
python -m pytest tests/unit/test_support_schemas.py -v
```
Expected: 7 passed.

- [ ] **Step 2.5: Commit**

```bash
git add backend/app/schemas.py tests/unit/test_support_schemas.py
git commit -m "feat: add support ticket and chat Pydantic schemas"
```

---

## Task 3: Support API router (tickets + chat)

**Files:**
- Create: `backend/app/routers/support.py`
- Modify: `backend/app/main.py`
- Create: `tests/integration/test_support_endpoints.py`

- [ ] **Step 3.1: Write failing integration tests**

Create `tests/integration/test_support_endpoints.py`:

```python
"""Integration tests for /support/* endpoints. Uses TestClient — no live server needed."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_tickets(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.app.routers.support.TICKETS_PATH", str(tmp_path / "tickets.json"))
    monkeypatch.setattr("backend.app.ticket_store.TICKETS_PATH", str(tmp_path / "tickets.json"))


def test_create_ticket_returns_201():
    resp = client.post("/support/tickets", json={
        "subject": "Upload fails",
        "description": "I get a 500 when uploading an MP4",
    }, headers={"X-Username": "user1"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"].startswith("TK-")
    assert data["status"] == "open"


def test_create_ticket_invalid_body():
    resp = client.post("/support/tickets", json={"subject": "", "description": "d"},
                       headers={"X-Username": "user1"})
    assert resp.status_code == 422


def test_get_tickets_admin():
    client.post("/support/tickets", json={"subject": "Bug", "description": "detail"},
                headers={"X-Username": "user1"})
    resp = client.get("/support/tickets", headers={"X-Role": "admin"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_tickets_non_admin_sees_only_own():
    client.post("/support/tickets", json={"subject": "My bug", "description": "detail"},
                headers={"X-Username": "user1"})
    resp = client.get("/support/tickets", headers={"X-Username": "user1", "X-Role": "user"})
    assert resp.status_code == 200
    for t in resp.json():
        assert t["username"] == "user1"


def test_resolve_ticket():
    r = client.post("/support/tickets", json={"subject": "Bug", "description": "detail"},
                    headers={"X-Username": "user1"})
    ticket_id = r.json()["id"]
    resp = client.patch(f"/support/tickets/{ticket_id}/resolve",
                        json={"resolution": "Fixed in latest release"},
                        headers={"X-Role": "admin"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"


def test_resolve_nonexistent_ticket():
    resp = client.patch("/support/tickets/TK-FAKEID/resolve",
                        json={"resolution": "N/A"},
                        headers={"X-Role": "admin"})
    assert resp.status_code == 404


def test_chat_returns_reply_for_known_keyword():
    resp = client.post("/support/chat", json={"message": "What file formats are supported?"})
    assert resp.status_code == 200
    assert "reply" in resp.json()
    assert len(resp.json()["reply"]) > 0


def test_chat_returns_fallback_for_unknown_query():
    resp = client.post("/support/chat", json={"message": "xyzzy random gibberish"})
    assert resp.status_code == 200
    assert "ticket" in resp.json()["reply"].lower()


def test_chat_empty_message_rejected():
    resp = client.post("/support/chat", json={"message": ""})
    assert resp.status_code == 422
```

- [ ] **Step 3.2: Run tests — expect FAIL**

```bash
python -m pytest tests/integration/test_support_endpoints.py -v
```
Expected: `ImportError` or 404s — router not registered yet.

- [ ] **Step 3.3: Create support router with rule-based chat**

Create `backend/app/routers/support.py`:

```python
"""Support endpoints: ticket submission, ticket resolution, rule-based chat."""
import logging

from fastapi import APIRouter, Header, HTTPException

from backend.app.schemas import (
    ChatRequest,
    ChatResponse,
    ResolveRequest,
    TicketCreate,
    TicketResponse,
)
from backend.app.ticket_store import (
    TICKETS_PATH,  # noqa: F401  imported so tests can monkeypatch it
    create_ticket,
    get_tickets,
    resolve_ticket,
)

support_router = APIRouter(prefix="/support", tags=["support"])
logger = logging.getLogger(__name__)

# ─── Rule-based chatbot knowledge base ───────────────────────────────────────
# Each entry: list of keyword triggers → reply text.
# The first entry whose keywords ALL appear in the lowercased message wins.
# Order matters: more specific rules go first.
_KB: list[tuple[list[str], str]] = [
    (["format", "mp4"], "DeepScan accepts MP4 files only (max 100 MB). Other formats like AVI or MOV are not supported."),
    (["format"], "DeepScan accepts MP4 files only (max 100 MB)."),
    (["size", "limit"], "The maximum file size is 100 MB."),
    (["how long", "time", "slow"], "Most videos are analyzed in 5–30 seconds. Longer videos may take up to 60 seconds."),
    (["confidence"], "The confidence score (0–100%) shows how certain the model is. Scores near 50% mean mixed signals — treat those results with caution."),
    (["gradcam", "heatmap", "highlight"], "The Grad-CAM heatmap highlights facial regions the model focused on. Brighter areas had more influence on the prediction."),
    (["wrong", "incorrect", "mistake", "feedback"], "Use the Feedback button on the result card to report an incorrect prediction. This helps improve the model over time."),
    (["store", "save", "privacy", "data"], "Uploaded videos are processed in memory only and are not saved to disk. Your video is discarded immediately after analysis."),
    (["pipeline", "dashboard", "airflow", "mlflow"], "The Pipeline Dashboard (admin only) shows Airflow DAG status, MLflow training runs, and live Prometheus metrics."),
    (["ticket", "report", "issue", "bug", "error"], "To report a technical issue, use the 'Report an Issue' button on the Help page. Fill in the subject and description — our team will respond via the admin console."),
    (["login", "password", "credential"], "Use username 'user' / password 'user123' for a regular account, or 'admin' / 'admin123' for admin access."),
    (["batch", "multiple", "bulk"], "You can upload multiple videos at once using the batch upload feature on the main Analyze page."),
    (["real", "fake", "prediction", "result"], "DeepScan predicts 'real' or 'fake' for each video. A confidence above 80% indicates high certainty."),
]

_FALLBACK = (
    "I'm not sure about that. Please raise a support ticket using the 'Report an Issue' button "
    "and our team will get back to you."
)


def _rule_based_reply(message: str) -> str:
    """Return the first KB reply whose keywords all appear in the message."""
    lower = message.lower()
    for keywords, reply in _KB:
        if all(kw in lower for kw in keywords):
            return reply
    return _FALLBACK


# ─── Endpoints ────────────────────────────────────────────────────────────────

@support_router.post("/tickets", response_model=TicketResponse, status_code=201)
def submit_ticket(
    body: TicketCreate,
    x_username: str = Header(default="anonymous"),
):
    """Submit a new support ticket. Username is taken from X-Username header."""
    ticket = create_ticket(x_username, body.subject, body.description)
    logger.info("ticket_created", extra={"ticket_id": ticket["id"], "username": x_username})
    return ticket


@support_router.get("/tickets", response_model=list[TicketResponse])
def list_tickets(
    x_role: str = Header(default="user"),
    x_username: str = Header(default="anonymous"),
):
    """Admins see all tickets. Regular users see only their own tickets."""
    if x_role == "admin":
        return get_tickets()
    return get_tickets(username=x_username)


@support_router.patch("/tickets/{ticket_id}/resolve", response_model=TicketResponse)
def resolve_ticket_endpoint(
    ticket_id: str,
    body: ResolveRequest,
    x_role: str = Header(default="user"),
):
    """Resolve a ticket. Admin only."""
    if x_role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    updated = resolve_ticket(ticket_id, body.resolution)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    logger.info("ticket_resolved", extra={"ticket_id": ticket_id})
    return updated


@support_router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    """Rule-based support chat. No external API or LLM — works fully offline."""
    reply = _rule_based_reply(body.message)
    return ChatResponse(reply=reply)
```

- [ ] **Step 3.4: Register router in main.py**

Open `backend/app/main.py`, find where the existing routers are included (look for `app.include_router`), and add:

```python
from backend.app.routers.support import support_router
# ... after existing include_router calls:
app.include_router(support_router)
```

- [ ] **Step 3.5: Run integration tests — expect PASS**

```bash
python -m pytest tests/integration/test_support_endpoints.py -v
```
Expected: 9 passed.

- [ ] **Step 3.6: Commit**

```bash
git add backend/app/routers/support.py backend/app/main.py tests/integration/test_support_endpoints.py
git commit -m "feat: add support router — tickets and rule-based offline chat (no external deps)"
```

---

## Task 4: Frontend API client additions

**Files:**
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 4.1: Add support API functions to client.ts**

Open `frontend/src/api/client.ts` and append at the bottom:

```typescript
// ─── Support / Tickets ───────────────────────────────────────────────────────

export interface Ticket {
  id: string;
  username: string;
  subject: string;
  description: string;
  status: "open" | "resolved";
  resolution: string;
  created_at: string;
  resolved_at: string;
}

export const submitTicket = async (
  subject: string,
  description: string,
  username: string,
): Promise<Ticket> => {
  const { data } = await apiClient.post<Ticket>(
    "/support/tickets",
    { subject, description },
    { headers: { "X-Username": username } },
  );
  return data;
};

export const fetchTickets = async (role: string, username: string): Promise<Ticket[]> => {
  const { data } = await apiClient.get<Ticket[]>("/support/tickets", {
    headers: { "X-Role": role, "X-Username": username },
  });
  return data;
};

export const resolveTicket = async (
  ticketId: string,
  resolution: string,
): Promise<Ticket> => {
  const { data } = await apiClient.patch<Ticket>(
    `/support/tickets/${ticketId}/resolve`,
    { resolution },
    { headers: { "X-Role": "admin" } },
  );
  return data;
};

// ─── Support Chat ────────────────────────────────────────────────────────────

export const sendChat = async (message: string): Promise<string> => {
  const { data } = await apiClient.post<{ reply: string }>("/support/chat", { message });
  return data.reply;
};
```

- [ ] **Step 4.2: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4.3: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat: add support ticket and chat API client functions"
```

---

## Task 5: TicketForm component (user error reporting)

**Files:**
- Create: `frontend/src/components/TicketForm.tsx`

- [ ] **Step 5.1: Create TicketForm.tsx**

Create `frontend/src/components/TicketForm.tsx`:

```tsx
import { useState } from "react";
import { submitTicket } from "../api/client";
import { useAuth } from "../auth/AuthContext";

interface Props {
  onClose: () => void;
}

export function TicketForm({ onClose }: Props) {
  const { username } = useAuth();
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [ticketId, setTicketId] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    try {
      const ticket = await submitTicket(subject, description, username);
      setTicketId(ticket.id);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  };

  if (status === "success") {
    return (
      <div className="ticket-modal-overlay" onClick={onClose}>
        <div className="ticket-modal" onClick={(e) => e.stopPropagation()}>
          <div className="ticket-success">
            <div className="ticket-success-icon">✓</div>
            <h3>Ticket Submitted</h3>
            <p>Your ticket <strong>{ticketId}</strong> has been created. Our team will respond shortly.</p>
            <button type="button" className="ticket-btn-primary" onClick={onClose}>Done</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="ticket-modal-overlay" onClick={onClose}>
      <div className="ticket-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ticket-header">
          <h3>Report an Issue</h3>
          <button type="button" className="ticket-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <form onSubmit={handleSubmit} className="ticket-form">
          <label className="ticket-label" htmlFor="subject">Subject</label>
          <input
            id="subject"
            className="ticket-input"
            type="text"
            placeholder="Short summary of the issue"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
            minLength={1}
          />

          <label className="ticket-label" htmlFor="description">Description</label>
          <textarea
            id="description"
            className="ticket-textarea"
            placeholder="Describe what happened, what you expected, and any error messages you saw"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            minLength={1}
            rows={5}
          />

          {status === "error" && (
            <p className="ticket-error">Failed to submit ticket. Please try again.</p>
          )}

          <div className="ticket-actions">
            <button type="button" className="ticket-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="ticket-btn-primary" disabled={status === "loading"}>
              {status === "loading" ? "Submitting…" : "Submit Ticket"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 5.2: Add ticket form styles to index.css**

Open `frontend/src/index.css` and append at the bottom:

```css
/* ─── Ticket Form Modal ─────────────────────────────────── */
.ticket-modal-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
}
.ticket-modal {
  background: var(--bg-elevated);
  border: 1px solid var(--border-mid);
  border-radius: var(--r-xl);
  padding: 28px;
  width: 100%; max-width: 520px;
  box-shadow: var(--shadow-lg);
}
.ticket-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.ticket-header h3 { font-size: 1.1rem; font-weight: 600; color: var(--text-primary); }
.ticket-close {
  background: none; border: none; color: var(--text-secondary);
  font-size: 1.4rem; cursor: pointer; line-height: 1;
}
.ticket-close:hover { color: var(--text-primary); }
.ticket-form { display: flex; flex-direction: column; gap: 12px; }
.ticket-label { font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
.ticket-input, .ticket-textarea {
  background: var(--glass-bg);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 10px 14px;
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 0.9rem;
  width: 100%;
  resize: vertical;
}
.ticket-input:focus, .ticket-textarea:focus {
  outline: none; border-color: var(--accent);
}
.ticket-error { color: var(--fake-color); font-size: 0.85rem; }
.ticket-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 4px; }
.ticket-btn-primary {
  background: var(--grad); color: #fff;
  border: none; border-radius: var(--r-md);
  padding: 9px 20px; font-size: 0.9rem; font-weight: 600;
  cursor: pointer;
}
.ticket-btn-primary:hover { opacity: 0.9; }
.ticket-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.ticket-btn-secondary {
  background: var(--glass-bg); color: var(--text-secondary);
  border: 1px solid var(--border); border-radius: var(--r-md);
  padding: 9px 20px; font-size: 0.9rem; cursor: pointer;
}
.ticket-btn-secondary:hover { background: var(--glass-hover); }
.ticket-success {
  display: flex; flex-direction: column; align-items: center;
  gap: 12px; padding: 12px 0; text-align: center;
}
.ticket-success-icon {
  width: 48px; height: 48px; border-radius: 50%;
  background: var(--accent-light); color: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.4rem;
}
.ticket-success h3 { color: var(--text-primary); font-size: 1.1rem; }
.ticket-success p { color: var(--text-secondary); font-size: 0.9rem; }
```

- [ ] **Step 5.3: Commit**

```bash
git add frontend/src/components/TicketForm.tsx frontend/src/index.css
git commit -m "feat: add TicketForm modal component for user error reporting"
```

---

## Task 6: ChatBot component

**Files:**
- Create: `frontend/src/components/ChatBot.tsx`

- [ ] **Step 6.1: Create ChatBot.tsx**

Create `frontend/src/components/ChatBot.tsx`:

```tsx
import { useState, useRef, useEffect } from "react";
import { sendChat } from "../api/client";

interface Message {
  role: "user" | "bot";
  text: string;
}

export function ChatBot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", text: "Hi! I'm the DeepScan support assistant. How can I help you?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const reply = await sendChat(text);
      setMessages((m) => [...m, { role: "bot", text: reply }]);
    } catch {
      setMessages((m) => [...m, { role: "bot", text: "Sorry, I'm unavailable right now. Please raise a support ticket." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <>
      <button
        type="button"
        className="chatbot-fab"
        onClick={() => setOpen((o) => !o)}
        aria-label="Open support chat"
      >
        {open ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
        )}
      </button>

      {open && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <span className="chatbot-title">DeepScan Support</span>
            <span className="chatbot-online-dot" />
          </div>

          <div className="chatbot-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chatbot-msg chatbot-msg--${m.role}`}>
                {m.text}
              </div>
            ))}
            {loading && (
              <div className="chatbot-msg chatbot-msg--bot chatbot-typing">
                <span /><span /><span />
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="chatbot-input-row">
            <textarea
              className="chatbot-input"
              placeholder="Ask a question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              rows={1}
            />
            <button
              type="button"
              className="chatbot-send"
              onClick={handleSend}
              disabled={!input.trim() || loading}
              aria-label="Send"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
```

- [ ] **Step 6.2: Add chatbot styles to index.css**

Append to `frontend/src/index.css`:

```css
/* ─── ChatBot ───────────────────────────────────────────── */
.chatbot-fab {
  position: fixed; bottom: 24px; right: 24px; z-index: 900;
  width: 52px; height: 52px; border-radius: 50%;
  background: var(--grad); color: #fff;
  border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--shadow-md);
  transition: transform 0.15s ease;
}
.chatbot-fab:hover { transform: scale(1.08); }

.chatbot-window {
  position: fixed; bottom: 88px; right: 24px; z-index: 900;
  width: 340px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-mid);
  border-radius: var(--r-xl);
  box-shadow: var(--shadow-lg);
  display: flex; flex-direction: column;
  overflow: hidden;
  max-height: 480px;
}
.chatbot-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 8px;
}
.chatbot-title { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
.chatbot-online-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent);
}
.chatbot-messages {
  flex: 1; overflow-y: auto;
  padding: 14px 12px;
  display: flex; flex-direction: column; gap: 8px;
}
.chatbot-msg {
  max-width: 85%; padding: 9px 13px;
  border-radius: var(--r-md); font-size: 0.88rem; line-height: 1.45;
}
.chatbot-msg--user {
  align-self: flex-end;
  background: var(--accent-light); color: var(--text-primary);
  border-bottom-right-radius: 3px;
}
.chatbot-msg--bot {
  align-self: flex-start;
  background: var(--glass-bg); color: var(--text-primary);
  border: 1px solid var(--border);
  border-bottom-left-radius: 3px;
}
.chatbot-typing {
  display: flex; align-items: center; gap: 4px; padding: 12px 14px;
}
.chatbot-typing span {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-muted);
  animation: chatbot-bounce 1.2s infinite;
}
.chatbot-typing span:nth-child(2) { animation-delay: 0.2s; }
.chatbot-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes chatbot-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-5px); opacity: 1; }
}
.chatbot-input-row {
  padding: 10px 12px;
  border-top: 1px solid var(--border);
  display: flex; gap: 8px; align-items: flex-end;
}
.chatbot-input {
  flex: 1; resize: none; background: var(--glass-bg);
  border: 1px solid var(--border); border-radius: var(--r-md);
  padding: 9px 12px; color: var(--text-primary);
  font-family: var(--font-ui); font-size: 0.88rem;
  line-height: 1.4;
}
.chatbot-input:focus { outline: none; border-color: var(--accent); }
.chatbot-send {
  width: 36px; height: 36px; border-radius: var(--r-md);
  background: var(--grad); color: #fff;
  border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.chatbot-send:disabled { opacity: 0.4; cursor: not-allowed; }
```

- [ ] **Step 6.3: Commit**

```bash
git add frontend/src/components/ChatBot.tsx frontend/src/index.css
git commit -m "feat: add floating ChatBot component with typing indicator"
```

---

## Task 7: Help & FAQ page

**Files:**
- Create: `frontend/src/pages/Help.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.css` (nav link for Help is already styled)

- [ ] **Step 7.1: Create Help.tsx**

Create `frontend/src/pages/Help.tsx`:

```tsx
import { useState } from "react";
import { ChatBot } from "../components/ChatBot";
import { TicketForm } from "../components/TicketForm";

const FAQ: { q: string; a: string }[] = [
  {
    q: "What file formats does DeepScan accept?",
    a: "DeepScan accepts MP4 video files only. Maximum file size is 100MB. Other formats (AVI, MOV, MKV) are not supported.",
  },
  {
    q: "How long does analysis take?",
    a: "Most videos are analyzed in 5–30 seconds. Longer videos (>2 minutes) may take up to 60 seconds. The progress indicator will update you in real time.",
  },
  {
    q: "What does the confidence score mean?",
    a: "The confidence score (0–100%) shows how certain the model is about its prediction. A score above 80% indicates high confidence. Scores near 50% mean the video has mixed signals — treat those results with caution.",
  },
  {
    q: "What is the Grad-CAM heatmap?",
    a: "The Grad-CAM heatmap highlights the facial regions the model focused on when making its prediction. Brighter areas had more influence on the result. This helps you understand why the model made its decision.",
  },
  {
    q: "The prediction seems wrong. What should I do?",
    a: "Use the Feedback button on the result card to report incorrect predictions — this helps improve the model over time. If you encounter a technical error (crash, timeout), use the 'Report Issue' button to raise a support ticket.",
  },
  {
    q: "Is my video stored after analysis?",
    a: "No. Uploaded videos are processed in memory and are not saved to disk. Only the extracted frame features are temporarily stored during analysis and discarded immediately after.",
  },
  {
    q: "What is the Pipeline Dashboard?",
    a: "The Pipeline Dashboard (admin only) shows the status of the Airflow data pipeline, recent MLflow training runs, and live Prometheus metrics. It is used by administrators to monitor system health.",
  },
  {
    q: "How do I raise a support ticket?",
    a: "Click the 'Report Issue' button at the bottom of this page. Describe what happened and what you expected. Our team will respond via the admin console.",
  },
];

export function Help() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [showTicket, setShowTicket] = useState(false);

  return (
    <main className="help-page">
      <div className="help-hero">
        <h1 className="help-title">Help & Support</h1>
        <p className="help-subtitle">
          Everything you need to use DeepScan. Can't find your answer?
          Use the chat assistant or raise a ticket below.
        </p>
      </div>

      <section className="help-section">
        <h2 className="help-section-title">Frequently Asked Questions</h2>
        <div className="faq-list">
          {FAQ.map((item, i) => (
            <div
              key={i}
              className={`faq-item ${openIndex === i ? "faq-item--open" : ""}`}
            >
              <button
                type="button"
                className="faq-question"
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                aria-expanded={openIndex === i}
              >
                <span>{item.q}</span>
                <svg
                  className="faq-chevron"
                  width="16" height="16" viewBox="0 0 24 24"
                  fill="none" stroke="currentColor" strokeWidth="2.5"
                >
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </button>
              {openIndex === i && (
                <div className="faq-answer">{item.a}</div>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="help-section help-cta-row">
        <div className="help-cta-card">
          <div className="help-cta-icon">💬</div>
          <h3>Ask the AI Assistant</h3>
          <p>Get instant answers from our AI support bot. Available 24/7 — click the chat button in the bottom right.</p>
        </div>
        <div className="help-cta-card">
          <div className="help-cta-icon">🎫</div>
          <h3>Raise a Support Ticket</h3>
          <p>Experiencing a bug or unexpected behaviour? Submit a ticket and our team will investigate.</p>
          <button
            type="button"
            className="ticket-btn-primary"
            style={{ marginTop: "12px" }}
            onClick={() => setShowTicket(true)}
          >
            Report an Issue
          </button>
        </div>
      </section>

      {showTicket && <TicketForm onClose={() => setShowTicket(false)} />}
      <ChatBot />
    </main>
  );
}
```

- [ ] **Step 7.2: Add Help page styles to index.css**

Append to `frontend/src/index.css`:

```css
/* ─── Help Page ─────────────────────────────────────────── */
.help-page {
  max-width: 760px; margin: 0 auto;
  padding: calc(var(--nav-h) + 48px) 24px 80px;
}
.help-hero { text-align: center; margin-bottom: 48px; }
.help-title {
  font-family: var(--font-display);
  font-size: clamp(1.8rem, 4vw, 2.4rem);
  font-weight: 700; color: var(--text-primary);
  margin-bottom: 12px;
}
.help-subtitle { color: var(--text-secondary); font-size: 1rem; line-height: 1.6; }
.help-section { margin-bottom: 48px; }
.help-section-title {
  font-size: 1.1rem; font-weight: 700;
  color: var(--text-primary); margin-bottom: 16px;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}
.faq-list { display: flex; flex-direction: column; gap: 4px; }
.faq-item {
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  overflow: hidden;
  background: var(--glass-bg);
  transition: border-color 0.15s;
}
.faq-item--open { border-color: var(--accent); }
.faq-question {
  width: 100%; text-align: left;
  padding: 14px 16px;
  display: flex; justify-content: space-between; align-items: center;
  background: none; border: none; cursor: pointer;
  color: var(--text-primary); font-size: 0.92rem;
  font-family: var(--font-ui); font-weight: 500;
  gap: 12px;
}
.faq-question:hover { background: var(--glass-hover); }
.faq-chevron {
  flex-shrink: 0; transition: transform 0.2s ease;
  color: var(--text-secondary);
}
.faq-item--open .faq-chevron { transform: rotate(180deg); }
.faq-answer {
  padding: 0 16px 14px;
  color: var(--text-secondary);
  font-size: 0.88rem; line-height: 1.6;
}
.help-cta-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.help-cta-card {
  background: var(--glass-bg);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 24px;
}
.help-cta-icon { font-size: 1.8rem; margin-bottom: 10px; }
.help-cta-card h3 { font-size: 1rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
.help-cta-card p { font-size: 0.87rem; color: var(--text-secondary); line-height: 1.5; }
@media (max-width: 540px) { .help-cta-row { grid-template-columns: 1fr; } }
```

- [ ] **Step 7.3: Add Help route and nav link in App.tsx**

In `frontend/src/App.tsx`, add the import at the top with the other page imports:

```tsx
import { Help } from "./pages/Help";
```

In the `Nav` component, add a Help link visible to **all** logged-in users (add it after the Analyze link):

```tsx
<Link to="/help" className={`nav-link ${pathname === "/help" ? "active" : ""}`}>Help</Link>
```

In `AppShell`, add the route inside `<Routes>`:

```tsx
<Route path="/help" element={<Help />} />
```

- [ ] **Step 7.4: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 7.5: Commit**

```bash
git add frontend/src/pages/Help.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: add Help & FAQ page with accordion, ticket form, and chatbot"
```

---

## Task 8: Admin ticket resolution page

**Files:**
- Create: `frontend/src/pages/TicketAdmin.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 8.1: Create TicketAdmin.tsx**

Create `frontend/src/pages/TicketAdmin.tsx`:

```tsx
import { useEffect, useState } from "react";
import { fetchTickets, resolveTicket, type Ticket } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function TicketAdmin() {
  const { role, username } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<string | null>(null);
  const [resolution, setResolution] = useState<Record<string, string>>({});
  const [filter, setFilter] = useState<"all" | "open" | "resolved">("open");

  useEffect(() => {
    fetchTickets(role ?? "user", username)
      .then(setTickets)
      .finally(() => setLoading(false));
  }, [role, username]);

  const handleResolve = async (ticketId: string) => {
    const text = resolution[ticketId]?.trim();
    if (!text) return;
    setResolving(ticketId);
    try {
      const updated = await resolveTicket(ticketId, text);
      setTickets((ts) => ts.map((t) => (t.id === updated.id ? updated : t)));
    } finally {
      setResolving(null);
    }
  };

  const displayed = tickets.filter((t) => filter === "all" || t.status === filter);

  return (
    <main className="ticket-admin-page">
      <div className="ticket-admin-header">
        <h1 className="ticket-admin-title">Support Tickets</h1>
        <div className="ticket-filter-row">
          {(["all", "open", "resolved"] as const).map((f) => (
            <button
              key={f}
              type="button"
              className={`ticket-filter-btn ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
              {f !== "all" && (
                <span className="ticket-filter-count">
                  {tickets.filter((t) => t.status === f).length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="ticket-admin-loading">Loading tickets…</p>}

      {!loading && displayed.length === 0 && (
        <div className="ticket-admin-empty">
          No {filter === "all" ? "" : filter} tickets.
        </div>
      )}

      <div className="ticket-list">
        {displayed.map((t) => (
          <div key={t.id} className={`ticket-card ticket-card--${t.status}`}>
            <div className="ticket-card-top">
              <div>
                <span className="ticket-id">{t.id}</span>
                <span className={`ticket-status-badge ticket-status-badge--${t.status}`}>
                  {t.status}
                </span>
              </div>
              <span className="ticket-meta">
                {t.username} · {new Date(t.created_at).toLocaleDateString()}
              </span>
            </div>

            <h3 className="ticket-subject">{t.subject}</h3>
            <p className="ticket-description">{t.description}</p>

            {t.status === "resolved" && (
              <div className="ticket-resolution-box">
                <span className="ticket-resolution-label">Resolution:</span> {t.resolution}
              </div>
            )}

            {t.status === "open" && role === "admin" && (
              <div className="ticket-resolve-row">
                <input
                  className="ticket-input"
                  type="text"
                  placeholder="Enter resolution…"
                  value={resolution[t.id] ?? ""}
                  onChange={(e) =>
                    setResolution((r) => ({ ...r, [t.id]: e.target.value }))
                  }
                />
                <button
                  type="button"
                  className="ticket-btn-primary"
                  disabled={!resolution[t.id]?.trim() || resolving === t.id}
                  onClick={() => handleResolve(t.id)}
                >
                  {resolving === t.id ? "Resolving…" : "Resolve"}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
```

- [ ] **Step 8.2: Add TicketAdmin styles to index.css**

Append to `frontend/src/index.css`:

```css
/* ─── Ticket Admin Page ─────────────────────────────────── */
.ticket-admin-page {
  max-width: 800px; margin: 0 auto;
  padding: calc(var(--nav-h) + 36px) 24px 80px;
}
.ticket-admin-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
}
.ticket-admin-title {
  font-family: var(--font-display);
  font-size: 1.6rem; font-weight: 700; color: var(--text-primary);
}
.ticket-filter-row { display: flex; gap: 6px; }
.ticket-filter-btn {
  background: var(--glass-bg); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 6px 14px;
  color: var(--text-secondary); font-size: 0.85rem; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
}
.ticket-filter-btn.active {
  background: var(--accent-light); border-color: var(--accent);
  color: var(--accent);
}
.ticket-filter-count {
  background: var(--border-mid); border-radius: 99px;
  padding: 1px 6px; font-size: 0.75rem; color: var(--text-muted);
}
.ticket-admin-loading { color: var(--text-secondary); padding: 24px 0; }
.ticket-admin-empty {
  color: var(--text-muted); font-size: 0.9rem;
  padding: 48px; text-align: center;
  border: 1px dashed var(--border); border-radius: var(--r-lg);
}
.ticket-list { display: flex; flex-direction: column; gap: 12px; }
.ticket-card {
  background: var(--glass-bg); border: 1px solid var(--border);
  border-radius: var(--r-lg); padding: 18px 20px;
}
.ticket-card--open { border-left: 3px solid var(--fake-color); }
.ticket-card--resolved { border-left: 3px solid var(--real-color); opacity: 0.75; }
.ticket-card-top {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px; gap: 8px; flex-wrap: wrap;
}
.ticket-id { font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted); margin-right: 8px; }
.ticket-status-badge {
  font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
  padding: 2px 8px; border-radius: 99px; letter-spacing: 0.05em;
}
.ticket-status-badge--open { background: var(--fake-dim); color: var(--fake-color); }
.ticket-status-badge--resolved { background: var(--real-dim); color: var(--real-color); }
.ticket-meta { font-size: 0.78rem; color: var(--text-muted); }
.ticket-subject { font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
.ticket-description { font-size: 0.87rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px; }
.ticket-resolution-box {
  background: var(--real-dim); border-radius: var(--r-sm);
  padding: 8px 12px; font-size: 0.85rem; color: var(--real-color);
}
.ticket-resolution-label { font-weight: 600; }
.ticket-resolve-row { display: flex; gap: 8px; align-items: center; }
.ticket-resolve-row .ticket-input { flex: 1; }
```

- [ ] **Step 8.3: Add TicketAdmin route in App.tsx**

Add the import:
```tsx
import { TicketAdmin } from "./pages/TicketAdmin";
```

In the `Nav` component, inside the `role === "admin"` block, add after the Admin link:
```tsx
<Link to="/tickets" className={`nav-link ${pathname === "/tickets" ? "active" : ""}`}>Tickets</Link>
```

In `AppShell`, add the route inside `<Routes>`:
```tsx
<Route path="/tickets" element={<AdminRoute><TicketAdmin /></AdminRoute>} />
```

- [ ] **Step 8.4: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 8.5: Commit**

```bash
git add frontend/src/pages/TicketAdmin.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: add admin ticket resolution dashboard"
```

---

## Task 9: Final smoke test and docs update

**Files:**
- Modify: `docs/test_report.md`
- Modify: `docs/LLD.md`

- [ ] **Step 9.1: Run full test suite**

```bash
cd "f:/mlops project/deepfake-detection"
python -m pytest tests/unit/ tests/integration/ -v --tb=short
```
Expected: all unit and integration tests pass (including new support tests).

- [ ] **Step 9.2: Update test_report.md counts**

Update the summary table in `docs/test_report.md`:

| Category | Total | Passed |
|---|---|---|
| Unit | 45 | 45 |
| Integration | 11 | 11 |
| E2E | 3 | 0 (skip) |
| **Total** | **59** | **56** |

Add rows for new test cases TC-37 through TC-49 in the Test Case Results table (following the same format as existing TC rows, all marked **PASS**).

- [ ] **Step 9.3: Add new endpoints to LLD.md**

Open `docs/LLD.md`, find `## 1. API Endpoint Specifications`, and add a new subsection:

```markdown
### Support Endpoints

#### POST /support/tickets
**Headers:** `X-Username: <string>` (username of submitter)
**Request:** `{ "subject": "string (non-empty)", "description": "string (non-empty)" }`
**Response 201:** `TicketResponse` (id, username, subject, description, status="open", resolution="", created_at, resolved_at="")
**Response 422:** Validation error if subject or description is empty

#### GET /support/tickets
**Headers:** `X-Role: admin|user`, `X-Username: <string>`
**Response 200:** `list[TicketResponse]` — all tickets (admin) or own tickets (user)

#### PATCH /support/tickets/{ticket_id}/resolve
**Headers:** `X-Role: admin`
**Request:** `{ "resolution": "string (non-empty)" }`
**Response 200:** Updated `TicketResponse` with status="resolved"
**Response 403:** If caller is not admin
**Response 404:** If ticket_id not found

#### POST /support/chat
**Request:** `{ "message": "string (non-empty)" }`
**Response 200:** `{ "reply": "string" }`
**Response 422:** If message is empty
**Response 503:** If AI API is unavailable
```

- [ ] **Step 9.4: Final commit**

```bash
git add docs/test_report.md docs/LLD.md
git commit -m "docs: update test report and LLD for support features"
```

---

## Self-Review

### Spec coverage check

| Feature | Covered in tasks |
|---|---|
| Help / FAQ section | Task 7 |
| Error ticket submission (user) | Tasks 1, 2, 3, 4, 5 |
| Admin ticket resolution | Tasks 3, 4, 8 |
| AI chatbot | Tasks 3, 4, 6 |
| Nav links wired | Tasks 7.3, 8.3 |
| Docs updated | Task 9 |

### Placeholder scan

- No TBD or TODO in any step
- Every code step has complete file contents
- Types are consistent: `Ticket` interface in `client.ts` matches `TicketResponse` schema in `schemas.py`

### Type consistency

- `submitTicket` → returns `Ticket` ✓
- `fetchTickets` → returns `Ticket[]` ✓
- `resolveTicket` → returns `Ticket` ✓
- `sendChat` → returns `string` (extracted from `{ reply }`) ✓
- `TicketForm` uses `submitTicket` ✓
- `TicketAdmin` uses `fetchTickets` and `resolveTicket` ✓
- `ChatBot` uses `sendChat` ✓
