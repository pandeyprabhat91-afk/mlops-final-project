# Deepfake Detection System — Design Specification
**Date:** 2026-03-23
**Version:** 1.0
**Project:** End-to-end Deepfake Detection with Full MLOps Pipeline

---

## 1. Problem Statement

Deepfake videos are AI-generated manipulations that impersonate individuals or fabricate events, posing risks in cybersecurity, digital forensics, defense, and social media. This system provides an end-to-end solution to classify MP4 videos as **real** or **fake** using a deep learning model, served through a production-grade MLOps pipeline.

### Success Metrics
| Metric | Target |
|---|---|
| Accuracy | ≥ 90% |
| F1-score | ≥ 0.90 |
| Inference latency | < 200 ms |
| Data pipeline throughput | ≥ 10 videos/minute end-to-end via Airflow |

Every experiment must be reproducible via a specific **Git commit hash** and a corresponding **MLflow run ID**.

---

## 2. Architecture Overview

```
User → [React Frontend (Nginx)]
         ↓ REST API
       [FastAPI Backend]
         ↓ calls
       [MLflow Model Server] ←── [MLflow Tracking Server + Registry]
         ↑                              ↑
       [Preprocessing]           [ml/train.py + MLproject]
       (frames + faces)                 ↑
         ↑                        [Airflow DAG]
       [Data Pipeline]                  ↑
       (DVC + Git LFS)           [Raw MP4 Data (DVC)]
         ↓
       [Prometheus] → [Grafana Dashboards + Alerts]
```

**Core principle:** Frontend and backend are strictly loosely coupled — connected only via configurable REST API calls. No direct model access from the frontend.

---

## 3. Repository Structure

```
deepfake-detection/
├── docker-compose.yml             # Orchestrates all services
├── docker-compose.override.yml    # Dev overrides (hot reload, debug)
├── .env                           # Runtime secrets (not committed)
├── .env.example                   # Template for secrets
├── .gitattributes                 # Git LFS config for large files
├── .dvcignore                     # DVC ignore rules
├── pyproject.toml                 # black + flake8 + isort config
├── README.md
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # CI: lint → DVC repro → pytest unit → pytest integration
│
├── frontend/
│   ├── Dockerfile                 # Nginx + React build
│   ├── nginx.conf                 # Serve React, proxy /api → backend
│   ├── package.json
│   └── src/
│       ├── App.tsx
│       ├── pages/
│       │   ├── Home.tsx           # Video upload + result display
│       │   └── PipelineDashboard.tsx  # ML pipeline visualization
│       ├── components/
│       │   ├── VideoUpload.tsx    # Drag-drop upload with validation
│       │   ├── ResultCard.tsx     # Prediction + confidence + Grad-CAM
│       │   ├── PipelineStatus.tsx # Airflow DAG status
│       │   ├── ExperimentTable.tsx# MLflow runs table
│       │   └── ErrorConsole.tsx   # Errors/failures/successful runs log
│       ├── api/
│       │   └── client.ts          # Axios client with base URL from env
│       └── hooks/
│           └── usePrediction.ts   # Upload + polling logic
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt       # pytest, black, flake8, isort
│   └── app/
│       ├── main.py                # FastAPI app + router registration
│       ├── routers/
│       │   └── predict.py         # POST /predict, GET /health, GET /ready
│       ├── model_loader.py        # Load model from MLflow registry
│       ├── preprocessing.py       # MP4 → frames → face detection (MTCNN)
│       ├── explainability.py      # Grad-CAM heatmap generation
│       ├── drift_detector.py      # Feature drift vs baseline stats
│       ├── feedback_logger.py     # Ground truth label logging
│       ├── metrics.py             # Prometheus custom metrics (Counter, Histogram)
│       ├── logging_config.py      # Structured JSON logging setup
│       └── schemas.py             # Pydantic request/response models
│
├── ml/
│   ├── MLproject                  # MLflow project definition
│   ├── conda.yaml                 # MLproject environment spec
│   ├── dvc.yaml                   # DVC DAG (pipeline stages)
│   ├── dvc.lock                   # DVC lock file (committed)
│   ├── params.yaml                # Hyperparameters (tracked by DVC + MLflow)
│   ├── model.py                   # CNN+LSTM architecture (EfficientNet backbone)
│   ├── train.py                   # Training loop + MLflow custom logging
│   ├── evaluate.py                # Evaluation + metrics report
│   ├── data_loader.py             # Frame dataset + augmentation
│   ├── drift_baseline.py          # Compute + save feature baseline stats
│   └── requirements.txt
│
├── data/                          # DVC-managed (not committed to Git)
│   ├── raw/                       # Original MP4s (.dvc tracked)
│   ├── frames/                    # Extracted frames
│   ├── faces/                     # Cropped face regions
│   └── features/                  # Processed feature tensors
│
├── airflow/
│   ├── dags/
│   │   ├── deepfake_pipeline.py   # Data ingestion + preprocessing DAG
│   │   └── retraining_dag.py      # Automated retraining DAG
│   └── plugins/
│
├── monitoring/
│   ├── prometheus.yml             # Scrape configs (backend, airflow, mlflow, nginx)
│   ├── alert_rules.yml            # Alert: error rate > 5%, drift detected
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   └── dashboards/
│       └── dashboards/
│           ├── inference.json     # Request rate, latency, error rate
│           ├── data_pipeline.json # Airflow task durations, throughput
│           └── model_drift.json   # Feature drift over time
│
├── tests/
│   ├── conftest.py                # Pytest fixtures (test client, sample video)
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   ├── test_model.py
│   │   ├── test_drift_detector.py
│   │   └── test_schemas.py
│   └── integration/
│       ├── test_predict_endpoint.py   # Full POST /predict pipeline
│       └── test_health_endpoints.py
│
└── docs/
    ├── HLD.md                     # High-level design + architecture rationale
    ├── LLD.md                     # API endpoint specs with I/O definitions
    ├── test_plan.md               # Test cases + acceptance criteria
    ├── test_report.md             # Pass/fail results (generated after test run)
    ├── user_manual.md             # Non-technical user guide
    └── architecture_diagram.png   # Visual architecture diagram
```

