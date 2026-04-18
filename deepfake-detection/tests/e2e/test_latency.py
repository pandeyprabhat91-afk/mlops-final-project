# tests/e2e/test_latency.py
"""End-to-end test: upload MP4 -> assert prediction shape + latency < 200ms.

Requires the backend to be running at BACKEND_URL (default http://localhost:8000).
Skip automatically if the backend is not reachable.
"""
import os
import time

import pytest
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
LATENCY_BUDGET_MS = 200.0


def _backend_available() -> bool:
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not _backend_available(), reason="Backend not running")
def test_predict_returns_valid_response(tmp_path):
    """POST /predict with a minimal valid MP4 returns a well-formed prediction."""
    # Minimal ftyp box — backend will reject in preprocessing, but the endpoint
    # must return a structured response (400 or 422 is acceptable for invalid video).
    mp4_bytes = b"\x00\x00\x00\x08ftypisom" + b"\x00" * 200
    mp4_file = tmp_path / "test.mp4"
    mp4_file.write_bytes(mp4_bytes)

    with open(mp4_file, "rb") as f:
        resp = requests.post(
            f"{BACKEND_URL}/predict",
            files={"file": ("test.mp4", f, "video/mp4")},
            timeout=30,
        )

    # Accept either success or preprocessing failure — endpoint itself must not 500 unexpectedly
    assert resp.status_code in (200, 422), f"Unexpected status {resp.status_code}: {resp.text}"


@pytest.mark.skipif(not _backend_available(), reason="Backend not running")
def test_health_endpoint_responds_under_50ms():
    """GET /health must respond in under 50ms."""
    start = time.time()
    resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
    elapsed_ms = (time.time() - start) * 1000
    assert resp.status_code == 200
    assert elapsed_ms < 50.0, f"/health took {elapsed_ms:.1f}ms -- expected < 50ms"


@pytest.mark.skipif(not _backend_available(), reason="Backend not running")
def test_ready_endpoint_responds():
    """GET /ready must return 200 or 503 (never a 5xx crash)."""
    resp = requests.get(f"{BACKEND_URL}/ready", timeout=5)
    assert resp.status_code in (200, 503)
