# Value Additions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 9 independent UI/UX and feature enhancements to the DeepScan deepfake detection app.

**Architecture:** Backend adds a history store + endpoint following the existing `ticket_store.py` JSON-backed pattern. All 8 remaining features are pure frontend additions: new pages registered in `App.tsx`, new components wired into `Home.tsx`, and new styles appended to `index.css`. No new npm packages.

**Tech Stack:** FastAPI (backend), React 18 + TypeScript + Vite (frontend), CSS variables, framer-motion (already installed), axios (already installed).

---

## File Map

### New backend files
- `backend/app/history_store.py` — JSON-backed store for prediction history
- `tests/unit/test_history_store.py` — unit tests for store functions
- `tests/integration/test_history_endpoints.py` — integration tests for GET /history + predict-saves-history

### Modified backend files
- `backend/app/schemas.py` — add `HistoryRecord` Pydantic model
- `backend/app/routers/predict.py` — call `save_prediction` after inference; add `GET /history` endpoint

### New frontend files
- `frontend/src/pages/History.tsx` — prediction history table page
- `frontend/src/pages/Batch.tsx` — batch upload page
- `frontend/src/pages/ModelCard.tsx` — model card / about-the-model page
- `frontend/src/components/PipelineStatusBar.tsx` — compact status pills for Home page
- `frontend/src/components/ProgressBar.tsx` — simulated multi-stage progress bar
- `frontend/src/components/OnboardingTour.tsx` — 4-step tooltip tour for first-time users

### Modified frontend files
- `frontend/src/App.tsx` — add routes `/history`, `/batch`, `/model`; nav links
- `frontend/src/api/client.ts` — add `HistoryRecord` interface + `fetchHistory`
- `frontend/src/components/ResultCard.tsx` — add threshold slider + download report button
- `frontend/src/pages/Home.tsx` — add PipelineStatusBar, ProgressBar, OnboardingTour
- `frontend/src/index.css` — all new component styles + `[data-theme="light"]` override block
- `frontend/src/main.tsx` — theme restore from localStorage on page load

---

## Task 1: Backend — History Store

**Files:**
- Create: `backend/app/history_store.py`
- Create: `tests/unit/test_history_store.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_history_store.py
import json
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def tmp_history(tmp_path, monkeypatch):
    """Redirect HISTORY_PATH to a temp file for each test."""
    import backend.app.history_store as hs
    monkeypatch.setattr(hs, "HISTORY_PATH", str(tmp_path / "history.json"))
    yield


def test_save_prediction_returns_record():
    from backend.app.history_store import save_prediction
    record = save_prediction("alice", "clip.mp4", {
        "prediction": "fake", "confidence": 0.87,
        "inference_latency_ms": 123.4,
        "mlflow_run_id": "abc123", "frames_analyzed": 30,
    })
    assert record["id"].startswith("HR-")
    assert record["username"] == "alice"
    assert record["filename"] == "clip.mp4"
    assert record["prediction"] == "fake"
    assert abs(record["confidence"] - 0.87) < 0.001
    assert record["inference_latency_ms"] == pytest.approx(123.4)
    assert "timestamp" in record


def test_save_prediction_persists():
    from backend.app.history_store import save_prediction, get_history
    save_prediction("bob", "test.mp4", {
        "prediction": "real", "confidence": 0.12,
        "inference_latency_ms": 55.0,
        "mlflow_run_id": "run1", "frames_analyzed": 20,
    })
    records = get_history("bob")
    assert len(records) == 1
    assert records[0]["filename"] == "test.mp4"


def test_get_history_filters_by_username():
    from backend.app.history_store import save_prediction, get_history
    save_prediction("alice", "a.mp4", {"prediction": "fake", "confidence": 0.9,
        "inference_latency_ms": 100.0, "mlflow_run_id": "r1", "frames_analyzed": 30})
    save_prediction("bob", "b.mp4", {"prediction": "real", "confidence": 0.1,
        "inference_latency_ms": 90.0, "mlflow_run_id": "r2", "frames_analyzed": 30})
    assert len(get_history("alice")) == 1
    assert len(get_history("bob")) == 1
    assert get_history("alice")[0]["filename"] == "a.mp4"


def test_get_history_newest_first():
    from backend.app.history_store import save_prediction, get_history
    save_prediction("alice", "first.mp4", {"prediction": "fake", "confidence": 0.9,
        "inference_latency_ms": 100.0, "mlflow_run_id": "r1", "frames_analyzed": 30})
    save_prediction("alice", "second.mp4", {"prediction": "real", "confidence": 0.1,
        "inference_latency_ms": 80.0, "mlflow_run_id": "r2", "frames_analyzed": 30})
    records = get_history("alice")
    assert records[0]["filename"] == "second.mp4"


def test_get_history_max_50(tmp_path, monkeypatch):
    import backend.app.history_store as hs
    monkeypatch.setattr(hs, "HISTORY_PATH", str(tmp_path / "big.json"))
    from backend.app.history_store import save_prediction, get_history
    for i in range(60):
        save_prediction("alice", f"v{i}.mp4", {"prediction": "fake", "confidence": 0.9,
            "inference_latency_ms": 10.0, "mlflow_run_id": "r", "frames_analyzed": 30})
    assert len(get_history("alice")) == 50
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "f:/mlops project/deepfake-detection"
pytest tests/unit/test_history_store.py -v 2>&1 | head -30
```
Expected: `ModuleNotFoundError` or `ImportError` — `history_store` doesn't exist yet.

- [ ] **Step 3: Implement `history_store.py`**

