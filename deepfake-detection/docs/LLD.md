# Low-Level Design — Deepfake Detection System

**Version:** 1.1
**Date:** 2026-04-07

---

## 1. API Endpoint Specifications

### POST /predict

**Request:** `multipart/form-data`
- `file`: MP4 video file (max 100MB)

**Validation:** File must have `.mp4` extension — returns HTTP 400 otherwise.

**Response (HTTP 200):**
```json
{
  "prediction": "fake",
  "confidence": 0.94,
  "inference_latency_ms": 143.2,
  "gradcam_image": "<base64 PNG string>",
  "mlflow_run_id": "uuid-string",
  "frames_analyzed": 30
}
```

**Response (HTTP 400):** `{"detail": "Only MP4 files are accepted"}`
**Response (HTTP 500):** `{"detail": "<error message>"}`

**Data flow:**
1. Save upload to temp file
2. `preprocess_video(tmp_path)` → tensor `(30, 3, 224, 224)`
3. `model.predict(tensor.unsqueeze(0).numpy())` → confidence float
4. `prediction = "fake" if confidence >= 0.5 else "real"`
5. Feature drift check via `compute_drift_score(features, baseline)`
6. `generate_gradcam(model, frames_tensor)` → base64 PNG (best-effort)
7. Update Prometheus metrics

---

### GET /health

**Response (HTTP 200):**
```json
{"status": "ok", "model_loaded": true}
```

---

### GET /ready

**Response (HTTP 200):**
```json
{"status": "ready", "model_version": "deepfake/Production/3"}
```

**Response (HTTP 503):** `{"detail": "Model not loaded"}` — when model is not loaded.

---

### GET /metrics

**Response:** Prometheus text exposition format (HTTP 200, `text/plain`)

Metrics exposed:
| Metric | Type | Labels | Description |
|---|---|---|---|
| `deepfake_requests_total` | Counter | method, endpoint, status | Total prediction requests |
| `deepfake_request_latency_seconds` | Histogram | endpoint | End-to-end request latency |
| `deepfake_inference_latency_ms` | Histogram | — | Model inference time |
| `deepfake_confidence_score` | Histogram | — | Confidence distribution |
| `deepfake_predictions_total` | Counter | label | Predictions by real/fake label |
| `deepfake_drift_score` | Gauge | — | Current feature drift z-score |
| `deepfake_drift_detected_total` | Counter | — | Requests with drift detected |
| `pipeline_validation_failures_total` | Counter | — | Schema validation failures |

---

### POST /admin/reload-model

**Auth:** Internal only (not exposed through Nginx)

**Request:** Empty JSON body `{}`

**Response (HTTP 200):**
```json
{"status": "reloaded", "model_version": "deepfake/Production/2"}
```

---

### POST /feedback

Submit ground-truth label for a previous prediction to close the feedback loop.

**Request:** `application/json`
```json
{
  "request_id": "uuid-string",
  "predicted": "fake",
  "ground_truth": "real"
}
```

**Validation:**
- `predicted` and `ground_truth` must be `"real"` or `"fake"` — returns HTTP 422 otherwise
- `request_id` is a free-form string (UUID recommended)

**Response (HTTP 200):**
```json
{"status": "logged", "request_id": "uuid-string"}
```

**Response (HTTP 500):** `{"detail": "<error message>"}` — if feedback logger fails

**Data flow:**
1. Validate Pydantic `FeedbackRequest` schema
2. `log_feedback(request_id, predicted, ground_truth)` → appends JSONL entry to `data/feedback/feedback_log.jsonl`
3. Prometheus `ERROR_COUNTER` incremented on failure

---

### POST /predict/batch

Predict multiple videos in one request (max 10 files).

**Request:** `multipart/form-data`
- `files`: list of MP4 video files (each max 100MB)

**Validation:** Returns HTTP 400 if more than 10 files submitted.

**Response (HTTP 200):**
```json
{
  "results": [
    {
      "filename": "video1.mp4",
      "prediction": "fake",
      "confidence": 0.87,
      "inference_latency_ms": 132.1,
      "error": null
    },
    {
      "filename": "video2.mp4",
      "prediction": null,
      "confidence": null,
      "inference_latency_ms": null,
      "error": "Only MP4 files are accepted"
    }
  ],
  "total": 2,
  "succeeded": 1,
  "failed": 1
}
```

