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
