# High-Level Design — Deepfake Detection System

**Version:** 1.0
**Date:** 2026-03-24

---

## 1. System Overview

The Deepfake Detection System is an end-to-end ML platform that classifies MP4 videos as **real** or **fake** using a deep learning model, served through a production-grade MLOps pipeline. The system is designed for local deployment using Docker Compose.

**Key design goals:**
- End-to-end deepfake classification with ≥ 90% accuracy and ≥ 0.90 F1-score
- Full MLOps lifecycle: data versioning, experiment tracking, model registry, automated retraining
- Sub-200ms inference latency (p95)
- Reproducibility: every experiment tied to a Git commit hash and MLflow run ID
- Monitoring, alerting, and drift detection on all components

---

## 2. Architecture

```
User → [React Frontend (Nginx:3000)]
         ↓ REST API (/api/* → proxied to backend)
       [FastAPI Backend :8000]
         ↓ mlflow.pyfunc.load_model() — in-process, no separate server
       [MLflow Model Registry]  ←──  [MLflow Tracking Server :5000]
         ↑                                    ↑
       [Preprocessing]              [ml/train.py + MLproject]
       (MTCNN + EfficientNet)               ↑
         ↑                          [Airflow DAGs :8080]
       [MP4 Upload (temp file)]     (LocalExecutor — scheduler + tasks in one process)
                                            ↑
                                   [Raw MP4 Data (DVC + Git LFS)]
                                            ↓
       [Prometheus :9090] → [Grafana :3001]
       [Node Exporter :9100] ↗
```

**Core principle:** Frontend and backend are strictly loosely coupled — connected only via configurable REST API calls. No direct model access from the frontend.

---

## 3. Component Responsibilities

### FastAPI Backend (port 8000)
- Receives MP4 video uploads and preprocesses them (frame extraction → MTCNN face detection)
- Calls the MLflow-registered Production model for inference
- Generates Grad-CAM explainability heatmaps
- Exposes Prometheus metrics at `/metrics`
- Detects feature drift against stored baseline
- Logs ground-truth feedback for ongoing performance tracking

### MLflow (port 5000)
- **mlflow-server (5000):** Tracking server + Model Registry UI. Stores experiment runs, metrics, artifacts, model versions.
- The backend loads the model directly via `mlflow.pyfunc.load_model("models:/deepfake/Production")` — no separate model-serving container is needed.

### Apache Airflow (port 8080)
- Runs with **LocalExecutor** — tasks execute in-process alongside the scheduler, no separate worker container required.
- **deepfake_pipeline DAG:** Daily data ingestion pipeline — ingest MP4s → extract frames → MTCNN face detection → EfficientNet feature extraction → schema validation → baseline stats → DVC versioning.
- **retraining_dag:** Weekly automated retraining — checks baseline staleness → fetches new data → MLflow run → evaluates → registers if F1 ≥ 0.90 → promotes to Production.

### DVC
- Manages data versioning for `data/raw/`, `data/frames/`, `data/faces/`, `data/features/`
- Defines a 5-stage pipeline DAG: `extract_frames → detect_faces → compute_features → train → evaluate`
- Lock file (`dvc.lock`) committed to Git for exact reproducibility

### React Frontend (port 3000)
- Page 1 (Home): drag-and-drop MP4 upload, loading state, prediction result with confidence bar and Grad-CAM overlay
- Page 2 (Pipeline Dashboard): MLflow experiments table, Airflow DAG status, pipeline throughput widget
- Served by Nginx which proxies `/api/*` to the backend

### Prometheus + Grafana (ports 9090, 3001)
- Prometheus scrapes: backend (:8000/metrics), airflow-webserver (:8080/admin/metrics), mlflow-server (:5000/metrics), nginx exporter (:9113/metrics)
- Grafana dashboards: inference (request rate, latency, error rate, drift score), data pipeline (task durations, throughput), model drift (z-score over time)
- Alert rules: error rate > 5%, p95 latency > 200ms, drift score > 3.0, pipeline validation failure

---

