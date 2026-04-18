# Value Additions — Design Spec

**Date:** 2026-04-16
**Project:** DeepScan Deepfake Detection App
**Scope:** 9 independent UI/UX and feature additions

---

## Overview

Nine additions are grouped into three implementation tiers based on where they live:

| # | Feature | Tier | Backend? |
|---|---|---|---|
| 1 | Prediction history | Backend + Frontend | ✅ new endpoint + JSON store |
| 2 | Confidence threshold slider | Frontend only | ❌ |
| 3 | Model card page | Frontend only | ❌ |
| 4 | Batch upload UI | Frontend only | ❌ (endpoint exists) |
| 5 | Pipeline status widget | Frontend only | ❌ (endpoints exist) |
| 6 | Exportable report | Frontend only | ❌ |
| 7 | Dark/light mode toggle | Frontend only | ❌ |
| 8 | Onboarding tooltip tour | Frontend only | ❌ |
| 9 | Simulated progress bar | Frontend only | ❌ |

All frontend work follows the existing patterns: CSS variables in `index.css`, components in `frontend/src/components/`, pages in `frontend/src/pages/`, API calls in `frontend/src/api/client.ts`. No new npm packages.

---

## Feature 1: Prediction History

### Backend
- New file: `backend/app/history_store.py` — same pattern as `ticket_store.py`. Reads/writes `data/history.json`.
- Each record: `{ id, username, filename, prediction, confidence, inference_latency_ms, timestamp }`.
- Functions: `save_prediction(username, filename, result_dict) -> dict`, `get_history(username) -> list[dict]`.
- New endpoint `GET /history` on `predict` router — reads `X-Username` header, returns that user's records newest-first (max 50).
- The existing `POST /predict` handler calls `save_prediction(...)` after a successful inference.

### Frontend
- New page `frontend/src/pages/History.tsx` — table of past analyses: timestamp, filename, prediction badge (real/fake coloured), confidence %, latency. Newest first.
- Nav link "History" visible to all logged-in users.
- Route `/history`.
- API call `fetchHistory(username): Promise<HistoryRecord[]>` in `client.ts`.

---

## Feature 2: Confidence Threshold Slider

### Frontend only
- A range slider (`<input type="range" min="0" max="100" step="1" />`) rendered in `ResultCard.tsx` below the confidence score, defaulting to 50.
- When the user drags the slider, the displayed verdict label ("DEEPFAKE" / "AUTHENTIC") re-evaluates client-side: `prediction = confidence >= threshold ? "fake" : "real"`.
- The slider value is shown as a label: "Threshold: 62%".
- No API call — purely re-renders the existing result in-place.
- Slider state is local to `ResultCard` — resets to 50 on each new prediction.

---

## Feature 3: Model Card Page

### Frontend only
- New page `frontend/src/pages/ModelCard.tsx`.
- Renders the content of `docs/MODEL_CARD.md` as structured HTML sections (not a raw markdown renderer — hardcoded JSX sections to avoid a new dep).
- Sections: Model Details table, Architecture, Training Data, Intended Use, Limitations, Evaluation Metrics, Responsible AI notice.
- Nav link "Model" visible to all logged-in users.
- Route `/model`.

---

## Feature 4: Batch Upload UI

### Frontend only
- New page `frontend/src/pages/Batch.tsx`.
- Multi-file picker (`<input type="file" multiple accept=".mp4" />`).
- On submit calls existing `batchPredict(files)` from `client.ts`.
- Results rendered as a table: filename, prediction badge, confidence %, latency, error column (if any).
- Summary row at top: "X of Y succeeded".
- Nav link "Batch" visible to all logged-in users.
- Route `/batch`.

---

## Feature 5: Pipeline Status Widget

### Frontend only
- New component `frontend/src/components/PipelineStatusBar.tsx` — a compact bar rendered at the top of the Home page (below the nav, above the hero).
- Calls existing `GET /pipeline/airflow-runs` and `GET /pipeline/mlflow-runs` on mount.
- Shows three pills: **Pipeline** (last Airflow run status + time ago), **Model** (latest MLflow run version + F1), **System** (always "Online" if the fetch succeeded).
- If the backend is unreachable, the bar is hidden silently (no error shown to users).
- Auto-refreshes every 60 seconds.

---

## Feature 6: Exportable Report

### Frontend only
- A "Download Report" button added to `ResultCard.tsx`, visible after a successful prediction.
- Clicking it generates and downloads a JSON file: `deepscan-report-<timestamp>.json`.
- Report contents: `{ generated_at, filename, prediction, confidence, threshold_used, inference_latency_ms, mlflow_run_id, frames_analyzed }`.
- The Grad-CAM image (base64) is included as `gradcam_base64` field.
- Implemented with a vanilla `URL.createObjectURL(new Blob([JSON.stringify(report)]))` — no new deps.

---

## Feature 7: Dark / Light Mode Toggle

