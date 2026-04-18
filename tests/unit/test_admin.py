# tests/unit/test_admin.py
from unittest.mock import patch


def test_rollback_to_version(client):
    with patch("backend.app.routers.admin.reload_to_version", return_value="deepfake/2") as mock_rb:
        resp = client.post("/admin/rollback", json={"version": "2"})
    assert resp.status_code == 200
    assert resp.json()["model_version"] == "deepfake/2"
    mock_rb.assert_called_once_with("2")


def test_rollback_invalid_version(client):
    with patch("backend.app.routers.admin.reload_to_version", side_effect=Exception("not found")):
        resp = client.post("/admin/rollback", json={"version": "999"})
    assert resp.status_code == 500


def test_model_info(client):
    resp = client.get("/admin/model-info")
    assert resp.status_code == 200
    data = resp.json()
    assert "model_version" in data
    assert "run_id" in data
    assert "model_loaded" in data