## 4. Model Architecture

**CNN + LSTM with EfficientNet-B0 backbone:**

```
Input: (batch, 30, 3, 224, 224)  ← 30 face-cropped frames
  ↓
EfficientNet-B0 (pretrained ImageNet)  ← spatial features per frame
  ↓ (batch, 30, 1280)
2-layer LSTM (hidden=256)  ← temporal dependencies across frames
  ↓ (batch, 256)  ← last timestep
Linear(256→128) → ReLU → Dropout(0.3) → Linear(128→1) → Sigmoid
  ↓
Output: (batch, 1)  ← probability (>= 0.5 = fake)
```

**Preprocessing pipeline:**
1. `extract_frames()` — sample 30 frames evenly using `np.linspace`
2. `detect_faces()` — MTCNN face detection; fallback to resized full frame if no face
3. Normalize with ImageNet stats (mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])

---

## 5. Software Design Paradigm

The codebase uses a **mixed OO + functional paradigm**, chosen per layer:

| Layer | Paradigm | Rationale |
|---|---|---|
| ML model (`ml/model.py`) | **Object-Oriented** — `DeepfakeDetector(nn.Module)` | PyTorch's Module system requires OO; encapsulates CNN + LSTM as a single composable unit |
| Backend API (`backend/app/routers/`) | **Functional** — FastAPI route functions | Stateless request handlers are naturally functional; easier to test in isolation |
| Model loader (`backend/app/model_loader.py`) | **Module-level singleton** | Holds shared mutable state (loaded model) without a class; standard Python pattern for process-wide singletons |
| Data pipeline (`airflow/dags/`) | **Functional** — plain Python callables as Airflow operators | Airflow PythonOperator expects callables; pure functions are easier to test and reason about |
| Preprocessing (`backend/app/preprocessing.py`) | **Functional with lazy singleton** — `get_mtcnn()` | Stateless transforms; MTCNN is cached via module-level variable to avoid reloading on each request |

**Loose coupling is enforced at every boundary:** Frontend ↔ Backend via REST only; Backend ↔ Model via `mlflow.pyfunc` URI; Backend ↔ Airflow/MLflow via HTTP. No component has a direct import dependency on another service.

---

## 6. Experiment Tracking — Beyond Autolog

MLflow tracking is **fully manual** (no autolog) to give precise control over what is recorded:

| What is tracked | How | Where |
|---|---|---|
| All hyperparameters | `mlflow.log_params(params)` | From `ml/params.yaml` — single source of truth |
| Per-epoch metrics | `mlflow.log_metrics({...}, step=epoch)` | `train_loss`, `val_loss`, `train_f1`, `val_f1`, `val_accuracy`, `learning_rate` |
| Git commit SHA | `mlflow.set_tag("git_commit", get_git_commit())` | Links every run to the exact code state |
| Device used | `mlflow.set_tag("device", str(device))` | CPU vs CUDA — affects reproducibility |
| Best model artifact | `mlflow.pytorch.log_model(model, "model")` | Registered to Model Registry as `deepfake` |
| Checkpoint copy | `mlflow.log_artifact("ml/best_model.pt", "checkpoints")` | Raw state-dict for checkpoint-based loading |
| Confusion matrix | `mlflow.log_artifact("confusion_matrix.png")` | Visual evaluation artifact |
| ROC curve | `mlflow.log_artifact("roc_curve.png")` | AUC-ROC visual artifact |
| Extended eval metrics | `mlflow.log_metrics({pr_auc, precision_fake, recall_fake, ...})` | Beyond accuracy/F1: PR-AUC, per-class precision/recall, optimal threshold |

Every training run is reproducible: check out the tagged Git commit + MLflow run ID → `dvc repro` recreates the exact model.

---

## 7. Design Choices and Rationale

