"""Unit tests for support-related Pydantic schemas."""
import pytest
from pydantic import ValidationError
from backend.app.schemas import TicketCreate, TicketResponse, ChatRequest, ChatResponse, ResolveRequest


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


def test_ticket_response_rejects_invalid_status():
    with pytest.raises(ValidationError):
        TicketResponse(
            id="TK-1",
            username="user1",
            subject="Bug",
            description="detail",
            status="pending",  # invalid — not "open" or "resolved"
            created_at="2026-04-16T10:00:00+00:00",
        )


def test_resolve_request_valid():
    r = ResolveRequest(resolution="Fixed in v1.2")
    assert r.resolution == "Fixed in v1.2"


def test_resolve_request_rejects_empty():
    with pytest.raises(ValidationError):
        ResolveRequest(resolution="")