---

## 4. Docker Compose Services

| Service | Image | Port | Purpose |
|---|---|---|---|
| `frontend` | `./frontend` | 3000 | React app served via Nginx |
| `backend` | `./backend` | 8000 | FastAPI prediction + health APIs |
| `mlflow-server` | `ghcr.io/mlflow/mlflow` | 5000 | Tracking UI + Model Registry |
| `mlflow-serve` | `./ml` | 5001 | MLflow pyfunc model server |
| `airflow-webserver` | `apache/airflow` | 8080 | Airflow UI |
| `airflow-scheduler` | `apache/airflow` | — | DAG scheduler |
| `airflow-worker` | `apache/airflow` | — | Task executor |
| `postgres` | `postgres:15` | 5432 | Airflow + MLflow metadata DB |
| `redis` | `redis:7` | 6379 | Airflow Celery broker |
| `prometheus` | `prom/prometheus` | 9090 | Metrics scraping |
| `grafana` | `grafana/grafana` | 3001 | Dashboards + alerting |

All services communicate on an internal Docker network (`deepfake-net`). Only `frontend` (3000), `backend` (8000), `mlflow-server` (5000), `airflow-webserver` (8080), and `grafana` (3001) are exposed to the host.

---

## 5. API Specification (LLD Summary)

### `POST /predict`
**Request:** `multipart/form-data` — `file: MP4 video (max 100MB)`
**Response:**
```json
{
  "prediction": "fake",
  "confidence": 0.94,
  "inference_latency_ms": 143,
  "gradcam_image": "<base64 string>",
  "mlflow_run_id": "abc123",
  "frames_analyzed": 30
}
```

### `GET /health`
**Response:** `{"status": "ok", "model_loaded": true}`

### `GET /ready`
**Response:** `{"status": "ready", "model_version": "deepfake/Production/3"}`