| Decision | Choice | Rationale |
|---|---|---|
| Feature extractor | EfficientNet-B0 | Best accuracy/efficiency trade-off; pretrained ImageNet weights |
| Temporal model | 2-layer LSTM | Captures inter-frame temporal dependencies; simpler than transformers for this sequence length |
| Face detection | MTCNN | High accuracy, handles pose variation; lightweight at inference |
| Experiment tracking | MLflow | Rich model registry with stage transitions; pyfunc serving |
| Data pipeline | Airflow + DVC | Airflow for orchestration + scheduling; DVC for reproducible data versioning |
| Serving | mlflow.pyfunc (in-process) | Backend loads model directly — no extra container, lower latency, fewer failure points |
| Monitoring | Prometheus + Grafana | Industry standard; no external dependencies |
| Frontend | React + Vite | Fast build; TypeScript safety |

---

## 8. Data Flow — POST /predict

```
1. User uploads MP4 → multipart POST to /predict
2. Backend saves to temp file (tempfile.NamedTemporaryFile)
3. extract_frames(): evenly sample 30 frames with OpenCV
4. detect_faces(): MTCNN crops each frame; fallback to resize
5. Normalize: ImageNet mean/std → tensor (30, 3, 224, 224)
6. model.predict(tensor.unsqueeze(0).numpy()) → confidence float
7. Drift check: z-score vs feature baseline; update Prometheus gauge
8. Grad-CAM: hook last EfficientNet block → heatmap overlay on middle frame
9. Return PredictResponse JSON (prediction, confidence, gradcam_image, latency, run_id)
```

---

## 9. Loose Coupling Strategy

- Frontend ↔ Backend: REST API only. Base URL configurable via `VITE_API_URL` env var.
- Backend ↔ Model: `mlflow.pyfunc.load_model()` URI. Model URI configurable via `MODEL_NAME`/`MODEL_STAGE` env vars.
- Backend ↔ Airflow/MLflow: HTTP proxied via pipeline router. URLs configurable via `MLFLOW_TRACKING_URI`/`AIRFLOW_URL` env vars.
- All secrets: `.env` file (never committed). Template in `.env.example`.

---

## 10. Security

- All secrets stored in `.env` (not committed to Git)
- HTTPS via Nginx TLS termination in production
- Prometheus and Grafana behind basic auth
- No cloud usage — all data stays local
- **Encryption at rest:** Docker volumes for `data/` and Postgres mounted on OS-level encrypted filesystem (BitLocker on Windows / LUKS on Linux). Documented requirement in README.
- Admin endpoint (`POST /admin/reload-model`) not exposed through Nginx to public users

---

## 11. Rollback Procedure

**Trigger:** Error rate > 5% for 3 minutes (Grafana alert) OR manual decision.

**Steps:**
1. Via MLflow UI or CLI: demote current Production model to Archived
2. Promote previous Production version (now Archived) back to Production
3. Backend detects change on next `/ready` poll OR force-reload via `POST /admin/reload-model`
4. `retraining_dag` `check_drift` also triggers this flow when drift exceeds threshold

**Rollback is supported by MLflow Model Registry stages** — every promoted version is retained in Archived state, enabling any version to be reinstated instantly.

---

## 12. Reproducibility Guarantee

Every training run is tagged with the Git commit SHA:
```python
mlflow.set_tag("git_commit", subprocess.check_output(["git", "rev-parse", "HEAD"]))
```

To reproduce any experiment: check out the tagged commit + run the MLflow run ID. DVC `dvc.lock` records exact data versions for full pipeline reproducibility.

---

## 13. Docker Compose Services

| Service | Port | Purpose |
|---|---|---|
| frontend | 3000 | React + Nginx |
| backend | 8000 | FastAPI |
| mlflow-server | 5000 | Tracking UI + Registry |
| airflow-webserver | 8080 | Airflow UI |
| airflow-scheduler | — | DAG scheduler (LocalExecutor — runs tasks in-process) |
| airflow-init | — | One-shot DB init + admin user creation |
| postgres | 5432 | Airflow metadata + backend |
| prometheus | 9090 | Metrics scraping |
| grafana | 3001 | Dashboards + alerts |
| node-exporter | 9100 | Host system metrics (CPU, RAM, disk) |
