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


def test_get_tickets_filters_by_username():
    create_ticket("alice", "Alice bug", "detail")
    create_ticket("bob", "Bob bug", "detail")
    alice_tickets = get_tickets(username="alice")
    assert len(alice_tickets) == 1
    assert alice_tickets[0]["username"] == "alice"