### Frontend only
- A toggle button in the `Nav` component (sun/moon SVG icon).
- On click, adds/removes a `data-theme="light"` attribute on `<html>`.
- A `[data-theme="light"]` block in `index.css` overrides the CSS variables to light equivalents (white/grey backgrounds, dark text, same accent green).
- Preference saved to `localStorage` key `"theme"` and restored on page load via a one-liner in `main.tsx`.
- No new state management — a simple DOM attribute + CSS handles everything.

---

## Feature 8: Onboarding Tooltip Tour

### Frontend only
- New component `frontend/src/components/OnboardingTour.tsx`.
- Shows a 4-step tooltip sequence on first login (tracked via `localStorage` key `"tour_done"`):
  1. Upload area — "Drop your MP4 here to start"
  2. Result card (after first result) — "Your verdict and confidence score appear here"
  3. Grad-CAM heatmap — "Highlighted regions influenced the prediction"
  4. Help link — "Visit Help for FAQs and support"
- Each tooltip: a small floating card with an arrow, "Next" / "Skip Tour" buttons.
- Tour only runs once per browser. Admin users skip it entirely.
- Rendered inside `Home.tsx` — no router changes needed.
- Pure CSS positioning (absolute/fixed) — no tooltip library dep.

---

## Feature 9: Simulated Progress Bar

### Frontend only
- Replaces the current spinner in `Home.tsx` during loading.
- A full-width progress bar with step labels that cycles through 4 stages on a timer while the API call is in-flight:
  1. `Extracting frames…` — 0–25% (0.8s)
  2. `Detecting faces…` — 25–55% (1.2s)
  3. `Running model…` — 55–85% (1.5s)
  4. `Finalizing…` — 85–99% (holds until API responds)
- When the API responds, bar jumps to 100% then fades out.
- If the API errors, bar turns red and shows the error message.
- Implemented in a new component `frontend/src/components/ProgressBar.tsx`.
- `Home.tsx` passes `loading` boolean to it; the timer logic lives entirely inside `ProgressBar`.

---

## Architecture & Patterns

### CSS
All new styles appended to `index.css` using existing CSS variables. No new stylesheets.

### Routing
New pages added to `App.tsx` following the existing `<Route>` pattern. All new routes accessible to all authenticated users (no new `AdminRoute` wrappers needed).

### No new npm packages
Every feature is implemented with vanilla React hooks, DOM APIs, and existing deps (`axios`, `framer-motion` already installed).

### Backend pattern
Feature 1 backend follows exactly the `ticket_store.py` pattern — a module-level `HISTORY_PATH` constant, pure functions, monkeypatchable in tests.

---

## File Map

### New backend files
- `backend/app/history_store.py`
- `tests/unit/test_history_store.py`
- `tests/integration/test_history_endpoints.py`

### Modified backend files
- `backend/app/routers/predict.py` — call `save_prediction` after successful inference; add `GET /history` endpoint
- `backend/app/schemas.py` — add `HistoryRecord` schema

### New frontend files
- `frontend/src/pages/History.tsx`
- `frontend/src/pages/Batch.tsx`
- `frontend/src/pages/ModelCard.tsx`
- `frontend/src/components/PipelineStatusBar.tsx`
- `frontend/src/components/ProgressBar.tsx`
- `frontend/src/components/OnboardingTour.tsx`

### Modified frontend files
- `frontend/src/App.tsx` — add routes `/history`, `/batch`, `/model`; nav links
- `frontend/src/api/client.ts` — add `fetchHistory`
- `frontend/src/components/ResultCard.tsx` — add threshold slider + download button
- `frontend/src/pages/Home.tsx` — add `PipelineStatusBar`, replace spinner with `ProgressBar`, add `OnboardingTour`
- `frontend/src/index.css` — all new styles + light theme override block
- `frontend/src/main.tsx` — theme preference restore on load

---

## Testing

### Backend (TDD)
- `test_history_store.py` — unit tests: save record, get records, per-user filtering, max-50 cap
- `test_history_endpoints.py` — integration: `GET /history` returns correct records per user; predict endpoint saves to history

### Frontend
- TypeScript compilation (`npx tsc --noEmit`) verifies no type errors
- No UI unit tests (consistent with existing project — no Vitest/RTL setup)

---

## Spec Self-Review

**Placeholder scan:** No TBD or TODO sections. All features fully specified.

**Internal consistency:**
- Feature 1 backend uses `X-Username` header — consistent with support tickets pattern. ✅
- Feature 2 slider uses existing `result.confidence` from `PredictResponse` — no new API field needed. ✅
- Feature 5 widget uses existing `/pipeline/*` endpoints — no new backend work. ✅
- Feature 9 progress bar replaces the `loading` spinner in `Home.tsx` — the `loading` state already exists. ✅

**Scope:** 9 features but most are frontend-only and small. Backend work is only Feature 1. Each feature is independent — they can be implemented and reviewed one at a time.

**Ambiguity resolved:**
- History storage: backend JSON (not localStorage)
- Progress bar: simulated steps (not real polling)
- Model card: hardcoded JSX (not markdown renderer)
- Light mode: CSS variable override via `data-theme` attribute (not a full CSS-in-JS solution)