### `GET /metrics`
**Response:** Prometheus text exposition format (scraped by Prometheus; not called by frontend). Includes proxied metrics for `mlflow-serve` (inference count, latency) since MLflow pyfunc server has no native Prometheus endpoint — backend instruments these metrics on every call to `mlflow-serve`.

### `POST /admin/reload-model`
**Auth:** Internal only (not exposed through Nginx to the public)
**Purpose:** Force-reloads the model from MLflow registry (used during rollback)
**Request:** `{}` (empty body)
**Response:** `{"status": "reloaded", "model_version": "deepfake/Production/2"}`

---

## 6. Model Architecture

**CNN + LSTM with EfficientNet-B0 backbone:**
1. Input: sequence of 30 face-cropped frames (224×224 RGB)
2. EfficientNet-B0 (pretrained ImageNet) → spatial features per frame
3. LSTM (hidden=256, layers=2) → temporal dependencies across frames
4. Dense → Sigmoid → binary output (real/fake)

**Face detection:** MTCNN (Multi-task Cascaded CNN) for robust face cropping
**Optimization:** Post-training quantization (INT8) for local hardware performance

---

## 7. MLflow Integration

| Stage | What is logged |
|---|---|
| Training | `accuracy`, `f1`, `loss`, `val_loss` per epoch (custom, beyond autolog) |
| Training | `learning_rate`, `batch_size`, `lstm_hidden`, `backbone` (params) |
| Training | `confusion_matrix.png`, `roc_curve.png`, `model.pkl` (artifacts) |
| Training | `frame_count`, `face_detection_rate`, preprocessing stats |
| Inference | Per-request `inference_latency_ms`, `confidence_score` |
| Model Registry | Stages: `None → Staging → Production → Archived` (rollback = demote) |

**Reproducibility:** Each run tagged with Git commit SHA via `mlflow.set_tag("git_commit", subprocess.check_output(["git", "rev-parse", "HEAD"]))`

**Backend loads model:** `mlflow.pyfunc.load_model("models:/deepfake/Production")`

---

## 8. Data Pipeline (Airflow DAG)

**`deepfake_pipeline` DAG:**
```
ingest_videos → extract_frames → detect_faces → compute_features → validate_schema → record_baseline_stats → version_with_dvc
```

**Data Validation (`validate_schema` task):**
- Schema checks: each sample must have `frames` (list, len ≥ 1), `face_tensor` (shape `[N, 3, 224, 224]`), `label` (`0` or `1`)
- Null checks: `face_tensor` must contain no NaN values; `label` must not be null
- Dimension checks: tensor dtype must be `float32`; pixel values in `[0.0, 1.0]`
- On failure: task raises `AirflowException`, DAG halts, Prometheus counter `pipeline_validation_failures_total` incremented, Grafana alert fired

**`retraining_dag` DAG (scheduled / drift-triggered):**
```
check_drift → fetch_new_data → run_mlproject → evaluate_model → register_if_better → promote_to_production
```

**DVC pipeline stages** (`dvc.yaml`):
```
stages:
  extract_frames → detect_faces → compute_features → train → evaluate
```

---

## 9. Monitoring & Alerting

**Prometheus scrape targets:**
- `backend:8000/metrics` — request count, latency histogram, error rate, drift score, **plus proxied mlflow-serve metrics** (inference count, per-request latency). Since `mlflow-serve` (pyfunc server) exposes no native `/metrics` endpoint, the backend's `metrics.py` instruments all calls to `mlflow-serve` and exposes them here. There is no separate scrape target for `mlflow-serve:5001`.
- `airflow-webserver:8080/metrics` — DAG success/failure rates, task duration
- `mlflow-server:5000/metrics` — experiment count, model versions
- `frontend nginx:9113/metrics` — via nginx-prometheus-exporter sidecar

**Grafana alert rules:**
- Error rate > 5% → trigger alert
- Feature drift score > threshold → trigger retraining DAG
- Inference latency p95 > 200ms → alert

---

## 10. Security