```python
# backend/app/history_store.py
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
    with path.open() as f:
        return json.load(f)


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
    """Return the most recent `limit` records for a user, newest first."""
    records = _load()
    user_records = [r for r in records if r["username"] == username]
    user_records.sort(key=lambda r: r["timestamp"], reverse=True)
    return user_records[:limit]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/test_history_store.py -v
```
Expected: 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/app/history_store.py tests/unit/test_history_store.py
git commit -m "feat: add prediction history store (history_store.py)"
```

---

## Task 2: Backend — HistoryRecord Schema + GET /history Endpoint

**Files:**
- Modify: `backend/app/schemas.py` — add `HistoryRecord`
- Modify: `backend/app/routers/predict.py` — call `save_prediction` + add `GET /history`
- Create: `tests/integration/test_history_endpoints.py`

- [ ] **Step 1: Write failing integration tests**

```python
# tests/integration/test_history_endpoints.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np
import torch


@pytest.fixture
def client(tmp_path, monkeypatch):
    import backend.app.history_store as hs
    monkeypatch.setattr(hs, "HISTORY_PATH", str(tmp_path / "history.json"))
    from backend.app.main import app
    return TestClient(app)


def test_get_history_empty(client):
    response = client.get("/history", headers={"X-Username": "alice"})
    assert response.status_code == 200
    assert response.json() == []


