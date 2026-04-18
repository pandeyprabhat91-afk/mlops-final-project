# Deepfake Detection MLOps — Setup Guide

## Prerequisites

- Python 3.11+
- Docker Desktop (running)
- DVC 3.x — `pip install dvc`
- Git

---

## Fresh Setup (first machine)

```bash
git clone <repo-url>
cd deepfake-detection
docker compose up -d
```

To populate the MLflow UI with sample training runs and model versions:

```bash
# Copy and run inside the mlflow-server container
docker cp ml/populate_mlflow.py deepfake-detection-mlflow-server-1:/tmp/populate_mlflow.py
docker exec -e GIT_PYTHON_REFRESH=quiet -e MLFLOW_TRACKING_URI=http://localhost:5000 \
  deepfake-detection-mlflow-server-1 python3 /tmp/populate_mlflow.py
```

> **Windows Git Bash:** prefix `docker` commands with `MSYS_NO_PATHCONV=1` to prevent path translation.

---

## Migration to Another PC

Raw video data is NOT in git. The `dvc-storage/` folder (local content-addressed cache) must be transferred alongside the repository.

### Step 1 — Transfer files

Copy **both** of these to the new machine:

| What | Where |
|---|---|
| Git repository | `deepfake-detection/` folder (clone or copy) |
| DVC cache | `dvc-storage/` folder (sits **next to** `deepfake-detection/`) |

**OneDrive:** If the project is inside OneDrive, both folders sync automatically — no manual copy needed.

**Zip transfer:**
```
project-root/
├── deepfake-detection/   ← git repo
└── dvc-storage/          ← DVC cache (copy this too)
```

### Step 2 — Restore raw data

```bash
cd deepfake-detection
dvc pull          # restores data/raw/ (106 videos, 182 MB) from dvc-storage/
```

Expected output: `X files fetched`

### Step 3 — Start services

```bash
docker compose up -d
```

### Step 4 — Reproduce the pipeline (optional)

```bash
# Linux / macOS / Windows Git Bash
export MLFLOW_TRACKING_URI=http://localhost:5000
dvc repro

# Windows PowerShell
$env:MLFLOW_TRACKING_URI = "http://localhost:5000"
dvc repro
```

`dvc repro` runs all stages in order:
1. `extract_frames` — extract 30 frames per video from `data/raw/`
2. `detect_faces` — MTCNN face detection on frames
3. `compute_features` — save face-crop tensors for model input
4. `train` — train EfficientNet-B0 + LSTM, log to MLflow
5. `evaluate` — evaluate best checkpoint on test set

Stages that haven't changed are skipped automatically.

---

## DVC Commands Reference

| Command | Description |
|---|---|
| `dvc status` | Show which stages are out of date |
| `dvc repro` | Re-run all outdated stages |
| `dvc repro train` | Re-run only the train stage |
| `dvc metrics show` | Print `val_f1`, `val_accuracy`, `val_loss`, `best_epoch` |
| `dvc metrics diff HEAD~1` | Compare metrics vs previous commit |
| `dvc dag` | Show pipeline dependency graph |
| `dvc push` | Push data/model changes to `dvc-storage/` |
| `dvc pull` | Pull data from `dvc-storage/` |
| `dvc params diff` | Show hyperparameter changes vs previous commit |

---

## Services and Ports

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| MLflow UI | http://localhost:5000 |
| Airflow | http://localhost:8080 (admin / admin) |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |

---

## Troubleshooting

**`dvc pull` says "0 files fetched"**
→ `dvc-storage/` is missing or in the wrong location. It must be at `../dvc-storage` relative to the repo root (i.e., a sibling of `deepfake-detection/`).

**MLflow returns 403**
→ The mlflow-server container needs `--allowed-hosts '*'`. Check docker-compose.yml and run:
```bash
docker compose up -d --force-recreate mlflow-server
```

**`dvc repro` train stage fails with "No .pt files found"**
→ Run `dvc repro compute_features` first to generate `data/features/`.

## Security — TLS Setup

For on-prem deployments, generate self-signed certificates before starting the stack:

```bash
bash scripts/gen_certs.sh
```

Then the frontend is available over HTTPS at https://localhost:3443.

For production, replace `nginx/certs/server.crt` and `nginx/certs/server.key` with
CA-signed certificates. Data at rest (uploaded videos) is stored only in ephemeral
`/tmp` within the container and deleted immediately after inference.