- All secrets in `.env` (not committed) — `.env.example` documents required keys
- HTTPS enforced via Nginx TLS termination in production
- Prometheus and Grafana behind basic auth
- No cloud usage — all data stays local
- **Encryption at rest:** Docker volumes for `data/` (face crops, feature tensors) and Postgres are mounted on an OS-level encrypted filesystem (BitLocker on Windows, LUKS on Linux). This is documented in `docs/HLD.md` under the security section. As a local-only deployment, Docker volume encryption is the responsibility of the host OS. The `README.md` documents the requirement for the host filesystem to be encrypted before running the system.

### Rollback Procedure

**Trigger:** Grafana alert fires when error rate > 5% sustained for 3 minutes OR manual decision.

**Steps:**
1. Via MLflow UI (or `mlflow models` CLI): demote current `Production` model to `Archived`
2. Promote the previous `Production` version (now `Archived`) back to `Production`
3. Backend detects version change on next `/ready` poll (or force-reload via `POST /admin/reload-model`)
4. The `retraining_dag` `check_drift` task also triggers this flow automatically when drift exceeds threshold

**Rollback is supported by MLflow Model Registry stages** — every promoted model version is retained in `Archived` state, never deleted, ensuring any version can be reinstated.

---

## 11. Frontend Pages

### Page 1: Home (Video Upload + Results)
- Drag-and-drop MP4 upload with file validation (type + size)
- Loading state during inference
- Result card: prediction label (REAL/FAKE), confidence bar, Grad-CAM overlay
- Error boundary — graceful error display for all failure modes

### Page 2: Pipeline Dashboard
- MLflow experiments table (run ID, metrics, status, git commit)
- Airflow DAG status (last run, next run, task breakdown)
- **Throughput widget:** videos/minute processed in the last pipeline run (polled from Airflow API)
- Error/failure/success console (last N pipeline runs)
- Links to full MLflow UI and Airflow UI

---

## 12. Testing Strategy

| Level | Tool | Coverage |
|---|---|---|
| Unit | pytest | preprocessing, model, drift detector, schemas |
| Integration | pytest + httpx | POST /predict, /health, /ready end-to-end |
| Acceptance | manual + test report | Accuracy ≥ 90%, latency < 200ms |

**Acceptance criteria:** Model must achieve F1 ≥ 0.90 and accuracy ≥ 90% on held-out test set. Inference latency measured over 100 requests must have p95 < 200ms.

---

## 13. CI/CD Pipeline

**File:** `.github/workflows/ci.yml`
**Trigger:** Push to `main` or any pull request

**Pipeline stages (in order):**
```
1. lint       → black --check, flake8, isort --check (Python)
               → eslint --max-warnings 0 (TypeScript/React)
2. dvc-repro  → dvc repro (runs extract_frames → train → evaluate stages)
3. unit-tests → pytest tests/unit/ --cov=app --cov-report=xml
4. int-tests  → docker-compose -f docker-compose.yml up -d
               → pytest tests/integration/
               → docker-compose down
5. report     → upload test coverage and pytest results as CI artifacts
```

**DVC CI integration:** `dvc repro` uses the DVC DAG (`dvc.yaml`) to ensure pipeline stages are deterministic and reproducible. DVC lock file (`dvc.lock`) is committed and checked for drift on every run.

---

## 14. Code Quality Standards


- **Style:** PEP8 enforced via `black` + `flake8` + `isort` (configured in `pyproject.toml`)
- **Paradigm:** Object-oriented for model/pipeline classes; functional for API route handlers
- **Logging:** Structured JSON logging via `logging_config.py` across all backend modules
- **Exception handling:** All route handlers wrapped with try/except; errors return structured JSON with status codes
- **Inline docs:** All functions have docstrings; complex logic has inline comments

---

## 15. Documentation Deliverables

| Document | Location | Audience |
|---|---|---|
| HLD | `docs/HLD.md` | Technical reviewers |
| LLD | `docs/LLD.md` | Developers |
| Test Plan + Cases | `docs/test_plan.md` | QA / evaluators |
| Test Report | `docs/test_report.md` | Evaluators |
| User Manual | `docs/user_manual.md` | Non-technical users |
| Architecture Diagram | `docs/architecture_diagram.png` | All |