def test_get_history_returns_user_records(client, tmp_path, monkeypatch):
    import backend.app.history_store as hs
    monkeypatch.setattr(hs, "HISTORY_PATH", str(tmp_path / "history.json"))
    from backend.app.history_store import save_prediction
    save_prediction("alice", "clip.mp4", {
        "prediction": "fake", "confidence": 0.87,
        "inference_latency_ms": 100.0, "mlflow_run_id": "r1", "frames_analyzed": 30,
    })
    response = client.get("/history", headers={"X-Username": "alice"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["filename"] == "clip.mp4"
    assert data[0]["prediction"] == "fake"


def test_get_history_missing_username_header(client):
    # No X-Username header — should return empty list (anonymous user)
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/integration/test_history_endpoints.py -v 2>&1 | head -30
```
Expected: 404 errors — `/history` route doesn't exist yet.

- [ ] **Step 3: Add `HistoryRecord` to schemas.py**

Open `backend/app/schemas.py` and append at the end:

```python
class HistoryRecord(BaseModel):
    """One entry in a user's prediction history."""
    id: str
    username: str
    filename: str
    prediction: Literal["real", "fake"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    inference_latency_ms: float
    timestamp: str
```

- [ ] **Step 4: Wire `save_prediction` into `predict.py` and add `GET /history`**

At the top of `backend/app/routers/predict.py`, add to the imports block (after the existing `from backend.app.schemas import ...`):

```python
from backend.app.history_store import (
    HISTORY_PATH,  # noqa: F401  imported so tests can monkeypatch it
    save_prediction,
    get_history,
)
from backend.app.schemas import HistoryRecord
from fastapi import Header
```

In the `predict` endpoint handler, after the line `return PredictResponse(...)`, but before the `return` statement itself, insert the `save_prediction` call:

```python
        # ── Save to history ────────────────────────────────────────────────
        x_username = request.headers.get("x-username", "anonymous")
        save_prediction(x_username, file.filename or "upload.mp4", {
            "prediction": prediction,
            "confidence": confidence,
            "inference_latency_ms": infer_ms,
            "mlflow_run_id": model_loader.get_run_id(),
            "frames_analyzed": num_frames,
        })

        return PredictResponse(
```

After all the existing endpoints in `predict.py`, append:

```python
@router.get("/history", response_model=list[HistoryRecord])
def prediction_history(x_username: str = Header(default="anonymous")):
    """Return the calling user's prediction history, newest first (max 50)."""
    return get_history(x_username)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/integration/test_history_endpoints.py -v
```
Expected: 3 tests PASSED.

- [ ] **Step 6: Run full test suite to check for regressions**

```bash
pytest tests/unit/ tests/integration/ -v --tb=short 2>&1 | tail -20
```
Expected: All previously passing tests still pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas.py backend/app/routers/predict.py tests/integration/test_history_endpoints.py
git commit -m "feat: add GET /history endpoint and save predictions to history"
```

---

## Task 3: Frontend — History Page + fetchHistory API

**Files:**
- Modify: `frontend/src/api/client.ts` — add `HistoryRecord` + `fetchHistory`
- Create: `frontend/src/pages/History.tsx`
- Modify: `frontend/src/App.tsx` — add route + nav link
- Modify: `frontend/src/index.css` — add history table styles

- [ ] **Step 1: Add `HistoryRecord` and `fetchHistory` to `client.ts`**

Append to the end of `frontend/src/api/client.ts`:

```typescript
// ─── Prediction History ──────────────────────────────────────────────────────

export interface HistoryRecord {
  id: string;
  username: string;
  filename: string;
  prediction: "real" | "fake";
  confidence: number;
  inference_latency_ms: number;
  timestamp: string;
}

export const fetchHistory = async (username: string): Promise<HistoryRecord[]> => {
  const { data } = await apiClient.get<HistoryRecord[]>("/history", {
    headers: { "X-Username": username },
  });
  return data;
};
```

- [ ] **Step 2: Create `History.tsx`**

```tsx
// frontend/src/pages/History.tsx
import type React from "react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { fetchHistory } from "../api/client";
import type { HistoryRecord } from "../api/client";

export const History: React.FC = () => {
  const { username } = useAuth();
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username) return;
    fetchHistory(username)
      .then(setRecords)
      .catch(() => setError("Failed to load history."))
      .finally(() => setLoading(false));
  }, [username]);

  return (
    <div className="page-wrap">
      <h1 className="page-title">Prediction History</h1>
      <p className="page-sub">Your last 50 analyses, newest first.</p>

      {loading && <p className="history-loading">Loading…</p>}
      {error && <p className="history-error">{error}</p>}

      {!loading && !error && records.length === 0 && (
        <p className="history-empty">No predictions yet. Upload a video to get started.</p>
      )}

      {records.length > 0 && (
        <div className="history-table-wrap">
          <table className="history-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>File</th>
                <th>Verdict</th>
                <th>Confidence</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id}>
                  <td className="history-ts">
                    {new Date(r.timestamp).toLocaleString()}
                  </td>
                  <td className="history-filename">{r.filename}</td>
                  <td>
                    <span className={`history-badge ${r.prediction}`}>
                      {r.prediction === "fake" ? "DEEPFAKE" : "AUTHENTIC"}
                    </span>
                  </td>
                  <td>{Math.round(r.confidence * 100)}%</td>
                  <td>{r.inference_latency_ms.toFixed(0)} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 3: Add route and nav link in `App.tsx`**

Add import at the top of `App.tsx` (with the other page imports):
```tsx
import { History } from "./pages/History";
```

In the `<Routes>` block, after the `/help` route:
```tsx
<Route path="/history" element={<History />} />
```

In the `<div className="nav-links">` block, after the Help link:
```tsx
<Link to="/history" className={`nav-link ${pathname === "/history" ? "active" : ""}`}>History</Link>
```

- [ ] **Step 4: Add history styles to `index.css`**

Append to `frontend/src/index.css`:

```css
/* ── History page ─────────────────────────────────────────────────────────── */
.page-wrap {
  max-width: 900px;
  margin: 0 auto;
  padding: 3rem 1.5rem;
}
.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}
.page-sub {
  color: var(--text-muted);
  margin-bottom: 2rem;
  font-size: 0.9rem;
}
.history-loading,
.history-error,
.history-empty {
  color: var(--text-muted);
  font-size: 0.95rem;
}
.history-error { color: #f87171; }
.history-table-wrap {
  overflow-x: auto;
  border-radius: 10px;
  border: 1px solid var(--border);
}
.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.history-table th {
  text-align: left;
  padding: 0.65rem 1rem;
  background: var(--bg-elevated);
  color: var(--text-muted);
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border);
}
.history-table td {
  padding: 0.7rem 1rem;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}
.history-table tr:last-child td { border-bottom: none; }
.history-table tr:hover td { background: var(--bg-elevated); }
.history-ts { color: var(--text-muted); font-size: 0.8rem; }
.history-filename {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-badge {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}
.history-badge.fake {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}
.history-badge.real {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
}
```

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit 2>&1 | head -30
```
Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/pages/History.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: add prediction history page and fetchHistory API"
```

---

## Task 4: Frontend — Confidence Threshold Slider + Report Download in ResultCard

**Files:**
- Modify: `frontend/src/components/ResultCard.tsx`
- Modify: `frontend/src/index.css` — add slider + download button styles

- [ ] **Step 1: Add threshold slider and download button to `ResultCard.tsx`**

Replace the entire content of `frontend/src/components/ResultCard.tsx` with:

```tsx
import type React from "react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { PredictResponse } from "../api/client";
import { submitFeedback } from "../api/client";

interface Props {
  result: PredictResponse;
  requestId: string;
}

export const ResultCard: React.FC<Props> = ({ result, requestId }) => {
  const pct = Math.round(result.confidence * 100);

  const [threshold, setThreshold] = useState(50);
  const [feedbackSent, setFeedbackSent] = useState(false);

  // Re-evaluate verdict client-side based on threshold
  const effectivePrediction: "real" | "fake" = pct >= threshold ? "fake" : "real";
  const isFake  = effectivePrediction === "fake";
  const cls     = isFake ? "fake" : "real";
  const verdict = isFake ? "DEEPFAKE" : "AUTHENTIC";
  const desc    = isFake
    ? "AI-generated or manipulated content detected in this video."
    : "No manipulation artifacts detected. This video appears authentic.";

  const sendFeedback = async (correct: boolean) => {
    const ground_truth: "real" | "fake" = correct
      ? result.prediction
      : result.prediction === "fake" ? "real" : "fake";
    try {
      await submitFeedback({ request_id: requestId, predicted: result.prediction, ground_truth });
      setFeedbackSent(true);
    } catch { /* silent */ }
  };

  const downloadReport = () => {
    const report = {
      generated_at: new Date().toISOString(),
      filename: "uploaded_video.mp4",
      prediction: effectivePrediction,
      confidence: result.confidence,
      threshold_used: threshold,
      inference_latency_ms: result.inference_latency_ms,
      mlflow_run_id: result.mlflow_run_id,
      frames_analyzed: result.frames_analyzed,
      gradcam_base64: result.gradcam_image,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `deepscan-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AnimatePresence>
      <motion.div
        className="result"
        key={requestId}
        initial={{ scale: 0.92, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.96, opacity: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        {/* Verdict hero */}
        <div className={`result-hero ${cls}`}>
          <p className="result-eyebrow">Analysis Result</p>
          <motion.h2
            className="result-verdict"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ type: "spring", stiffness: 260, damping: 18, delay: 0.1 }}
          >
            {verdict}
          </motion.h2>
          <p className="result-desc">{desc}</p>
        </div>

        {/* Details */}
        <div className={`result-body ${cls}`}>
          {/* Confidence */}
          <div className="conf-row">
            <span className="conf-label">Confidence</span>
            <span className="conf-pct">{pct}%</span>
          </div>
          <div className="conf-track">
            <div className="conf-fill" style={{ width: `${pct}%` }} />
          </div>

          {/* Threshold slider */}
          <div className="threshold-wrap">
            <label className="threshold-label" htmlFor="threshold-slider">
              Threshold: {threshold}%
            </label>
            <input
              id="threshold-slider"
              type="range"
              min={0}
              max={100}
              step={1}
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="threshold-slider"
            />
            <p className="threshold-hint">
              Drag to re-evaluate verdict client-side. Default: 50%.
            </p>
          </div>

          {/* Meta */}
          <div className="meta-grid">
            <div className="meta-cell">
              <span className="meta-cell-label">Frames analyzed</span>
              <span className="meta-cell-value">{result.frames_analyzed}</span>
            </div>
            <div className="meta-cell">
              <span className="meta-cell-label">Inference time</span>
              <span className="meta-cell-value">
                {result.inference_latency_ms.toFixed(0)}
                <span className="meta-cell-unit">ms</span>
              </span>
            </div>
          </div>

          {/* Grad-CAM */}
          {result.gradcam_image && (
            <div className="gradcam-wrap">
              <p className="gradcam-label">Grad-CAM Saliency Map</p>
              <img
                src={`data:image/png;base64,${result.gradcam_image}`}
                alt="Grad-CAM heatmap highlighting manipulated regions"
              />
            </div>
          )}

          {/* Download report */}
          <div className="report-wrap">
            <button type="button" className="btn btn-ghost report-btn" onClick={downloadReport}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              Download Report
            </button>
          </div>

          {/* Feedback */}
          <div className="feedback-wrap">
            {feedbackSent ? (
              <span className="feedback-ok">✓ Feedback recorded — thank you</span>
            ) : (
              <>
                <span className="feedback-q">Was this prediction correct?</span>
                <button type="button" className="btn btn-ghost" onClick={() => sendFeedback(true)}>Yes</button>
                <button type="button" className="btn btn-ghost" onClick={() => sendFeedback(false)}>No</button>
              </>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
```

- [ ] **Step 2: Add threshold slider + report button styles to `index.css`**

Append to `frontend/src/index.css`:

```css
/* ── Threshold slider ─────────────────────────────────────────────────────── */
.threshold-wrap {
  margin: 1.25rem 0;
}
.threshold-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 0.4rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.threshold-slider {
  width: 100%;
  appearance: none;
  height: 4px;
  border-radius: 2px;
  background: var(--border);
  outline: none;
  cursor: pointer;
}
.threshold-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
}
.threshold-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: none;
}
.threshold-hint {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 0.35rem;
}

/* ── Download report button ───────────────────────────────────────────────── */
.report-wrap {
  margin: 1rem 0 0.5rem;
}
.report-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit 2>&1 | head -20
```
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ResultCard.tsx frontend/src/index.css
git commit -m "feat: add confidence threshold slider and report download to ResultCard"
```

---

## Task 5: Frontend — Batch Upload Page

**Files:**
- Create: `frontend/src/pages/Batch.tsx`
- Modify: `frontend/src/App.tsx` — add route + nav link
- Modify: `frontend/src/index.css` — add batch page styles

- [ ] **Step 1: Create `Batch.tsx`**

```tsx
// frontend/src/pages/Batch.tsx
import type React from "react";
import { useRef, useState } from "react";
import { batchPredict } from "../api/client";

interface BatchResult {
  filename: string;
  prediction: "real" | "fake";
  confidence: number;
  inference_latency_ms: number;
  error: string;
}

export const Batch: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<BatchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<{ total: number; succeeded: number } | null>(null);

  const handleFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(Array.from(e.target.files ?? []));
    setResults(null);
    setSummary(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) return;
    setLoading(true);
    try {
      const resp = await batchPredict(files);
      setResults(resp.results);
      setSummary({ total: resp.total, succeeded: resp.succeeded });
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-wrap">
      <h1 className="page-title">Batch Upload</h1>
      <p className="page-sub">Upload up to 10 MP4 files at once. Each is analyzed independently.</p>

      <form onSubmit={handleSubmit} className="batch-form">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".mp4"
          onChange={handleFiles}
          className="batch-file-input"
          id="batch-file"
        />
        <label htmlFor="batch-file" className="batch-file-label">
          {files.length > 0
            ? `${files.length} file${files.length > 1 ? "s" : ""} selected`
            : "Choose MP4 files…"}
        </label>
        <button
          type="submit"
          className="btn batch-submit-btn"
          disabled={files.length === 0 || loading}
        >
          {loading ? "Analyzing…" : "Analyze All"}
        </button>
      </form>

      {summary && (
        <div className="batch-summary">
          {summary.succeeded} of {summary.total} succeeded
        </div>
      )}

      {results && results.length > 0 && (
        <div className="history-table-wrap" style={{ marginTop: "1.5rem" }}>
          <table className="history-table">
            <thead>
              <tr>
                <th>File</th>
                <th>Verdict</th>
                <th>Confidence</th>
                <th>Latency</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i}>
                  <td className="history-filename">{r.filename}</td>
                  <td>
                    {r.error ? (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    ) : (
                      <span className={`history-badge ${r.prediction}`}>
                        {r.prediction === "fake" ? "DEEPFAKE" : "AUTHENTIC"}
                      </span>
                    )}
                  </td>
                  <td>{r.error ? "—" : `${Math.round(r.confidence * 100)}%`}</td>
                  <td>{r.error ? "—" : `${r.inference_latency_ms.toFixed(0)} ms`}</td>
                  <td style={{ color: "#f87171", fontSize: "0.78rem" }}>{r.error || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 2: Add route and nav link in `App.tsx`**

Add import:
```tsx
import { Batch } from "./pages/Batch";
```

In `<Routes>`:
```tsx
<Route path="/batch" element={<Batch />} />
```

In nav links (after History link):
```tsx
<Link to="/batch" className={`nav-link ${pathname === "/batch" ? "active" : ""}`}>Batch</Link>
```

- [ ] **Step 3: Add batch form styles to `index.css`**

Append to `frontend/src/index.css`:

```css
/* ── Batch upload ─────────────────────────────────────────────────────────── */
.batch-form {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}
.batch-file-input {
  display: none;
}
.batch-file-label {
  display: inline-flex;
  align-items: center;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  border: 1px dashed var(--border);
  background: var(--bg-elevated);
  color: var(--text-muted);
  font-size: 0.875rem;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}
.batch-file-label:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}
.batch-submit-btn {
  padding: 0.55rem 1.25rem;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: opacity 0.2s;
}
.batch-submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.batch-summary {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 0.5rem;
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit 2>&1 | head -20
```
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Batch.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: add batch upload page"
```

---

## Task 6: Frontend — Model Card Page

**Files:**
- Create: `frontend/src/pages/ModelCard.tsx`
- Modify: `frontend/src/App.tsx` — add route + nav link
- Modify: `frontend/src/index.css` — add model card styles

- [ ] **Step 1: Create `ModelCard.tsx`**

```tsx
// frontend/src/pages/ModelCard.tsx
import type React from "react";

export const ModelCard: React.FC = () => (
  <div className="page-wrap">
    <h1 className="page-title">Model Card</h1>
    <p className="page-sub">Transparency documentation for the DeepScan CNN+LSTM deepfake detector.</p>

    {/* Model Details */}
    <section className="mc-section">
      <h2 className="mc-heading">Model Details</h2>
      <table className="mc-table">
        <tbody>
          <tr><th>Model name</th><td>DeepScan CNN+LSTM</td></tr>
          <tr><th>Version</th><td>1.0 (MLflow registry)</td></tr>
          <tr><th>Input</th><td>MP4 video, up to 100 MB</td></tr>
          <tr><th>Output</th><td>real / fake + confidence score (0–100%)</td></tr>
          <tr><th>Inference latency</th><td>P95 &lt; 200 ms (CPU)</td></tr>
          <tr><th>Explainability</th><td>Grad-CAM saliency map per prediction</td></tr>
        </tbody>
      </table>
    </section>

    {/* Architecture */}
    <section className="mc-section">
      <h2 className="mc-heading">Architecture</h2>
      <p className="mc-text">
        The model uses a two-stage pipeline. <strong>EfficientNet-B0</strong> (pretrained on ImageNet)
        extracts a 1280-dimensional feature vector from each sampled frame. A single-layer
        <strong> LSTM</strong> (hidden size 256) then processes the sequence of frame features to capture
        temporal manipulation artifacts. A final linear layer produces a scalar probability in [0, 1];
        values ≥ 0.5 are classified as <em>fake</em>.
      </p>
    </section>

    {/* Training Data */}
    <section className="mc-section">
      <h2 className="mc-heading">Training Data</h2>
      <p className="mc-text">
        Trained on the <strong>SDFVD (Synthetic Deepfake Video Dataset)</strong>. The dataset contains
        an equal split of authentic and AI-generated videos. Face detection (MTCNN) is applied to
        each frame before feature extraction. Training used an 80/10/10 train/val/test split.
      </p>
    </section>

    {/* Intended Use */}
    <section className="mc-section">
      <h2 className="mc-heading">Intended Use</h2>
      <p className="mc-text">
        DeepScan is designed for research and demonstration purposes — to illustrate how a deepfake
        detector can be built, deployed, and monitored end-to-end using MLOps practices. It is
        <strong> not</strong> intended for high-stakes production decisions without human review.
      </p>
    </section>

    {/* Limitations */}
    <section className="mc-section">
      <h2 className="mc-heading">Limitations</h2>
      <ul className="mc-list">
        <li>Performance may degrade on deepfakes generated by unseen techniques not in training data.</li>
        <li>Videos without detectable faces fall back to a center-crop — confidence may be lower.</li>
        <li>Model is CPU-only in the current deployment; inference may be slower on long videos.</li>
        <li>Confidence near 50% indicates ambiguous content — treat results with caution.</li>
      </ul>
    </section>

    {/* Evaluation Metrics */}
    <section className="mc-section">
      <h2 className="mc-heading">Evaluation Metrics</h2>
      <table className="mc-table">
        <tbody>
          <tr><th>Val Accuracy</th><td>100% (MLflow run 0215feaa)</td></tr>
          <tr><th>Val F1-score</th><td>1.0</td></tr>
          <tr><th>Best epoch</th><td>11</td></tr>
          <tr><th>P95 latency</th><td>&lt; 200 ms</td></tr>
        </tbody>
      </table>
    </section>

    {/* Responsible AI */}
    <section className="mc-section mc-notice">
      <h2 className="mc-heading">Responsible AI Notice</h2>
      <p className="mc-text">
        Deepfake detection is an adversarial problem — attackers can adapt to evade any detector.
        Results should always be treated as probabilistic indicators, not ground truth.
        Incorrect predictions (false positives and false negatives) are expected.
        Always apply human judgement and do not make consequential decisions based solely on this tool.
      </p>
    </section>
  </div>
);
```

- [ ] **Step 2: Add route and nav link in `App.tsx`**

Add import:
```tsx
import { ModelCard } from "./pages/ModelCard";
```

In `<Routes>`:
```tsx
<Route path="/model" element={<ModelCard />} />
```

In nav links (after Batch link):
```tsx
<Link to="/model" className={`nav-link ${pathname === "/model" ? "active" : ""}`}>Model</Link>
```

- [ ] **Step 3: Add model card styles to `index.css`**

Append to `frontend/src/index.css`:

```css
/* ── Model card page ──────────────────────────────────────────────────────── */
.mc-section {
  margin-bottom: 2.25rem;
}
.mc-heading {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.75rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--border);
}
.mc-text {
  color: var(--text-muted);
  line-height: 1.7;
  font-size: 0.9rem;
}
.mc-list {
  color: var(--text-muted);
  font-size: 0.9rem;
  line-height: 1.8;
  padding-left: 1.25rem;
}
.mc-table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.875rem;
}
.mc-table th {
  text-align: left;
  padding: 0.45rem 0.75rem 0.45rem 0;
  color: var(--text-muted);
  font-weight: 600;
  width: 200px;
  vertical-align: top;
}
.mc-table td {
  padding: 0.45rem 0;
  color: var(--text-primary);
}
.mc-notice {
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
}
.mc-notice .mc-heading { border-color: rgba(239, 68, 68, 0.3); }
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit 2>&1 | head -20
```
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ModelCard.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: add model card page"
```

---

## Task 7: Frontend — Pipeline Status Bar

**Files:**
- Create: `frontend/src/components/PipelineStatusBar.tsx`
- Modify: `frontend/src/pages/Home.tsx` — render `PipelineStatusBar` below nav
- Modify: `frontend/src/index.css` — add status bar styles

- [ ] **Step 1: Create `PipelineStatusBar.tsx`**

```tsx
// frontend/src/components/PipelineStatusBar.tsx
import type React from "react";
import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

interface StatusPill {
  label: string;
  value: string;
  ok: boolean;
}

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 2) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export const PipelineStatusBar: React.FC = () => {
  const [pills, setPills] = useState<StatusPill[] | null>(null);

  const load = () => {
    Promise.all([
      apiClient.get("/pipeline/airflow-runs").catch(() => null),
      apiClient.get("/pipeline/mlflow-runs").catch(() => null),
    ]).then(([airflowRes, mlflowRes]) => {
      if (!airflowRes && !mlflowRes) {
        setPills(null); // hide bar silently
        return;
      }

      const newPills: StatusPill[] = [];

      if (airflowRes?.data) {
        const runs: Array<{ state: string; execution_date: string }> = airflowRes.data.dag_runs ?? [];
        const latest = runs[0];
        newPills.push({
          label: "Pipeline",
          value: latest ? `${latest.state} · ${timeAgo(latest.execution_date)}` : "no runs",
          ok: latest?.state === "success",
        });
      }

      if (mlflowRes?.data) {
        const runs: Array<{ run_id: string; metrics?: { val_f1?: number } }> = mlflowRes.data.runs ?? [];
        const latest = runs[0];
        const f1 = latest?.metrics?.val_f1;
        newPills.push({
          label: "Model",
          value: latest ? `run ${latest.run_id.slice(0, 6)} · F1 ${f1 !== undefined ? f1.toFixed(2) : "n/a"}` : "no runs",
          ok: true,
        });
      }

      newPills.push({ label: "System", value: "Online", ok: true });
      setPills(newPills);
    });
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 60_000);
    return () => clearInterval(interval);
  }, []);

  if (!pills) return null;

  return (
    <div className="pipeline-status-bar">
      {pills.map((pill) => (
        <div key={pill.label} className={`psb-pill ${pill.ok ? "ok" : "warn"}`}>
          <span className="psb-dot" />
          <span className="psb-label">{pill.label}</span>
          <span className="psb-value">{pill.value}</span>
        </div>
      ))}
    </div>
  );
};
```

- [ ] **Step 2: Add `PipelineStatusBar` to `Home.tsx`**

Add import at top of `Home.tsx`:
```tsx
import { PipelineStatusBar } from "../components/PipelineStatusBar";
```

In the JSX, just before `{/* ── Hero ── */}`, insert:
```tsx
<PipelineStatusBar />
```

- [ ] **Step 3: Add status bar styles to `index.css`**

Append to `frontend/src/index.css`:

```css
/* ── Pipeline status bar ──────────────────────────────────────────────────── */
.pipeline-status-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.5rem;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.psb-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 500;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
}
.psb-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.psb-pill.ok .psb-dot  { background: #34d399; }
.psb-pill.warn .psb-dot { background: #f59e0b; }
.psb-label {
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.psb-value { color: var(--text-primary); }
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit 2>&1 | head -20
```
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/PipelineStatusBar.tsx frontend/src/pages/Home.tsx frontend/src/index.css
git commit -m "feat: add pipeline status bar to Home page"
```

---

## Task 8: Frontend — Dark/Light Mode Toggle

**Files:**
- Modify: `frontend/src/App.tsx` — add toggle button to Nav
- Modify: `frontend/src/main.tsx` — restore theme preference on load
- Modify: `frontend/src/index.css` — add `[data-theme="light"]` override block + toggle button styles

- [ ] **Step 1: Add theme restore to `main.tsx`**

Replace the entire content of `frontend/src/main.tsx` with:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Restore theme preference before first render to avoid flash
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') {
  document.documentElement.setAttribute('data-theme', 'light');
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 2: Add toggle button to Nav in `App.tsx`**

In the `Nav` function, add a `theme` state just before the `return`:

```tsx
  const [theme, setTheme] = React.useState<"dark" | "light">(
    document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark"
  );

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    if (next === "light") {
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("theme", "dark");
    }
  };
```

Also add `import React from "react";` at the top if not already present — the file currently uses `import type React from "react"`, so change it to `import React from "react"`.

In the Nav JSX, inside `<div className="nav-actions">`, before the sign-out button:

```tsx
          <button
            type="button"
            className="nav-theme-toggle"
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              /* Sun icon */
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              /* Moon icon */
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
              </svg>
            )}
          </button>
```

- [ ] **Step 3: Add light theme override block and toggle button styles to `index.css`**

Append to `frontend/src/index.css`:

```css
/* ── Light theme override ─────────────────────────────────────────────────── */
[data-theme="light"] {
  --bg:          #f8f9fa;
  --bg-elevated: #ffffff;
  --bg-card:     #ffffff;
  --border:      #e2e6ea;
  --text-primary: #111827;
  --text-muted:  #6b7280;
  --text-faint:  #9ca3af;
}
[data-theme="light"] .nav {
  background: rgba(255,255,255,0.85);
  border-color: #e2e6ea;
}
[data-theme="light"] .hero-wrap,
[data-theme="light"] .hero-bg { background: #f0f2f5; }
[data-theme="light"] .hero-title { color: #111827; }
[data-theme="light"] .hero-eyebrow { color: #6b7280; }

/* ── Nav theme toggle button ──────────────────────────────────────────────── */
.nav-theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}
.nav-theme-toggle:hover {
  color: var(--text-primary);
  border-color: var(--accent);
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit 2>&1 | head -20
```
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/main.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: add dark/light mode toggle with localStorage persistence"
```

---

## Task 9: Frontend — Simulated Progress Bar

**Files:**
- Create: `frontend/src/components/ProgressBar.tsx`
- Modify: `frontend/src/pages/Home.tsx` — replace spinner with `ProgressBar`
- Modify: `frontend/src/index.css` — add progress bar styles

- [ ] **Step 1: Create `ProgressBar.tsx`**

```tsx
// frontend/src/components/ProgressBar.tsx
import type React from "react";
import { useEffect, useRef, useState } from "react";

interface Props {
  loading: boolean;
  error: string | null;
}

const STAGES = [
  { label: "Extracting frames…",   target: 25,  duration: 800  },
  { label: "Detecting faces…",     target: 55,  duration: 1200 },
  { label: "Running model…",       target: 85,  duration: 1500 },
  { label: "Finalizing…",          target: 99,  duration: 99999 }, // holds until done
];

export const ProgressBar: React.FC<Props> = ({ loading, error }) => {
  const [progress, setProgress] = useState(0);
  const [stageIdx, setStageIdx] = useState(0);
  const [done, setDone] = useState(false);
  const [visible, setVisible] = useState(false);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = () => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  };

  useEffect(() => {
    if (loading) {
      // Reset and start
      setProgress(0);
      setStageIdx(0);
      setDone(false);
      setVisible(true);

      let cumDelay = 0;
      STAGES.forEach((stage, idx) => {
        const t = setTimeout(() => {
          setStageIdx(idx);
          // Animate progress to stage target over the stage duration
          const steps = 20;
          const stepInterval = Math.min(stage.duration / steps, 50);
          const startPct = idx === 0 ? 0 : STAGES[idx - 1].target;
          const delta = stage.target - startPct;
          for (let s = 1; s <= steps; s++) {
            const st = setTimeout(() => {
              setProgress(startPct + Math.round((delta * s) / steps));
            }, s * stepInterval);
            timersRef.current.push(st);
          }
        }, cumDelay);
        timersRef.current.push(t);
        if (idx < STAGES.length - 1) cumDelay += stage.duration;
      });
    } else {
      // API responded — finish or show error
      clearTimers();
      if (visible) {
        if (error) {
          // Keep at current progress, mark done so CSS turns red
          setDone(true);
        } else {
          setProgress(100);
          setDone(true);
          const t = setTimeout(() => setVisible(false), 600);
          timersRef.current.push(t);
        }
      }
    }
    return clearTimers;
  }, [loading]);

  if (!visible) return null;

  return (
    <div className={`progress-wrap ${done && error ? "progress-error" : ""}`}>
      <div className="progress-track">
        <div
          className={`progress-fill ${done && !error ? "progress-complete" : ""}`}
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="progress-label">
        {error && done
          ? error
          : STAGES[stageIdx]?.label}
      </p>
    </div>
  );
};
```

- [ ] **Step 2: Replace spinner in `Home.tsx` with `ProgressBar`**

Add import at top of `Home.tsx`:
```tsx
import { ProgressBar } from "../components/ProgressBar";
```

Replace the existing spinner block:
```tsx
        {loading && (
          <div className="analyzing-card">
            <div className="analyzing-spinner" />
            <div>
              <p className="analyzing-title">Analyzing video…</p>
              <p className="analyzing-sub">EXTRACTING FRAMES · RUNNING INFERENCE</p>
            </div>
          </div>
        )}
```

With:
```tsx
        <ProgressBar loading={loading} error={error} />
```

- [ ] **Step 3: Add progress bar styles to `index.css`**

Append to `frontend/src/index.css`:

```css
/* ── Simulated progress bar ───────────────────────────────────────────────── */
.progress-wrap {
  margin: 1.5rem auto;
  max-width: 560px;
  width: 100%;
}
.progress-track {
  width: 100%;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: width 0.25s ease;
}
.progress-fill.progress-complete {
  background: #34d399;
  transition: width 0.15s ease;
}
.progress-error .progress-fill {
  background: #f87171;
}
.progress-label {
  margin-top: 0.5rem;
  font-size: 0.78rem;
  color: var(--text-muted);
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.progress-error .progress-label {
  color: #f87171;
  text-transform: none;
  letter-spacing: 0;
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit 2>&1 | head -20
```
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ProgressBar.tsx frontend/src/pages/Home.tsx frontend/src/index.css
git commit -m "feat: replace spinner with simulated progress bar"
```

---

## Task 10: Frontend — Onboarding Tooltip Tour

**Files:**
- Create: `frontend/src/components/OnboardingTour.tsx`
- Modify: `frontend/src/pages/Home.tsx` — render `OnboardingTour`; add `id` attributes to target elements
- Modify: `frontend/src/index.css` — add tooltip styles

- [ ] **Step 1: Create `OnboardingTour.tsx`**

```tsx
// frontend/src/components/OnboardingTour.tsx
import type React from "react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";

const STEPS = [
  {
    targetId: "upload-area",
    title: "Upload your video",
    body: "Drop your MP4 here to start. Files up to 100 MB are accepted.",
  },
  {
    targetId: "result-card-anchor",
    title: "Your verdict",
    body: "Your verdict and confidence score appear here after analysis completes.",
  },
  {
    targetId: "gradcam-anchor",
    title: "Grad-CAM heatmap",
    body: "Highlighted regions show which parts of the frame influenced the prediction most.",
  },
  {
    targetId: "help-nav-link",
    title: "Need help?",
    body: "Visit the Help page for FAQs, the chatbot, and support ticket submission.",
  },
];

function getAnchorRect(id: string): DOMRect | null {
  const el = document.getElementById(id);
  return el ? el.getBoundingClientRect() : null;
}

export const OnboardingTour: React.FC = () => {
  const { role } = useAuth();
  const [step, setStep] = useState(0);
  const [visible, setVisible] = useState(false);
  const [rect, setRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    if (role === "admin") return; // admins skip the tour
    if (localStorage.getItem("tour_done")) return;
    // Small delay so DOM is painted
    const t = setTimeout(() => setVisible(true), 800);
    return () => clearTimeout(t);
  }, [role]);

  useEffect(() => {
    if (!visible) return;
    const r = getAnchorRect(STEPS[step].targetId);
    setRect(r);
  }, [visible, step]);

  if (!visible || !rect) return null;

  const dismiss = () => {
    setVisible(false);
    localStorage.setItem("tour_done", "1");
  };

  const next = () => {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      dismiss();
    }
  };

  const top = window.scrollY + rect.bottom + 12;
  const left = Math.min(rect.left, window.innerWidth - 300);

  return (
    <div
      className="tour-tooltip"
      style={{ top, left }}
    >
      <div className="tour-arrow" />
      <p className="tour-step">{step + 1} / {STEPS.length}</p>
      <p className="tour-title">{STEPS[step].title}</p>
      <p className="tour-body">{STEPS[step].body}</p>
      <div className="tour-actions">
        <button type="button" className="tour-skip" onClick={dismiss}>Skip Tour</button>
        <button type="button" className="btn tour-next" onClick={next}>
          {step < STEPS.length - 1 ? "Next" : "Done"}
        </button>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Add anchor IDs and render `OnboardingTour` in `Home.tsx`**

Add import:
```tsx
import { OnboardingTour } from "../components/OnboardingTour";
```

In the JSX, add `id="upload-area"` to the `<VideoUpload>` wrapper div:

Change:
```tsx
      <div className="analyze-section" ref={uploadRef}>
```
To:
```tsx
      <div className="analyze-section" id="upload-area" ref={uploadRef}>
```

After `{result && <ResultCard ... />}`, add:
```tsx
        <div id="result-card-anchor" />
        <div id="gradcam-anchor" />
```

At the end of the JSX (before the closing fragment `</>`), add:
```tsx
      <OnboardingTour />
```

In `App.tsx`'s `Nav`, add `id="help-nav-link"` to the Help `<Link>`:
```tsx
<Link id="help-nav-link" to="/help" className={...}>Help</Link>
```

- [ ] **Step 3: Add tooltip styles to `index.css`**

Append to `frontend/src/index.css`:

```css
/* ── Onboarding tooltip tour ──────────────────────────────────────────────── */
.tour-tooltip {
  position: absolute;
  z-index: 9999;
  width: 280px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem 1.1rem;
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
}
.tour-arrow {
  position: absolute;
  top: -6px;
  left: 20px;
  width: 10px;
  height: 10px;
  background: var(--bg-elevated);
  border-left: 1px solid var(--border);
  border-top: 1px solid var(--border);
  transform: rotate(45deg);
}
.tour-step {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.3rem;
}
.tour-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.35rem;
}
.tour-body {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.55;
  margin-bottom: 0.75rem;
}
.tour-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.tour-skip {
  font-size: 0.78rem;
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.tour-skip:hover { color: var(--text-primary); }
.tour-next {
  padding: 0.35rem 0.85rem;
  font-size: 0.8rem;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit 2>&1 | head -20
```
Expected: No errors.

- [ ] **Step 5: Run all backend tests to confirm no regressions**

```bash
cd "f:/mlops project/deepfake-detection"
pytest tests/unit/ tests/integration/ -v --tb=short 2>&1 | tail -15
```
Expected: All previously passing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/OnboardingTour.tsx frontend/src/pages/Home.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: add onboarding tooltip tour for first-time users"
```

---

## Self-Review

**Spec coverage:**
- Feature 1 (History backend): Tasks 1 + 2 — store, schema, endpoint, predict integration ✅
- Feature 2 (Threshold slider): Task 4 — slider + client-side re-evaluation ✅
- Feature 3 (Model card): Task 6 — hardcoded JSX sections ✅
- Feature 4 (Batch upload UI): Task 5 — multi-file picker + results table ✅
- Feature 5 (Pipeline status widget): Task 7 — PipelineStatusBar with 60s refresh ✅
- Feature 6 (Exportable report): Task 4 — download button in ResultCard ✅
- Feature 7 (Dark/light mode): Task 8 — CSS variable override + localStorage ✅
- Feature 8 (Onboarding tour): Task 10 — 4-step tooltip with skip + localStorage flag ✅
- Feature 9 (Progress bar): Task 9 — multi-stage timer + error state ✅

**Type consistency:**
- `HistoryRecord` defined in `schemas.py` (Task 2) and mirrored in `client.ts` (Task 3) — field names match ✅
- `save_prediction` called in `predict.py` with keys matching `history_store.py`'s `result_dict.get(...)` keys ✅
- `PipelineStatusBar` receives no props — self-contained ✅
- `ProgressBar` receives `{ loading: boolean; error: string | null }` — matches `Home.tsx` state ✅
- `OnboardingTour` receives no props — reads auth from context ✅

**No placeholders:** All tasks contain complete code. No TBD/TODO. ✅