**Data flow:** Each file is processed independently via the same pipeline as `POST /predict`. Errors per file are captured without aborting the batch.

---

### POST /admin/rollback

Roll back the loaded model to a specific MLflow registry version.

**Request:** `application/json`
```json
{"version": "2"}
```

**Response (HTTP 200):**
```json
{"status": "reloaded", "model_version": "models:/deepfake/2"}
```

**Response (HTTP 500):** `{"detail": "<error message>"}` — if version not found or load fails

---

### GET /admin/model-info

Return metadata about the currently loaded model.

**Response (HTTP 200):**
```json
{
  "model_version": "models:/deepfake/Production",
  "run_id": "abc123def456",
  "model_loaded": true
}
```

---

### GET /pipeline/mlflow-runs

**Response (HTTP 200):**
```json
[
  {
    "run_id": "abc123",
    "status": "FINISHED",
    "metrics": {"val_f1": 0.932, "val_accuracy": 0.94},
    "tags": {"git_commit": "abc1234"}
  }
]
```

---

### GET /pipeline/airflow-runs

**Response (HTTP 200):**
```json
[
  {
    "dag_id": "deepfake_pipeline",
    "state": "success",
    "start_date": "2026-03-24T10:00:00",
    "end_date": "2026-03-24T10:08:23"
  }
]
```

---

### GET /pipeline/throughput

**Response (HTTP 200):**
```json
{"videos_per_minute": 12.4}
```

---

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
**Response 200:** `{ "reply": "string" }` — rule-based keyword match (offline, no LLM)
**Response 422:** If message is empty

---

## 2. Module Reference

### `backend/app/preprocessing.py`
- `get_mtcnn()` — lazy singleton MTCNN loader (device=cpu)
- `extract_frames(video_path, num_frames=30)` — sample frames evenly with `np.linspace`; raises `ValueError` if video unreadable
- `detect_faces(frames)` — MTCNN detection; fallback to resized frame on miss; converts MTCNN output `(pixel+1)*127.5`
- `preprocess_video(video_path, num_frames=30)` — full pipeline; pads by repeating last frame if needed

### `backend/app/model_loader.py`
- Singleton pattern with module-level `_model` and `_current_version`
- `load_model()` — reads `MODEL_NAME`/`MODEL_STAGE` env vars; calls `mlflow.pyfunc.load_model`
- `reload_model()` — force-reloads for rollback support

### `backend/app/drift_detector.py`
- `compute_drift_score(features, baseline)` — mean absolute z-score; zero-std guard via `np.where(std==0, 1e-8, std)`
- Default threshold: `3.0` (configurable)
- `load_baseline()` — returns None if `ml/feature_baseline.json` not found

### `backend/app/explainability.py`
- `generate_gradcam(model, frames_tensor)` — hooks last EfficientNet `_blocks` layer; returns base64 PNG; returns `""` on any failure

---

## 3. Airflow DAG Reference

### deepfake_pipeline (daily)
```
ingest_videos → extract_frames → detect_faces → compute_features → validate_schema → record_baseline_stats → version_with_dvc
```

### retraining_dag (weekly)
```
check_drift (BranchPythonOperator)
  ├── fetch_new_data → run_mlproject → evaluate_model → register_if_better → promote_to_production
  └── skip_retraining (DummyOperator)
```

---

## 4. Data Directory Structure

```
data/
├── raw/          # Original MP4 files (.dvc tracked)
├── frames/       # Extracted JPG frames (per video subfolder)
├── faces/        # MTCNN-cropped face images (per video subfolder)
├── features/     # EfficientNet feature tensors (.pt files)
└── feedback/     # Ground-truth feedback log (feedback_log.jsonl)
```

---

## 5. MLflow Model Registry Stages

```
None → Staging → Production → Archived
```

- Training creates version in `None` stage
- `register_if_better()` (retraining DAG) transitions to `Staging` if F1 ≥ 0.90
- `promote_to_production()` transitions Staging → Production with `archive_existing_versions=True`
- Rollback: re-transition any Archived version back to Production
