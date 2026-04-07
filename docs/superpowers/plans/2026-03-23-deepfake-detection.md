# Deepfake Detection System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an end-to-end deepfake detection system with CNN+LSTM model, FastAPI backend, React frontend, Airflow data pipeline, MLflow experiment tracking, and Prometheus/Grafana monitoring — all orchestrated via Docker Compose.

**Architecture:** Monorepo with loosely-coupled services communicating over a Docker internal network. FastAPI backend preprocesses MP4 uploads (MTCNN face detection → frame sequences) and calls an MLflow pyfunc model server for inference. All components are monitored via Prometheus; Airflow manages data pipelines and automated retraining.

**Tech Stack:** Python 3.11, FastAPI, PyTorch, EfficientNet-B0, MTCNN, MLflow, Apache Airflow, DVC, React 18 + Vite + TypeScript, Prometheus, Grafana, Docker Compose, pytest, GitHub Actions

**Spec:** `docs/superpowers/specs/2026-03-23-deepfake-detection-design.md`

---

## Phase 1: Project Scaffold

### Task 1: Repository Root Setup

**Files:**
- Create: `deepfake-detection/.env.example`
- Create: `deepfake-detection/.gitignore`
- Create: `deepfake-detection/.gitattributes`
- Create: `deepfake-detection/.dvcignore`
- Create: `deepfake-detection/pyproject.toml`
- Create: `deepfake-detection/README.md`

- [ ] **Step 1: Create project root directory**
```bash
mkdir deepfake-detection && cd deepfake-detection
git init
dvc init
```

- [ ] **Step 2: Create `.gitignore`**
```
.env
__pycache__/
*.pyc
*.pyo
.pytest_cache/
*.egg-info/
dist/
build/
.coverage
htmlcov/
node_modules/
frontend/dist/
data/raw/
data/frames/
data/faces/
data/features/
*.dvc
!.dvcignore
mlruns/
```

- [ ] **Step 3: Create `.gitattributes` for Git LFS**
```
data/raw/*.mp4 filter=lfs diff=lfs merge=lfs -text
data/frames/**/*.jpg filter=lfs diff=lfs merge=lfs -text
data/faces/**/*.jpg filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.pt filter=lfs diff=lfs merge=lfs -text
```

- [ ] **Step 4: Create `.dvcignore`**
```
.git
__pycache__
*.pyc
node_modules
```

- [ ] **Step 5: Create `pyproject.toml`**
```toml
[tool.black]
line-length = 88
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
exclude = [".git", "__pycache__", "node_modules", "data"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

- [ ] **Step 6: Create `.env.example`**
```
# Database
POSTGRES_USER=deepfake
POSTGRES_PASSWORD=changeme
POSTGRES_DB=deepfake_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# MLflow
MLFLOW_TRACKING_URI=http://mlflow-server:5000
MLFLOW_EXPERIMENT_NAME=deepfake-detection
MODEL_NAME=deepfake
MODEL_STAGE=Production

# Airflow
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://deepfake:changeme@postgres/deepfake_db
AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://deepfake:changeme@postgres/deepfake_db
AIRFLOW__CORE__FERNET_KEY=changeme_generate_with_fernet

# Backend
BACKEND_PORT=8000
MODEL_SERVER_URL=http://mlflow-serve:5001/invocations

# Monitoring
GRAFANA_ADMIN_PASSWORD=changeme
```

- [ ] **Step 7: Copy `.env.example` to `.env` and fill real values**
```bash
cp .env.example .env
```

- [ ] **Step 8: Commit scaffold**
```bash
git add .gitignore .gitattributes .dvcignore pyproject.toml .env.example README.md
git commit -m "chore: initialize project scaffold"
```

---

### Task 2: Docker Compose Infrastructure

**Files:**
- Create: `docker-compose.yml`
- Create: `docker-compose.override.yml`

- [ ] **Step 1: Create `docker-compose.yml`**
```yaml
version: "3.9"

x-airflow-common: &airflow-common
  image: apache/airflow:2.8.1
  env_file: .env
  volumes:
    - ./airflow/dags:/opt/airflow/dags
    - ./airflow/plugins:/opt/airflow/plugins
    - ./data:/opt/airflow/data
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy

networks:
  deepfake-net:
    driver: bridge

volumes:
  postgres-data:
  mlflow-data:
  grafana-data:
  prometheus-data:

services:
  postgres:
    image: postgres:15
    env_file: .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks: [deepfake-net]
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "${POSTGRES_USER}"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    networks: [deepfake-net]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      retries: 5

  mlflow-server:
    image: ghcr.io/mlflow/mlflow:v2.11.1
    command: >
      mlflow server
      --host 0.0.0.0
      --port 5000
      --backend-store-uri postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres/${POSTGRES_DB}
      --default-artifact-root /mlflow/artifacts
    volumes:
      - mlflow-data:/mlflow/artifacts
    ports: ["5000:5000"]
    networks: [deepfake-net]
    depends_on:
      postgres:
        condition: service_healthy

  mlflow-serve:
    build:
      context: ./ml
      dockerfile: Dockerfile.serve
    ports: ["5001:5001"]
    networks: [deepfake-net]
    env_file: .env
    depends_on: [mlflow-server]

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports: ["8080:8080"]
    networks: [deepfake-net]

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    networks: [deepfake-net]

  airflow-worker:
    <<: *airflow-common
    command: celery worker
    networks: [deepfake-net]

  airflow-init:
    <<: *airflow-common
    command: >
      bash -c "airflow db init && airflow users create
      --username admin --password admin
      --firstname Admin --lastname User
      --role Admin --email admin@example.com"
    networks: [deepfake-net]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    networks: [deepfake-net]
    env_file: .env
    depends_on: [mlflow-serve]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      retries: 3

  frontend:
    build: ./frontend
    ports: ["3000:80"]
    networks: [deepfake-net]
    depends_on: [backend]

  prometheus:
    image: prom/prometheus:v2.50.1
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus-data:/prometheus
    ports: ["9090:9090"]
    networks: [deepfake-net]

  grafana:
    image: grafana/grafana:10.3.1
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    ports: ["3001:3000"]
    networks: [deepfake-net]
    depends_on: [prometheus]
```

- [ ] **Step 2: Create `docker-compose.override.yml` for dev**
```yaml
version: "3.9"
services:
  backend:
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  frontend:
    build:
      target: dev
    volumes:
      - ./frontend/src:/app/src
    command: npm run dev -- --host
```

- [ ] **Step 3: Commit**
```bash
git add docker-compose.yml docker-compose.override.yml
git commit -m "chore: add docker-compose infrastructure"
```

---

## Phase 2: ML Model

### Task 3: Model Architecture

**Files:**
- Create: `ml/model.py`
- Create: `ml/requirements.txt`
- Create: `tests/unit/test_model.py`

- [ ] **Step 1: Write failing test**
```python
# tests/unit/test_model.py
import torch
from ml.model import DeepfakeDetector

def test_output_shape():
    model = DeepfakeDetector()
    # batch=2, frames=30, C=3, H=224, W=224
    x = torch.randn(2, 30, 3, 224, 224)
    out = model(x)
    assert out.shape == (2, 1), f"Expected (2,1), got {out.shape}"

def test_output_in_range():
    model = DeepfakeDetector()
    x = torch.randn(1, 30, 3, 224, 224)
    out = model(x)
    assert 0.0 <= out.item() <= 1.0
```

- [ ] **Step 2: Run test — expect FAIL**
```bash
cd deepfake-detection
pytest tests/unit/test_model.py -v
# Expected: ModuleNotFoundError
```

- [ ] **Step 3: Create `ml/requirements.txt`**
```
torch==2.2.1
torchvision==0.17.1
efficientnet-pytorch==0.7.1
facenet-pytorch==2.5.3
mlflow==2.11.1
dvc==3.48.4
apache-airflow==2.8.1
opencv-python-headless==4.9.0.80
numpy==1.26.4
pandas==2.2.1
scikit-learn==1.4.1
matplotlib==3.8.3
Pillow==10.2.0
pytest==8.1.0
black==24.3.0
flake8==7.0.0
isort==5.13.2
```

- [ ] **Step 4: Create `ml/model.py`**
```python
"""CNN+LSTM deepfake detector using EfficientNet-B0 as spatial feature extractor."""
import torch
import torch.nn as nn
from efficientnet_pytorch import EfficientNet


class DeepfakeDetector(nn.Module):
    """EfficientNet-B0 spatial encoder + 2-layer LSTM temporal classifier.

    Input:  (batch, num_frames, C, H, W)  — face-cropped frames
    Output: (batch, 1)                     — sigmoid probability (1=fake)
    """

    def __init__(
        self,
        num_frames: int = 30,
        lstm_hidden: int = 256,
        lstm_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.num_frames = num_frames

        # Spatial feature extractor — pretrained ImageNet weights
        self.cnn = EfficientNet.from_pretrained("efficientnet-b0")
        cnn_out_features = self.cnn._fc.in_features
        self.cnn._fc = nn.Identity()  # remove classification head

        # Temporal classifier
        self.lstm = nn.LSTM(
            input_size=cnn_out_features,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout,
        )
        self.classifier = nn.Sequential(
            nn.Linear(lstm_hidden, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Tensor of shape (batch, num_frames, C, H, W)

        Returns:
            Tensor of shape (batch, 1) with sigmoid probabilities
        """
        batch, frames, C, H, W = x.shape
        # Flatten batch+frames for CNN
        x = x.view(batch * frames, C, H, W)
        features = self.cnn(x)  # (batch*frames, cnn_features)
        features = features.view(batch, frames, -1)  # (batch, frames, cnn_features)

        lstm_out, _ = self.lstm(features)  # (batch, frames, lstm_hidden)
        last_hidden = lstm_out[:, -1, :]  # take last timestep

        return self.classifier(last_hidden)
```

- [ ] **Step 5: Run tests — expect PASS**
```bash
pytest tests/unit/test_model.py -v
# Expected: 2 passed
```

- [ ] **Step 6: Commit**
```bash
git add ml/model.py ml/requirements.txt tests/unit/test_model.py
git commit -m "feat(ml): add CNN+LSTM DeepfakeDetector model architecture"
```

---

### Task 4: Data Loader

**Files:**
- Create: `ml/data_loader.py`
- Create: `tests/unit/test_data_loader.py`

- [ ] **Step 1: Write failing test**
```python
# tests/unit/test_data_loader.py
import torch
import numpy as np
import pytest
from ml.data_loader import FrameDataset, get_dataloaders

def make_fake_sample(num_frames=30):
    """Returns (frames_tensor, label) mimicking preprocessed output."""
    return torch.randn(num_frames, 3, 224, 224), 1

def test_dataset_getitem():
    frames, label = make_fake_sample()
    # Simulate a dataset backed by in-memory samples
    samples = [(frames, label), (frames, 0)]
    ds = FrameDataset(samples)
    x, y = ds[0]
    assert x.shape == (30, 3, 224, 224)
    assert y in (0, 1)

def test_dataset_len():
    samples = [(torch.randn(30, 3, 224, 224), 0)] * 5
    ds = FrameDataset(samples)
    assert len(ds) == 5
```

- [ ] **Step 2: Run — expect FAIL**
```bash
pytest tests/unit/test_data_loader.py -v
```

- [ ] **Step 3: Create `ml/data_loader.py`**
```python
"""Frame dataset and dataloader utilities."""
from pathlib import Path
from typing import List, Tuple, Optional

import torch
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms


TRAIN_TRANSFORM = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

EVAL_TRANSFORM = transforms.Compose([
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


class FrameDataset(Dataset):
    """Dataset of (frame_tensor, label) tuples.

    Args:
        samples: List of (tensor[num_frames, C, H, W], int_label) tuples
        transform: Optional per-frame transform applied to each frame
    """

    def __init__(
        self,
        samples: List[Tuple[torch.Tensor, int]],
        transform: Optional[transforms.Compose] = None,
    ):
        self.samples = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        frames, label = self.samples[idx]
        if self.transform:
            frames = torch.stack([self.transform(f) for f in frames])
        return frames, label


def get_dataloaders(
    samples: List[Tuple[torch.Tensor, int]],
    batch_size: int = 8,
    val_split: float = 0.2,
    num_workers: int = 2,
) -> Tuple[DataLoader, DataLoader]:
    """Split samples into train/val and return DataLoaders.

    Returns:
        (train_loader, val_loader)
    """
    val_size = int(len(samples) * val_split)
    train_size = len(samples) - val_size
    train_samples, val_samples = random_split(samples, [train_size, val_size])

    train_ds = FrameDataset(list(train_samples), transform=TRAIN_TRANSFORM)
    val_ds = FrameDataset(list(val_samples), transform=EVAL_TRANSFORM)

    train_loader = DataLoader(train_ds, batch_size=batch_size,
                               shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size,
                             shuffle=False, num_workers=num_workers)
    return train_loader, val_loader
```

- [ ] **Step 4: Run tests — expect PASS**
```bash
pytest tests/unit/test_data_loader.py -v
```

- [ ] **Step 5: Commit**
```bash
git add ml/data_loader.py tests/unit/test_data_loader.py
git commit -m "feat(ml): add FrameDataset and DataLoader utilities"
```

---

### Task 5: Training Script with MLflow

**Files:**
- Create: `ml/train.py`
- Create: `ml/evaluate.py`
- Create: `ml/params.yaml`
- Create: `ml/MLproject`
- Create: `ml/conda.yaml`

- [ ] **Step 1: Create `ml/params.yaml`**
```yaml
train:
  num_frames: 30
  batch_size: 8
  lr: 0.0001
  epochs: 20
  lstm_hidden: 256
  lstm_layers: 2
  dropout: 0.3
  val_split: 0.2
  backbone: efficientnet-b0
```

- [ ] **Step 2: Create `ml/train.py`**
```python
"""Training entry point. Logs all metrics, params, and artifacts to MLflow."""
import subprocess
import sys
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
import torch.nn as nn
import yaml
from sklearn.metrics import f1_score, accuracy_score
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from ml.model import DeepfakeDetector
from ml.data_loader import get_dataloaders


def load_params() -> dict:
    """Load hyperparameters from params.yaml."""
    with open(Path(__file__).parent / "params.yaml") as f:
        return yaml.safe_load(f)["train"]


def get_git_commit() -> str:
    """Return current git commit SHA for reproducibility tagging."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def train_epoch(model, loader, optimizer, criterion, device):
    """Run one training epoch. Returns (avg_loss, accuracy, f1)."""
    model.train()
    total_loss, all_preds, all_labels = 0.0, [], []
    for frames, labels in loader:
        frames, labels = frames.to(device), labels.float().to(device)
        optimizer.zero_grad()
        preds = model(frames).squeeze(1)
        loss = criterion(preds, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        all_preds.extend((preds > 0.5).long().cpu().numpy())
        all_labels.extend(labels.long().cpu().numpy())

    avg_loss = total_loss / len(loader)
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    return avg_loss, acc, f1


def eval_epoch(model, loader, criterion, device):
    """Evaluate model on validation set. Returns (avg_loss, accuracy, f1)."""
    model.eval()
    total_loss, all_preds, all_labels = 0.0, [], []
    with torch.no_grad():
        for frames, labels in loader:
            frames, labels = frames.to(device), labels.float().to(device)
            preds = model(frames).squeeze(1)
            total_loss += criterion(preds, labels).item()
            all_preds.extend((preds > 0.5).long().cpu().numpy())
            all_labels.extend(labels.long().cpu().numpy())

    avg_loss = total_loss / len(loader)
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    return avg_loss, acc, f1


def run_training(samples):
    """Main training loop. Tracks everything to MLflow."""
    params = load_params()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    mlflow.set_experiment(params.get("experiment_name", "deepfake-detection"))

    with mlflow.start_run() as run:
        # Tag for reproducibility
        mlflow.set_tag("git_commit", get_git_commit())
        mlflow.set_tag("device", str(device))

        # Log all hyperparameters explicitly (beyond autolog)
        mlflow.log_params(params)

        model = DeepfakeDetector(
            num_frames=params["num_frames"],
            lstm_hidden=params["lstm_hidden"],
            lstm_layers=params["lstm_layers"],
            dropout=params["dropout"],
        ).to(device)

        optimizer = Adam(model.parameters(), lr=params["lr"])
        criterion = nn.BCELoss()
        scheduler = ReduceLROnPlateau(optimizer, patience=3)
        train_loader, val_loader = get_dataloaders(
            samples,
            batch_size=params["batch_size"],
            val_split=params["val_split"],
        )

        best_val_f1 = 0.0
        for epoch in range(params["epochs"]):
            tr_loss, tr_acc, tr_f1 = train_epoch(
                model, train_loader, optimizer, criterion, device
            )
            val_loss, val_acc, val_f1 = eval_epoch(
                model, val_loader, criterion, device
            )
            scheduler.step(val_loss)

            # Custom per-epoch logging (not just autolog)
            mlflow.log_metrics({
                "train_loss": tr_loss,
                "train_accuracy": tr_acc,
                "train_f1": tr_f1,
                "val_loss": val_loss,
                "val_accuracy": val_acc,
                "val_f1": val_f1,
                "learning_rate": optimizer.param_groups[0]["lr"],
            }, step=epoch)

            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                torch.save(model.state_dict(), "/tmp/best_model.pt")

        # Load best and register
        model.load_state_dict(torch.load("/tmp/best_model.pt"))
        mlflow.pytorch.log_model(
            model,
            artifact_path="model",
            registered_model_name="deepfake",
        )
        mlflow.log_artifact("/tmp/best_model.pt", artifact_path="checkpoints")

        print(f"Run ID: {run.info.run_id} | Best val F1: {best_val_f1:.4f}")
        return run.info.run_id
```

- [ ] **Step 3: Create `ml/evaluate.py`**
```python
"""Standalone evaluation script. Generates confusion matrix and ROC curve artifacts."""
import sys
from pathlib import Path
import mlflow
import mlflow.pytorch
import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, f1_score, confusion_matrix, roc_curve, auc
)

sys.path.insert(0, str(Path(__file__).parent.parent))


def evaluate_model(model, loader, device, run_id: str):
    """Evaluate model and log confusion matrix + ROC curve to MLflow run."""
    model.eval()
    all_preds, all_probs, all_labels = [], [], []

    with torch.no_grad():
        for frames, labels in loader:
            frames = frames.to(device)
            probs = model(frames).squeeze(1).cpu().numpy()
            preds = (probs > 0.5).astype(int)
            all_probs.extend(probs)
            all_preds.extend(preds)
            all_labels.extend(labels.numpy())

    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    cm = confusion_matrix(all_labels, all_preds)
    fpr, tpr, _ = roc_curve(all_labels, all_probs)
    roc_auc = auc(fpr, tpr)

    with mlflow.start_run(run_id=run_id):
        mlflow.log_metrics({"test_accuracy": acc, "test_f1": f1, "roc_auc": roc_auc})

        # Confusion matrix artifact
        fig, ax = plt.subplots()
        ax.matshow(cm, cmap="Blues")
        for (i, j), val in np.ndenumerate(cm):
            ax.text(j, i, str(val), ha="center", va="center")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        fig.savefig("/tmp/confusion_matrix.png")
        mlflow.log_artifact("/tmp/confusion_matrix.png")

        # ROC curve artifact
        fig2, ax2 = plt.subplots()
        ax2.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}")
        ax2.plot([0, 1], [0, 1], "k--")
        ax2.set_xlabel("FPR")
        ax2.set_ylabel("TPR")
        ax2.legend()
        fig2.savefig("/tmp/roc_curve.png")
        mlflow.log_artifact("/tmp/roc_curve.png")

    return acc, f1
```

- [ ] **Step 4: Create `ml/MLproject`**
```yaml
name: deepfake-detection

conda_env: conda.yaml

entry_points:
  train:
    parameters:
      data_path: {type: str, default: "data/features"}
      params_file: {type: str, default: "ml/params.yaml"}
    command: "python ml/train.py --data_path {data_path} --params_file {params_file}"

  evaluate:
    parameters:
      run_id: {type: str}
      data_path: {type: str, default: "data/features"}
    command: "python ml/evaluate.py --run_id {run_id} --data_path {data_path}"
```

- [ ] **Step 5: Create `ml/conda.yaml`**
```yaml
name: deepfake-env
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.11
  - pip
  - pip:
    - -r ml/requirements.txt
```

- [ ] **Step 6: Commit**
```bash
git add ml/train.py ml/evaluate.py ml/params.yaml ml/MLproject ml/conda.yaml
git commit -m "feat(ml): add training script with full MLflow custom logging"
```

---

### Task 6: DVC Pipeline

**Files:**
- Create: `ml/dvc.yaml`
- Create: `ml/drift_baseline.py`

- [ ] **Step 1: Create `ml/dvc.yaml`**
```yaml
stages:
  extract_frames:
    cmd: python ml/preprocessing_pipeline.py extract_frames
    deps:
      - data/raw
      - ml/preprocessing_pipeline.py
    outs:
      - data/frames

  detect_faces:
    cmd: python ml/preprocessing_pipeline.py detect_faces
    deps:
      - data/frames
      - ml/preprocessing_pipeline.py
    outs:
      - data/faces

  compute_features:
    cmd: python ml/preprocessing_pipeline.py compute_features
    deps:
      - data/faces
      - ml/preprocessing_pipeline.py
    outs:
      - data/features

  train:
    cmd: mlflow run . -e train
    deps:
      - data/features
      - ml/train.py
      - ml/model.py
      - ml/params.yaml
    params:
      - ml/params.yaml:
    metrics:
      - ml/metrics.json:
          cache: false

  evaluate:
    cmd: python ml/evaluate.py
    deps:
      - data/features
      - ml/evaluate.py
    metrics:
      - ml/eval_metrics.json:
          cache: false
```

- [ ] **Step 2: Create `ml/drift_baseline.py`**
```python
"""Compute and save feature baseline statistics for drift detection."""
import json
from pathlib import Path
import numpy as np
import torch


BASELINE_PATH = Path("ml/feature_baseline.json")


def compute_baseline(features_dir: str) -> dict:
    """Compute mean, std, min, max for each feature dimension.

    Args:
        features_dir: Path to directory of saved feature .pt files

    Returns:
        dict with keys: mean, std, min, max (each a list of floats)
    """
    all_features = []
    for f in Path(features_dir).glob("*.pt"):
        tensor = torch.load(f)  # shape: (num_frames, feature_dim)
        all_features.append(tensor.mean(dim=0).numpy())

    if not all_features:
        raise ValueError(f"No .pt files found in {features_dir}")

    stacked = np.stack(all_features)  # (N, feature_dim)
    baseline = {
        "mean": stacked.mean(axis=0).tolist(),
        "std": stacked.std(axis=0).tolist(),
        "min": stacked.min(axis=0).tolist(),
        "max": stacked.max(axis=0).tolist(),
        "n_samples": len(all_features),
    }
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2))
    print(f"Baseline saved to {BASELINE_PATH} ({len(all_features)} samples)")
    return baseline


def load_baseline() -> dict:
    """Load saved baseline stats."""
    if not BASELINE_PATH.exists():
        raise FileNotFoundError(
            f"Baseline not found at {BASELINE_PATH}. Run compute_baseline first."
        )
    return json.loads(BASELINE_PATH.read_text())


if __name__ == "__main__":
    import sys
    compute_baseline(sys.argv[1] if len(sys.argv) > 1 else "data/features")
```

- [ ] **Step 3: Create `ml/preprocessing_pipeline.py`** (required by dvc.yaml)
```python
"""CLI entry point for DVC pipeline stages.

Usage: python ml/preprocessing_pipeline.py <stage>
Stages: extract_frames | detect_faces | compute_features
"""
import sys
import logging
from pathlib import Path

import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN
from PIL import Image
from efficientnet_pytorch import EfficientNet
from torchvision import transforms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
FRAMES_DIR = Path("data/frames")
FACES_DIR = Path("data/faces")
FEATURES_DIR = Path("data/features")


def extract_frames():
    """Extract 30 evenly-sampled frames from each MP4 in data/raw/."""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    for mp4 in RAW_DIR.glob("*.mp4"):
        cap = cv2.VideoCapture(str(mp4))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total == 0:
            logger.warning(f"Skipping empty video: {mp4}")
            continue
        indices = np.linspace(0, total - 1, 30, dtype=int)
        out_dir = FRAMES_DIR / mp4.stem
        out_dir.mkdir(exist_ok=True)
        for i, idx in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(str(out_dir / f"frame_{i:03d}.jpg"), frame)
        cap.release()
        logger.info(f"Extracted frames for {mp4.name}")


def detect_faces():
    """Run MTCNN face detection on extracted frames."""
    mtcnn = MTCNN(image_size=224, margin=20, keep_all=False, device="cpu")
    FACES_DIR.mkdir(parents=True, exist_ok=True)
    detected, total = 0, 0
    for video_dir in FRAMES_DIR.iterdir():
        out_dir = FACES_DIR / video_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for jpg in sorted(video_dir.glob("*.jpg")):
            total += 1
            img = Image.open(jpg).convert("RGB")
            face = mtcnn(img)
            if face is not None:
                detected += 1
                import torchvision.transforms.functional as TF
                TF.to_pil_image(((face + 1) / 2).clamp(0, 1)).save(out_dir / jpg.name)
            else:
                import shutil
                shutil.copy(jpg, out_dir / jpg.name)
    logger.info(f"Face detection: {detected}/{total} detected")


def compute_features():
    """Extract EfficientNet-B0 features from face crops."""
    model = EfficientNet.from_pretrained("efficientnet-b0")
    model._fc = torch.nn.Identity()
    model.eval()
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        for video_dir in FACES_DIR.iterdir():
            tensors = [transform(Image.open(j).convert("RGB"))
                       for j in sorted(video_dir.glob("*.jpg"))]
            if tensors:
                feats = model(torch.stack(tensors))
                torch.save(feats, FEATURES_DIR / f"{video_dir.name}.pt")
    logger.info("Feature extraction complete")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else ""
    if stage == "extract_frames":
        extract_frames()
    elif stage == "detect_faces":
        detect_faces()
    elif stage == "compute_features":
        compute_features()
    else:
        print(f"Unknown stage: {stage}. Use: extract_frames | detect_faces | compute_features")
        sys.exit(1)
```

- [ ] **Step 4: Commit**
```bash
git add ml/dvc.yaml ml/drift_baseline.py ml/preprocessing_pipeline.py
git commit -m "feat(ml): add DVC pipeline DAG, drift baseline, and preprocessing pipeline script"
```

---

## Phase 3: Backend

### Task 7: Backend Scaffold + Schemas

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/schemas.py`
- Create: `backend/app/logging_config.py`
- Create: `tests/unit/test_schemas.py`

- [ ] **Step 1: Write failing test**
```python
# tests/unit/test_schemas.py
from backend.app.schemas import PredictResponse, HealthResponse

def test_predict_response_fields():
    r = PredictResponse(
        prediction="fake",
        confidence=0.94,
        inference_latency_ms=143,
        gradcam_image="base64string",
        mlflow_run_id="abc123",
        frames_analyzed=30,
    )
    assert r.prediction in ("real", "fake")
    assert 0.0 <= r.confidence <= 1.0

def test_health_response():
    r = HealthResponse(status="ok", model_loaded=True)
    assert r.status == "ok"
```

- [ ] **Step 2: Run — expect FAIL**
```bash
pytest tests/unit/test_schemas.py -v
```

- [ ] **Step 3: Create `backend/app/schemas.py`**
```python
"""Pydantic request/response models for all API endpoints."""
from pydantic import BaseModel, Field


class PredictResponse(BaseModel):
    """Response from POST /predict."""
    prediction: str = Field(..., description="'real' or 'fake'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    inference_latency_ms: float
    gradcam_image: str = Field(..., description="Base64-encoded Grad-CAM PNG")
    mlflow_run_id: str
    frames_analyzed: int


class HealthResponse(BaseModel):
    """Response from GET /health."""
    status: str
    model_loaded: bool


class ReadyResponse(BaseModel):
    """Response from GET /ready."""
    status: str
    model_version: str


class ReloadResponse(BaseModel):
    """Response from POST /admin/reload-model."""
    status: str
    model_version: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str
```

- [ ] **Step 4: Create `backend/app/logging_config.py`**
```python
"""Structured JSON logging configuration for all backend modules."""
import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger to emit structured JSON to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
```

- [ ] **Step 5: Create `backend/requirements.txt`**
```
fastapi==0.110.0
uvicorn[standard]==0.27.1
python-multipart==0.0.9
pydantic==2.6.3
mlflow==2.11.1
torch==2.2.1
torchvision==0.17.1
efficientnet-pytorch==0.7.1
facenet-pytorch==2.5.3
opencv-python-headless==4.9.0.80
numpy==1.26.4
prometheus-client==0.20.0
python-json-logger==2.0.7
httpx==0.27.0
Pillow==10.2.0
```

- [ ] **Step 6: Create `backend/requirements-dev.txt`**
```
pytest==8.1.0
pytest-asyncio==0.23.5
httpx==0.27.0
black==24.3.0
flake8==7.0.0
isort==5.13.2
```

- [ ] **Step 7: Run test — expect PASS**
```bash
pytest tests/unit/test_schemas.py -v
```

- [ ] **Step 8: Commit**
```bash
git add backend/app/schemas.py backend/app/logging_config.py backend/requirements.txt backend/requirements-dev.txt tests/unit/test_schemas.py
git commit -m "feat(backend): add Pydantic schemas and structured JSON logging"
```

---

### Task 8: Preprocessing (MP4 → frames → faces)

**Files:**
- Create: `backend/app/preprocessing.py`
- Create: `tests/unit/test_preprocessing.py`

- [ ] **Step 1: Write failing tests**
```python
# tests/unit/test_preprocessing.py
import torch
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from backend.app.preprocessing import extract_frames, preprocess_video

def test_extract_frames_returns_list():
    """extract_frames should return a list of numpy arrays."""
    # Mock cv2.VideoCapture
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 30.0  # fps
    mock_cap.read.side_effect = [
        (True, np.zeros((480, 640, 3), dtype=np.uint8))
    ] * 30 + [(False, None)]

    with patch("backend.app.preprocessing.cv2.VideoCapture", return_value=mock_cap):
        frames = extract_frames("/fake/video.mp4", num_frames=10)

    assert isinstance(frames, list)
    assert len(frames) <= 10

def test_preprocess_video_output_shape():
    """preprocess_video should return tensor (num_frames, 3, 224, 224)."""
    fake_frames = [np.zeros((224, 224, 3), dtype=np.uint8)] * 30
    with patch("backend.app.preprocessing.extract_frames", return_value=fake_frames):
        with patch("backend.app.preprocessing.detect_faces", return_value=fake_frames):
            result = preprocess_video("/fake/video.mp4", num_frames=30)
    assert isinstance(result, torch.Tensor)
    assert result.shape == (30, 3, 224, 224)
```

- [ ] **Step 2: Run — expect FAIL**
```bash
pytest tests/unit/test_preprocessing.py -v
```

- [ ] **Step 3: Create `backend/app/preprocessing.py`**
```python
"""Video preprocessing: MP4 → sampled frames → MTCNN face crops → tensors."""
import logging
import tempfile
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN
from PIL import Image
from torchvision import transforms

logger = logging.getLogger(__name__)

FRAME_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

_mtcnn: Optional[MTCNN] = None


def get_mtcnn() -> MTCNN:
    """Lazy-load MTCNN face detector (singleton)."""
    global _mtcnn
    if _mtcnn is None:
        _mtcnn = MTCNN(
            image_size=224,
            margin=20,
            keep_all=False,
            device="cpu",
        )
    return _mtcnn


def extract_frames(video_path: str, num_frames: int = 30) -> List[np.ndarray]:
    """Sample num_frames evenly from an MP4 video.

    Args:
        video_path: Path to .mp4 file
        num_frames: Number of frames to sample

    Returns:
        List of BGR numpy arrays (H, W, 3)

    Raises:
        ValueError: If video cannot be opened or has no frames
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        raise ValueError(f"Video has no frames: {video_path}")

    indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    cap.release()

    if not frames:
        raise ValueError(f"Could not extract frames from {video_path}")

    logger.info("extracted_frames", extra={"count": len(frames), "path": video_path})
    return frames


def detect_faces(frames: List[np.ndarray]) -> List[np.ndarray]:
    """Run MTCNN face detection on each frame.

    Falls back to resized original frame if no face detected.

    Args:
        frames: List of BGR numpy arrays

    Returns:
        List of RGB numpy arrays (224, 224, 3)
    """
    mtcnn = get_mtcnn()
    face_crops = []
    detected = 0

    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        face_tensor = mtcnn(pil_img)

        if face_tensor is not None:
            # Convert back to numpy (C,H,W) → (H,W,C), unnormalize
            face_np = face_tensor.permute(1, 2, 0).numpy()
            face_np = ((face_np * 128) + 127.5).clip(0, 255).astype(np.uint8)
            face_crops.append(face_np)
            detected += 1
        else:
            # Fallback: resize full frame
            fallback = cv2.resize(rgb, (224, 224))
            face_crops.append(fallback)

    logger.info("face_detection", extra={
        "detected": detected, "total": len(frames),
        "detection_rate": detected / len(frames) if frames else 0
    })
    return face_crops


def preprocess_video(video_path: str, num_frames: int = 30) -> torch.Tensor:
    """Full preprocessing pipeline: MP4 → tensor ready for model.

    Args:
        video_path: Path to .mp4 file
        num_frames: Number of frames to use

    Returns:
        Tensor of shape (num_frames, 3, 224, 224)
    """
    frames = extract_frames(video_path, num_frames)
    face_crops = detect_faces(frames)

    tensors = []
    for crop in face_crops:
        pil = Image.fromarray(crop.astype(np.uint8))
        tensors.append(FRAME_TRANSFORM(pil))

    # Pad if fewer frames extracted than requested
    while len(tensors) < num_frames:
        tensors.append(tensors[-1].clone())

    return torch.stack(tensors[:num_frames])
```

- [ ] **Step 4: Run tests — expect PASS**
```bash
pytest tests/unit/test_preprocessing.py -v
```

- [ ] **Step 5: Commit**
```bash
git add backend/app/preprocessing.py tests/unit/test_preprocessing.py
git commit -m "feat(backend): add MP4 preprocessing with MTCNN face detection"
```

---

### Task 9: Model Loader + Metrics + Drift Detector

**Files:**
- Create: `backend/app/model_loader.py`
- Create: `backend/app/metrics.py`
- Create: `backend/app/drift_detector.py`
- Create: `tests/unit/test_drift_detector.py`

- [ ] **Step 1: Write failing test**
```python
# tests/unit/test_drift_detector.py
import numpy as np
import pytest
from unittest.mock import patch
from backend.app.drift_detector import compute_drift_score, is_drifted

MOCK_BASELINE = {
    "mean": [0.5] * 10,
    "std": [0.1] * 10,
}

def test_no_drift_within_threshold():
    features = np.array([0.5] * 10)
    score = compute_drift_score(features, MOCK_BASELINE)
    assert score < 1.0  # within 1 std → low drift

def test_drift_detected_far_from_mean():
    features = np.array([5.0] * 10)  # 45 std devs from mean
    score = compute_drift_score(features, MOCK_BASELINE)
    assert score > 3.0

def test_is_drifted_threshold():
    assert is_drifted(4.0, threshold=3.0) is True
    assert is_drifted(1.0, threshold=3.0) is False
```

- [ ] **Step 2: Run — expect FAIL**
```bash
pytest tests/unit/test_drift_detector.py -v
```

- [ ] **Step 3: Create `backend/app/drift_detector.py`**
```python
"""Feature drift detection: compare incoming features against stored baseline."""
import logging
from pathlib import Path
from typing import Optional
import json
import numpy as np

logger = logging.getLogger(__name__)

BASELINE_PATH = Path("ml/feature_baseline.json")
DEFAULT_DRIFT_THRESHOLD = 3.0  # z-score threshold


def load_baseline() -> Optional[dict]:
    """Load baseline statistics. Returns None if baseline not found."""
    if not BASELINE_PATH.exists():
        logger.warning("drift_baseline_not_found", extra={"path": str(BASELINE_PATH)})
        return None
    return json.loads(BASELINE_PATH.read_text())


def compute_drift_score(features: np.ndarray, baseline: dict) -> float:
    """Compute mean absolute z-score between features and baseline.

    Args:
        features: 1-D feature vector from current inference
        baseline: dict with 'mean' and 'std' keys (lists of floats)

    Returns:
        Mean absolute z-score across all dimensions
    """
    mean = np.array(baseline["mean"])
    std = np.array(baseline["std"])
    std = np.where(std == 0, 1e-8, std)  # avoid division by zero
    z_scores = np.abs((features - mean) / std)
    return float(z_scores.mean())


def is_drifted(drift_score: float, threshold: float = DEFAULT_DRIFT_THRESHOLD) -> bool:
    """Return True if drift score exceeds threshold."""
    return drift_score > threshold
```

- [ ] **Step 4: Create `backend/app/metrics.py`**
```python
"""Prometheus metrics definitions for the backend service."""
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    "deepfake_requests_total",
    "Total prediction requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "deepfake_request_latency_seconds",
    "Request latency",
    ["endpoint"],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
)

# Model metrics
INFERENCE_LATENCY = Histogram(
    "deepfake_inference_latency_ms",
    "Model inference latency in milliseconds",
    buckets=[10, 25, 50, 100, 200, 500, 1000],
)
CONFIDENCE_SCORE = Histogram(
    "deepfake_confidence_score",
    "Model confidence score distribution",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)
PREDICTION_COUNTER = Counter(
    "deepfake_predictions_total",
    "Total predictions by label",
    ["label"],
)

# Drift metrics
DRIFT_SCORE = Gauge(
    "deepfake_drift_score",
    "Current feature drift z-score",
)
DRIFT_DETECTED = Counter(
    "deepfake_drift_detected_total",
    "Number of requests where drift was detected",
)

# Pipeline validation failures (also scraped from Airflow, but tracked here too)
PIPELINE_VALIDATION_FAILURES = Counter(
    "pipeline_validation_failures_total",
    "Number of data pipeline schema validation failures",
)
```

- [ ] **Step 5: Create `backend/app/model_loader.py`**
```python
"""Load and reload model from MLflow Model Registry."""
import logging
import os
from typing import Optional

import mlflow.pyfunc

logger = logging.getLogger(__name__)

_model = None
_current_version: str = "unknown"


def load_model() -> None:
    """Load Production model from MLflow registry into module-level singleton."""
    global _model, _current_version
    model_name = os.getenv("MODEL_NAME", "deepfake")
    model_stage = os.getenv("MODEL_STAGE", "Production")
    model_uri = f"models:/{model_name}/{model_stage}"

    logger.info("loading_model", extra={"uri": model_uri})
    _model = mlflow.pyfunc.load_model(model_uri)
    _current_version = f"{model_name}/{model_stage}"
    logger.info("model_loaded", extra={"version": _current_version})


def get_model():
    """Return loaded model. Raises RuntimeError if not loaded."""
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")
    return _model


def get_model_version() -> str:
    """Return current model version string."""
    return _current_version


def is_model_loaded() -> bool:
    """Return True if model is loaded."""
    return _model is not None


def reload_model() -> str:
    """Force reload model from registry. Returns new version string."""
    load_model()
    return _current_version
```

- [ ] **Step 6: Run drift tests — expect PASS**
```bash
pytest tests/unit/test_drift_detector.py -v
```

- [ ] **Step 7: Commit**
```bash
git add backend/app/model_loader.py backend/app/metrics.py backend/app/drift_detector.py tests/unit/test_drift_detector.py
git commit -m "feat(backend): add model loader, Prometheus metrics, and drift detector"
```

---

### Task 10: Explainability (Grad-CAM)

**Files:**
- Create: `backend/app/explainability.py`

- [ ] **Step 1: Create `backend/app/explainability.py`**
```python
"""Grad-CAM heatmap generation for model explainability."""
import base64
import io
import logging
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

logger = logging.getLogger(__name__)


def generate_gradcam(
    model: torch.nn.Module,
    frames_tensor: torch.Tensor,
    target_layer_name: str = "cnn._blocks",
) -> Optional[str]:
    """Generate Grad-CAM heatmap for the most influential frame.

    Args:
        model: DeepfakeDetector model
        frames_tensor: Tensor of shape (num_frames, 3, 224, 224)
        target_layer_name: Name of the CNN layer to hook

    Returns:
        Base64-encoded PNG of Grad-CAM overlay, or None on failure
    """
    try:
        model.eval()
        input_tensor = frames_tensor.unsqueeze(0)  # (1, F, 3, 224, 224)

        # Hook the last EfficientNet block
        gradients = []
        activations = []

        def forward_hook(module, input, output):
            activations.append(output)

        def backward_hook(module, grad_in, grad_out):
            gradients.append(grad_out[0])

        # Find target layer
        target_layer = None
        for name, module in model.cnn.named_modules():
            if name.startswith("_blocks"):
                target_layer = module  # Will end up with the last block

        if target_layer is None:
            logger.warning("gradcam_target_layer_not_found")
            return None

        fwd_handle = target_layer.register_forward_hook(forward_hook)
        bwd_handle = target_layer.register_backward_hook(backward_hook)

        output = model(input_tensor)
        model.zero_grad()
        output.backward()

        fwd_handle.remove()
        bwd_handle.remove()

        if not gradients or not activations:
            return None

        # Pool gradients and weight activations
        pooled_gradients = gradients[0].mean(dim=[0, 2, 3])
        activation = activations[0][0]
        for i in range(activation.shape[0]):
            activation[i, :, :] *= pooled_gradients[i]

        heatmap = activation.mean(dim=0).detach().cpu().numpy()
        heatmap = np.maximum(heatmap, 0)
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)

        # Overlay on middle frame
        mid_frame = frames_tensor[len(frames_tensor) // 2]
        frame_np = mid_frame.permute(1, 2, 0).cpu().numpy()
        frame_np = (frame_np * np.array([0.229, 0.224, 0.225]) +
                    np.array([0.485, 0.456, 0.406]))
        frame_np = (frame_np * 255).clip(0, 255).astype(np.uint8)

        heatmap_resized = np.array(
            Image.fromarray((heatmap * 255).astype(np.uint8)).resize((224, 224))
        )
        overlay = frame_np.copy()
        overlay[:, :, 0] = np.clip(
            overlay[:, :, 0].astype(int) + heatmap_resized.astype(int) // 2, 0, 255
        )

        # Encode to base64
        pil_img = Image.fromarray(overlay)
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    except Exception as e:
        logger.error("gradcam_failed", extra={"error": str(e)})
        return ""
```

- [ ] **Step 2: Commit**
```bash
git add backend/app/explainability.py
git commit -m "feat(backend): add Grad-CAM explainability"
```

---

### Task 11: FastAPI App + Router

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/predict.py`
- Create: `backend/app/feedback_logger.py`
- Create: `backend/Dockerfile`
- Create: `tests/integration/test_predict_endpoint.py`
- Create: `tests/integration/test_health_endpoints.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `backend/app/feedback_logger.py`**
```python
"""Log ground-truth labels for model performance tracking over time."""
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
FEEDBACK_LOG = Path("data/feedback/feedback_log.jsonl")


def log_feedback(request_id: str, predicted: str, ground_truth: str) -> None:
    """Append a ground-truth label entry to the feedback log.

    Args:
        request_id: Unique identifier for the original prediction
        predicted: Model prediction ('real' or 'fake')
        ground_truth: Actual label provided by user/system
    """
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "predicted": predicted,
        "ground_truth": ground_truth,
        "correct": predicted == ground_truth,
    }
    with FEEDBACK_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    logger.info("feedback_logged", extra=entry)
```

- [ ] **Step 2: Create `backend/app/routers/predict.py`**
```python
"""Prediction, health, ready, metrics, and admin endpoints."""
import logging
import time
import uuid
from typing import Optional

import torch
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import tempfile

from backend.app import model_loader, explainability
from backend.app.drift_detector import compute_drift_score, is_drifted, load_baseline
from backend.app.metrics import (
    REQUEST_COUNT, REQUEST_LATENCY, INFERENCE_LATENCY,
    CONFIDENCE_SCORE, PREDICTION_COUNTER, DRIFT_SCORE, DRIFT_DETECTED
)
from backend.app.preprocessing import preprocess_video
from backend.app.schemas import (
    PredictResponse, HealthResponse, ReadyResponse, ReloadResponse, ErrorResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    """Accept an MP4 video and return real/fake prediction with Grad-CAM."""
    request_id = str(uuid.uuid4())
    start = time.time()

    try:
        if not file.filename.endswith(".mp4"):
            raise HTTPException(status_code=400, detail="Only MP4 files are accepted")

        # Save upload to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Preprocess
        frames_tensor = preprocess_video(tmp_path)

        # Inference via MLflow model server
        infer_start = time.time()
        model = model_loader.get_model()

        import numpy as np
        input_data = frames_tensor.unsqueeze(0).numpy()
        result = model.predict(input_data)
        confidence = float(result[0][0])
        infer_ms = (time.time() - infer_start) * 1000

        prediction = "fake" if confidence >= 0.5 else "real"

        # Drift detection
        feature_vec = frames_tensor.mean(dim=(0, 2, 3)).numpy()
        baseline = load_baseline()
        drift_score = 0.0
        if baseline:
            drift_score = compute_drift_score(feature_vec, baseline)
            DRIFT_SCORE.set(drift_score)
            if is_drifted(drift_score):
                DRIFT_DETECTED.inc()
                logger.warning("drift_detected", extra={
                    "score": drift_score, "request_id": request_id
                })

        # Grad-CAM
        gradcam_b64 = explainability.generate_gradcam(
            model_loader.get_model()._model_impl.python_model.model,
            frames_tensor,
        ) or ""

        # Metrics
        INFERENCE_LATENCY.observe(infer_ms)
        CONFIDENCE_SCORE.observe(confidence)
        PREDICTION_COUNTER.labels(label=prediction).inc()
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="200").inc()
        REQUEST_LATENCY.labels(endpoint="/predict").observe(time.time() - start)

        logger.info("prediction_complete", extra={
            "request_id": request_id, "prediction": prediction,
            "confidence": confidence, "infer_ms": infer_ms,
            "drift_score": drift_score,
        })

        return PredictResponse(
            prediction=prediction,
            confidence=confidence,
            inference_latency_ms=infer_ms,
            gradcam_image=gradcam_b64,
            mlflow_run_id=request_id,
            frames_analyzed=frames_tensor.shape[0],
        )

    except HTTPException:
        raise
    except Exception as e:
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="500").inc()
        logger.error("prediction_failed", extra={"error": str(e), "request_id": request_id})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
def health():
    """Liveness check."""
    return HealthResponse(status="ok", model_loaded=model_loader.is_model_loaded())


@router.get("/ready", response_model=ReadyResponse)
def ready():
    """Readiness check — fails if model not loaded."""
    if not model_loader.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    return ReadyResponse(status="ready", model_version=model_loader.get_model_version())


@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.post("/admin/reload-model", response_model=ReloadResponse)
def reload_model():
    """Force reload model from MLflow registry (used during rollback)."""
    try:
        version = model_loader.reload_model()
        logger.info("model_reloaded", extra={"version": version})
        return ReloadResponse(status="reloaded", model_version=version)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: Create `backend/app/main.py`**
```python
"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.logging_config import setup_logging
from backend.app.model_loader import load_model
from backend.app.routers.predict import router
from backend.app.routers.pipeline import pipeline_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup."""
    setup_logging()
    load_model()
    yield


app = FastAPI(
    title="Deepfake Detection API",
    description="Classify MP4 videos as real or fake using CNN+LSTM model",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(pipeline_router, prefix="/pipeline")
```

- [ ] **Step 4: Create `tests/conftest.py`**
```python
"""Shared pytest fixtures."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import torch
import io


@pytest.fixture
def client():
    """Test client with model loading mocked."""
    with patch("backend.app.model_loader.load_model"):
        with patch("backend.app.model_loader._model", MagicMock()):
            with patch("backend.app.model_loader._current_version", "deepfake/Production/1"):
                from backend.app.main import app
                return TestClient(app)


@pytest.fixture
def sample_mp4_bytes():
    """Minimal valid MP4-like bytes for upload tests."""
    # 8-byte ftyp box — enough to pass filename check
    return b"\x00\x00\x00\x08ftyp" + b"\x00" * 100


@pytest.fixture
def mock_frames_tensor():
    return torch.randn(30, 3, 224, 224)
```

- [ ] **Step 5: Create `tests/integration/test_health_endpoints.py`**
```python
# tests/integration/test_health_endpoints.py
def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"

def test_ready(client):
    resp = client.get("/ready")
    assert resp.status_code in (200, 503)

def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"deepfake_requests_total" in resp.content
```

- [ ] **Step 6: Create `tests/integration/test_predict_endpoint.py`**
```python
# tests/integration/test_predict_endpoint.py
import io
import torch
import numpy as np
from unittest.mock import patch, MagicMock


def test_predict_rejects_non_mp4(client):
    resp = client.post("/predict", files={"file": ("test.avi", b"fakecontent", "video/x-msvideo")})
    assert resp.status_code == 400


def test_predict_returns_valid_schema(client, mock_frames_tensor, sample_mp4_bytes):
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.85]])

    with patch("backend.app.routers.predict.preprocess_video", return_value=mock_frames_tensor):
        with patch("backend.app.model_loader.get_model", return_value=mock_model):
            with patch("backend.app.routers.predict.explainability.generate_gradcam", return_value="base64img"):
                resp = client.post(
                    "/predict",
                    files={"file": ("test.mp4", sample_mp4_bytes, "video/mp4")},
                )

    assert resp.status_code == 200
    data = resp.json()
    assert data["prediction"] in ("real", "fake")
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["frames_analyzed"] == 30
```

- [ ] **Step 7: Run integration tests**
```bash
pytest tests/integration/ -v
# Expected: all pass
```

- [ ] **Step 8: Create `backend/Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 9: Commit**
```bash
git add backend/app/ backend/Dockerfile tests/
git commit -m "feat(backend): add FastAPI app with all endpoints, middleware, and integration tests"
```

---

## Phase 4: Airflow Data Pipeline

### Task 12: Airflow DAGs

**Files:**
- Create: `airflow/dags/deepfake_pipeline.py`
- Create: `airflow/dags/retraining_dag.py`

- [ ] **Step 1: Create `airflow/dags/deepfake_pipeline.py`**
```python
"""Data ingestion and preprocessing DAG.

Pipeline: ingest_videos → extract_frames → detect_faces →
          compute_features → validate_schema → record_baseline_stats → version_with_dvc
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "mlops",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

DATA_PATH = Path("/opt/airflow/data")


def ingest_videos(**context):
    """Move raw MP4s from landing zone to data/raw/."""
    landing = DATA_PATH / "landing"
    raw = DATA_PATH / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    files = list(landing.glob("*.mp4")) if landing.exists() else []
    for f in files:
        f.rename(raw / f.name)
    logger.info(f"Ingested {len(files)} videos")
    context["ti"].xcom_push(key="video_count", value=len(files))


def extract_frames(**context):
    """Extract sampled frames from each MP4."""
    import cv2
    import numpy as np
    raw = DATA_PATH / "raw"
    frames_dir = DATA_PATH / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for mp4 in raw.glob("*.mp4"):
        cap = cv2.VideoCapture(str(mp4))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        indices = np.linspace(0, total - 1, 30, dtype=int)
        out_dir = frames_dir / mp4.stem
        out_dir.mkdir(exist_ok=True)
        for i, idx in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(str(out_dir / f"frame_{i:03d}.jpg"), frame)
                count += 1
        cap.release()
    logger.info(f"Extracted {count} frames total")


def detect_faces(**context):
    """Run MTCNN face detection on extracted frames."""
    from facenet_pytorch import MTCNN
    from PIL import Image
    import cv2
    mtcnn = MTCNN(image_size=224, margin=20, keep_all=False, device="cpu")
    frames_dir = DATA_PATH / "frames"
    faces_dir = DATA_PATH / "faces"
    detected, total = 0, 0
    for video_dir in frames_dir.iterdir():
        out_dir = faces_dir / video_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for jpg in video_dir.glob("*.jpg"):
            total += 1
            img = Image.open(jpg).convert("RGB")
            face = mtcnn(img)
            if face is not None:
                detected += 1
                out_path = out_dir / jpg.name
                import torchvision.transforms.functional as TF
                TF.to_pil_image(((face + 1) / 2).clamp(0, 1)).save(out_path)
            else:
                import shutil
                shutil.copy(jpg, out_dir / jpg.name)
    logger.info(f"Face detection rate: {detected}/{total}")


def compute_features(**context):
    """Extract EfficientNet features from face crops."""
    import torch
    from efficientnet_pytorch import EfficientNet
    from torchvision import transforms
    from PIL import Image
    model = EfficientNet.from_pretrained("efficientnet-b0")
    model._fc = torch.nn.Identity()
    model.eval()
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    faces_dir = DATA_PATH / "faces"
    features_dir = DATA_PATH / "features"
    with torch.no_grad():
        for video_dir in faces_dir.iterdir():
            tensors = []
            for jpg in sorted(video_dir.glob("*.jpg")):
                img = Image.open(jpg).convert("RGB")
                tensors.append(transform(img))
            if tensors:
                batch = torch.stack(tensors)
                feats = model(batch)
                out = features_dir / video_dir.name
                out.parent.mkdir(parents=True, exist_ok=True)
                torch.save(feats, str(out) + ".pt")


def validate_schema(**context):
    """Validate feature tensors: shape, dtype, value range, no NaN."""
    import torch
    features_dir = DATA_PATH / "features"
    failures = 0
    for pt_file in features_dir.rglob("*.pt"):
        tensor = torch.load(pt_file)
        errors = []
        if tensor.ndim != 2:
            errors.append(f"Expected 2D tensor, got {tensor.ndim}D")
        if tensor.dtype != torch.float32:
            errors.append(f"Expected float32, got {tensor.dtype}")
        if torch.isnan(tensor).any():
            errors.append("NaN values found")
        if tensor.min() < -10 or tensor.max() > 10:
            errors.append(f"Values out of expected range: [{tensor.min():.2f}, {tensor.max():.2f}]")
        if errors:
            failures += 1
            logger.error(f"Validation failed for {pt_file}: {errors}")

    if failures > 0:
        # Increment Prometheus counter via push gateway (Airflow has no scrape endpoint)
        try:
            from prometheus_client import CollectorRegistry, Counter, push_to_gateway
            reg = CollectorRegistry()
            c = Counter("pipeline_validation_failures_total",
                        "Pipeline schema validation failures", registry=reg)
            c.inc(failures)
            push_to_gateway("prometheus:9091", job="airflow", registry=reg)
        except Exception as prom_err:
            logger.warning(f"Could not push Prometheus metric: {prom_err}")
        from airflow.exceptions import AirflowException
        raise AirflowException(
            f"Schema validation failed for {failures} files. DAG halted."
        )
    logger.info("Schema validation passed for all feature files")


def record_baseline_stats(**context):
    """Compute and save feature baseline statistics."""
    import sys
    sys.path.insert(0, "/opt/airflow")
    from ml.drift_baseline import compute_baseline
    compute_baseline(str(DATA_PATH / "features"))


def version_with_dvc(**context):
    """Run dvc add on data directories to version artifacts."""
    import subprocess
    for directory in ["data/raw", "data/frames", "data/faces", "data/features"]:
        subprocess.run(["dvc", "add", directory], check=False)
    logger.info("DVC versioning complete")


with DAG(
    dag_id="deepfake_pipeline",
    default_args=DEFAULT_ARGS,
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["deepfake", "data-pipeline"],
) as dag:

    t1 = PythonOperator(task_id="ingest_videos", python_callable=ingest_videos)
    t2 = PythonOperator(task_id="extract_frames", python_callable=extract_frames)
    t3 = PythonOperator(task_id="detect_faces", python_callable=detect_faces)
    t4 = PythonOperator(task_id="compute_features", python_callable=compute_features)
    t5 = PythonOperator(task_id="validate_schema", python_callable=validate_schema)
    t6 = PythonOperator(task_id="record_baseline_stats", python_callable=record_baseline_stats)
    t7 = PythonOperator(task_id="version_with_dvc", python_callable=version_with_dvc)

    t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7
```

- [ ] **Step 2: Create `airflow/dags/retraining_dag.py`**
```python
"""Automated retraining DAG — triggered by drift detection or schedule.

Pipeline: check_drift → fetch_new_data → run_mlproject →
          evaluate_model → register_if_better → promote_to_production
"""
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "mlops",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

DRIFT_THRESHOLD = 3.0


def check_drift(**context):
    """Read latest drift score from Prometheus. Return branch decision."""
    import json
    from pathlib import Path
    baseline_path = Path("/opt/airflow/ml/feature_baseline.json")
    if not baseline_path.exists():
        return "skip_retraining"
    # In production, query Prometheus API for current drift gauge
    # For now, check if baseline is stale (>7 days)
    age_days = (datetime.now().timestamp() - baseline_path.stat().st_mtime) / 86400
    return "fetch_new_data" if age_days > 7 else "skip_retraining"


def fetch_new_data(**context):
    """Trigger deepfake_pipeline DAG to ingest fresh data."""
    from airflow.api.client.local_client import Client
    c = Client(None, None)
    c.trigger_dag("deepfake_pipeline")


def run_mlproject(**context):
    """Run MLflow project training entry point."""
    import subprocess
    result = subprocess.run(
        ["mlflow", "run", ".", "-e", "train"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"MLflow run failed: {result.stderr}")
    # Extract run_id from output
    for line in result.stdout.split("\n"):
        if "Run ID:" in line:
            run_id = line.split("Run ID:")[-1].strip()
            context["ti"].xcom_push(key="run_id", value=run_id)


def evaluate_model(**context):
    """Compare new model metrics against current Production model."""
    import mlflow
    run_id = context["ti"].xcom_pull(key="run_id", task_ids="run_mlproject")
    client = mlflow.tracking.MlflowClient()
    run = client.get_run(run_id)
    new_f1 = run.data.metrics.get("val_f1", 0)
    context["ti"].xcom_push(key="new_f1", value=new_f1)
    context["ti"].xcom_push(key="run_id", value=run_id)


def register_if_better(**context):
    """Register new model version to Staging if it outperforms threshold."""
    import mlflow
    new_f1 = context["ti"].xcom_pull(key="new_f1", task_ids="evaluate_model")
    run_id = context["ti"].xcom_pull(key="run_id", task_ids="evaluate_model")
    if new_f1 < 0.9:
        from airflow.exceptions import AirflowException
        raise AirflowException(
            f"New model F1 {new_f1:.4f} < 0.90 threshold, not registering"
        )
    # Register and transition to Staging so promote_to_production can find it
    model_uri = f"runs:/{run_id}/model"
    result = mlflow.register_model(model_uri, "deepfake")
    client = mlflow.tracking.MlflowClient()
    client.transition_model_version_stage(
        name="deepfake",
        version=result.version,
        stage="Staging",
    )
    logger.info(f"Registered version {result.version} to Staging (F1={new_f1:.4f})")


def promote_to_production(**context):
    """Transition new model version to Production in MLflow registry."""
    import mlflow
    client = mlflow.tracking.MlflowClient()
    versions = client.get_latest_versions("deepfake", stages=["Staging"])
    if versions:
        client.transition_model_version_stage(
            name="deepfake",
            version=versions[0].version,
            stage="Production",
            archive_existing_versions=True,
        )
        logger.info(f"Promoted version {versions[0].version} to Production")


with DAG(
    dag_id="retraining_dag",
    default_args=DEFAULT_ARGS,
    schedule_interval="@weekly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["deepfake", "retraining"],
) as dag:

    check = BranchPythonOperator(task_id="check_drift", python_callable=check_drift)
    skip = DummyOperator(task_id="skip_retraining")
    fetch = PythonOperator(task_id="fetch_new_data", python_callable=fetch_new_data)
    run = PythonOperator(task_id="run_mlproject", python_callable=run_mlproject)
    evaluate = PythonOperator(task_id="evaluate_model", python_callable=evaluate_model)
    register = PythonOperator(task_id="register_if_better", python_callable=register_if_better)
    promote = PythonOperator(task_id="promote_to_production", python_callable=promote_to_production)

    check >> [fetch, skip]
    fetch >> run >> evaluate >> register >> promote
```

- [ ] **Step 3: Commit**
```bash
git add airflow/dags/
git commit -m "feat(airflow): add data pipeline DAG and automated retraining DAG"
```

---

## Phase 5: Monitoring

### Task 13: Prometheus + Grafana Config

**Files:**
- Create: `monitoring/prometheus.yml`
- Create: `monitoring/alert_rules.yml`
- Create: `monitoring/grafana/provisioning/datasources/prometheus.yml`
- Create: `monitoring/grafana/provisioning/dashboards/dashboards.yml`
- Create: `monitoring/grafana/dashboards/inference.json`

- [ ] **Step 1: Create `monitoring/prometheus.yml`**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/alert_rules.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets: []  # Configure Alertmanager URL if needed

scrape_configs:
  - job_name: backend
    static_configs:
      - targets: ["backend:8000"]
    metrics_path: /metrics

  - job_name: airflow
    static_configs:
      - targets: ["airflow-webserver:8080"]
    metrics_path: /admin/metrics

  - job_name: mlflow
    static_configs:
      - targets: ["mlflow-server:5000"]
    metrics_path: /metrics

  - job_name: nginx
    static_configs:
      - targets: ["frontend:9113"]
    metrics_path: /metrics
```

- [ ] **Step 2: Create `monitoring/alert_rules.yml`**
```yaml
groups:
  - name: deepfake_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          rate(deepfake_requests_total{status="500"}[5m]) /
          rate(deepfake_requests_total[5m]) > 0.05
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Error rate > 5% for 3 minutes"
          description: "Backend error rate is {{ $value | humanizePercentage }}"

      - alert: HighInferenceLatency
        expr: |
          histogram_quantile(0.95, rate(deepfake_inference_latency_ms_bucket[5m])) > 200
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "P95 inference latency > 200ms"

      - alert: FeatureDriftDetected
        expr: deepfake_drift_score > 3.0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Feature drift detected — retraining may be needed"
          description: "Drift score: {{ $value }}"

      - alert: PipelineValidationFailure
        expr: increase(pipeline_validation_failures_total[1h]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Data pipeline schema validation failure"
```

- [ ] **Step 3: Create Grafana provisioning files**
```bash
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards
```

`monitoring/grafana/provisioning/datasources/prometheus.yml`:
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
    access: proxy
```

`monitoring/grafana/provisioning/dashboards/dashboards.yml`:
```yaml
apiVersion: 1
providers:
  - name: Default
    folder: Deepfake Detection
    type: file
    options:
      path: /var/lib/grafana/dashboards
```

- [ ] **Step 4: Commit**
```bash
git add monitoring/
git commit -m "feat(monitoring): add Prometheus scrape config, alert rules, and Grafana provisioning"
```

---

## Phase 6: Frontend

### Task 14: React App Setup

**Files:**
- Create: `frontend/` (Vite + React + TypeScript)
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/components/VideoUpload.tsx`
- Create: `frontend/src/components/ResultCard.tsx`
- Create: `frontend/src/components/ErrorConsole.tsx`
- Create: `frontend/src/pages/Home.tsx`
- Create: `frontend/src/pages/PipelineDashboard.tsx`
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`

- [ ] **Step 1: Scaffold Vite React TypeScript app**
```bash
cd deepfake-detection
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
npm install axios react-router-dom @types/react-router-dom
```

- [ ] **Step 2: Create `frontend/src/api/client.ts`**
```typescript
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "/api";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

export interface PredictResponse {
  prediction: "real" | "fake";
  confidence: number;
  inference_latency_ms: number;
  gradcam_image: string;
  mlflow_run_id: string;
  frames_analyzed: number;
}

export const predictVideo = async (file: File): Promise<PredictResponse> => {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<PredictResponse>("/predict", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};
```

- [ ] **Step 3: Create `frontend/src/components/VideoUpload.tsx`**
```tsx
import React, { useCallback, useState } from "react";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export const VideoUpload: React.FC<Props> = ({ onFile, disabled }) => {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = (file: File): string | null => {
    if (!file.name.endsWith(".mp4")) return "Only MP4 files are accepted.";
    if (file.size > 100 * 1024 * 1024) return "File must be under 100MB.";
    return null;
  };

  const handleFile = useCallback(
    (file: File) => {
      const err = validate(file);
      if (err) { setError(err); return; }
      setError(null);
      onFile(file);
    },
    [onFile]
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div
      onDrop={onDrop}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      style={{
        border: `2px dashed ${dragOver ? "#4f46e5" : "#d1d5db"}`,
        borderRadius: 12,
        padding: 40,
        textAlign: "center",
        background: dragOver ? "#eef2ff" : "#f9fafb",
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "all 0.2s",
      }}
    >
      <p style={{ color: "#6b7280", margin: 0 }}>
        Drag & drop an <strong>MP4</strong> video here, or{" "}
        <label style={{ color: "#4f46e5", cursor: "pointer" }}>
          browse
          <input
            type="file"
            accept=".mp4"
            hidden
            disabled={disabled}
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </label>
      </p>
      <p style={{ fontSize: 12, color: "#9ca3af", marginTop: 8 }}>Max 100MB · MP4 only</p>
      {error && <p style={{ color: "#dc2626", marginTop: 8 }}>{error}</p>}
    </div>
  );
};
```

- [ ] **Step 4: Create `frontend/src/components/ResultCard.tsx`**
```tsx
import React from "react";
import { PredictResponse } from "../api/client";

interface Props {
  result: PredictResponse;
}

export const ResultCard: React.FC<Props> = ({ result }) => {
  const isFake = result.prediction === "fake";
  const color = isFake ? "#dc2626" : "#16a34a";
  const pct = Math.round(result.confidence * 100);

  return (
    <div style={{
      border: `2px solid ${color}`,
      borderRadius: 12,
      padding: 24,
      marginTop: 24,
      background: "#fff",
    }}>
      <h2 style={{ color, fontSize: 28, margin: 0 }}>
        {isFake ? "🔴 FAKE" : "🟢 REAL"}
      </h2>

      <div style={{ marginTop: 12 }}>
        <p style={{ margin: "4px 0", color: "#374151" }}>Confidence: <strong>{pct}%</strong></p>
        <div style={{ background: "#e5e7eb", borderRadius: 9999, height: 10, marginTop: 4 }}>
          <div style={{
            width: `${pct}%`, height: "100%",
            background: color, borderRadius: 9999,
            transition: "width 0.5s ease",
          }} />
        </div>
      </div>

      <div style={{ marginTop: 12, fontSize: 13, color: "#6b7280" }}>
        <p style={{ margin: 0 }}>Frames analyzed: {result.frames_analyzed}</p>
        <p style={{ margin: 0 }}>Inference: {result.inference_latency_ms.toFixed(1)}ms</p>
      </div>

      {result.gradcam_image && (
        <div style={{ marginTop: 16 }}>
          <p style={{ fontWeight: 600, marginBottom: 8 }}>Grad-CAM Explanation</p>
          <img
            src={`data:image/png;base64,${result.gradcam_image}`}
            alt="Grad-CAM heatmap"
            style={{ maxWidth: "100%", borderRadius: 8 }}
          />
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 5: Create `frontend/src/components/ErrorConsole.tsx`**
```tsx
import React from "react";

interface LogEntry {
  id: string;
  timestamp: string;
  type: "success" | "error" | "warning";
  message: string;
}

interface Props {
  entries: LogEntry[];
}

const COLOR: Record<LogEntry["type"], string> = {
  success: "#16a34a",
  error: "#dc2626",
  warning: "#d97706",
};

export const ErrorConsole: React.FC<Props> = ({ entries }) => (
  <div style={{
    background: "#111827",
    color: "#f9fafb",
    borderRadius: 8,
    padding: 16,
    fontFamily: "monospace",
    fontSize: 13,
    maxHeight: 300,
    overflowY: "auto",
  }}>
    <p style={{ color: "#9ca3af", marginTop: 0 }}>Pipeline Console</p>
    {entries.length === 0 && <p style={{ color: "#6b7280" }}>No recent pipeline runs.</p>}
    {entries.map((e) => (
      <div key={e.id} style={{ marginBottom: 6 }}>
        <span style={{ color: "#6b7280" }}>{e.timestamp} </span>
        <span style={{ color: COLOR[e.type] }}>[{e.type.toUpperCase()}] </span>
        <span>{e.message}</span>
      </div>
    ))}
  </div>
);
```

- [ ] **Step 6: Create `frontend/src/pages/Home.tsx`**
```tsx
import React, { useState } from "react";
import { VideoUpload } from "../components/VideoUpload";
import { ResultCard } from "../components/ResultCard";
import { predictVideo, PredictResponse } from "../api/client";

export const Home: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await predictVideo(file);
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 640, margin: "48px auto", padding: "0 16px" }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>
        Deepfake Detection
      </h1>
      <p style={{ color: "#6b7280", marginBottom: 24 }}>
        Upload an MP4 video to classify it as real or AI-generated.
      </p>

      <VideoUpload onFile={handleFile} disabled={loading} />

      {loading && (
        <div style={{ textAlign: "center", marginTop: 32, color: "#6b7280" }}>
          <p>Analyzing video... this may take up to 30 seconds.</p>
        </div>
      )}

      {error && (
        <div style={{
          marginTop: 16, padding: 16, background: "#fef2f2",
          border: "1px solid #fecaca", borderRadius: 8, color: "#dc2626",
        }}>
          {error}
        </div>
      )}

      {result && <ResultCard result={result} />}
    </div>
  );
};
```

- [ ] **Step 7: Create `frontend/src/pages/PipelineDashboard.tsx`**
```tsx
import React, { useEffect, useState } from "react";
import { ErrorConsole } from "../components/ErrorConsole";
import { apiClient } from "../api/client";

interface MLflowRun {
  run_id: string;
  status: string;
  metrics: Record<string, number>;
  tags: Record<string, string>;
}

interface AirflowRun {
  dag_id: string;
  state: string;
  start_date: string;
  end_date: string | null;
}

export const PipelineDashboard: React.FC = () => {
  const [mlflowRuns, setMlflowRuns] = useState<MLflowRun[]>([]);
  const [airflowRuns, setAirflowRuns] = useState<AirflowRun[]>([]);
  const [throughput, setThroughput] = useState<number | null>(null);

  useEffect(() => {
    // Fetch MLflow runs via backend proxy
    apiClient.get("/pipeline/mlflow-runs").then(r => setMlflowRuns(r.data)).catch(() => {});
    apiClient.get("/pipeline/airflow-runs").then(r => setAirflowRuns(r.data)).catch(() => {});
    apiClient.get("/pipeline/throughput").then(r => setThroughput(r.data.videos_per_minute)).catch(() => {});
  }, []);

  const consoleEntries = airflowRuns.map((r) => ({
    id: r.dag_id + r.start_date,
    timestamp: r.start_date,
    type: (r.state === "success" ? "success" : r.state === "failed" ? "error" : "warning") as any,
    message: `${r.dag_id} — ${r.state}`,
  }));

  return (
    <div style={{ maxWidth: 900, margin: "48px auto", padding: "0 16px" }}>
      <h1 style={{ fontSize: 24, fontWeight: 700 }}>ML Pipeline Dashboard</h1>

      {/* Throughput widget */}
      <div style={{
        background: "#f0fdf4", border: "1px solid #bbf7d0",
        borderRadius: 8, padding: 16, marginBottom: 24, display: "inline-block"
      }}>
        <p style={{ margin: 0, color: "#166534" }}>
          Pipeline Throughput: <strong>
            {throughput !== null ? `${throughput.toFixed(1)} videos/min` : "—"}
          </strong>
        </p>
      </div>

      <h2 style={{ fontSize: 18 }}>MLflow Experiments</h2>
      <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 32 }}>
        <thead>
          <tr style={{ background: "#f3f4f6" }}>
            {["Run ID", "Status", "Val F1", "Val Acc", "Git Commit"].map(h => (
              <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontSize: 13 }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {mlflowRuns.map(run => (
            <tr key={run.run_id} style={{ borderBottom: "1px solid #e5e7eb" }}>
              <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 12 }}>
                {run.run_id.slice(0, 8)}...
              </td>
              <td style={{ padding: "8px 12px" }}>{run.status}</td>
              <td style={{ padding: "8px 12px" }}>{run.metrics?.val_f1?.toFixed(4) ?? "—"}</td>
              <td style={{ padding: "8px 12px" }}>{run.metrics?.val_accuracy?.toFixed(4) ?? "—"}</td>
              <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 12 }}>
                {run.tags?.git_commit?.slice(0, 7) ?? "—"}
              </td>
            </tr>
          ))}
          {mlflowRuns.length === 0 && (
            <tr><td colSpan={5} style={{ padding: 16, color: "#9ca3af" }}>No runs yet.</td></tr>
          )}
        </tbody>
      </table>

      <h2 style={{ fontSize: 18 }}>Airflow DAG Status</h2>
      <ErrorConsole entries={consoleEntries} />

      <div style={{ marginTop: 24, fontSize: 13, color: "#6b7280" }}>
        <a href="http://localhost:5000" target="_blank" rel="noreferrer" style={{ marginRight: 16 }}>
          Open MLflow UI ↗
        </a>
        <a href="http://localhost:8080" target="_blank" rel="noreferrer">
          Open Airflow UI ↗
        </a>
      </div>
    </div>
  );
};
```

- [ ] **Step 8: Create `frontend/src/App.tsx`**
```tsx
import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { Home } from "./pages/Home";
import { PipelineDashboard } from "./pages/PipelineDashboard";

function App() {
  return (
    <BrowserRouter>
      <nav style={{
        borderBottom: "1px solid #e5e7eb", padding: "12px 24px",
        display: "flex", gap: 24, background: "#fff",
      }}>
        <Link to="/" style={{ fontWeight: 600, color: "#1f2937", textDecoration: "none" }}>
          Deepfake Detector
        </Link>
        <Link to="/pipeline" style={{ color: "#6b7280", textDecoration: "none" }}>
          Pipeline Dashboard
        </Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/pipeline" element={<PipelineDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

- [ ] **Step 9: Create `frontend/nginx.conf`**
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Proxy API calls to backend
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Prometheus exporter sidecar metrics
    location /nginx-metrics {
        stub_status;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 10: Create `frontend/Dockerfile`**
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 11: Add `.eslintrc.cjs` to frontend**
```js
module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  plugins: ["@typescript-eslint", "react-hooks"],
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
  ],
  rules: {
    "@typescript-eslint/no-explicit-any": "warn",
  },
};
```

- [ ] **Step 12: Commit**
```bash
git add frontend/
git commit -m "feat(frontend): add React app with upload, result, pipeline dashboard pages"
```

---

## Phase 7: CI/CD Pipeline

### Task 15: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install black flake8 isort
      - run: black --check backend/ ml/ tests/
      - run: flake8 backend/ ml/ tests/
      - run: isort --check backend/ ml/ tests/
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd frontend && npm ci && npm run lint

  unit-tests:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r backend/requirements.txt -r backend/requirements-dev.txt
      - run: pip install -r ml/requirements.txt
      - run: pytest tests/unit/ -v --tb=short

  dvc-repro:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install dvc
      - run: dvc repro --dry  # verify DAG integrity without running

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r backend/requirements.txt -r backend/requirements-dev.txt
      - run: pytest tests/integration/ -v --tb=short

  build-docker:
    runs-on: ubuntu-latest
    needs: [dvc-repro, integration-tests]
    steps:
      - uses: actions/checkout@v4
      - run: docker build ./backend -t deepfake-backend:ci
      - run: docker build ./frontend -t deepfake-frontend:ci
```

- [ ] **Step 2: Commit**
```bash
git add .github/
git commit -m "ci: add GitHub Actions pipeline (lint, unit tests, DVC, integration, Docker build)"
```

---

## Phase 8: Documentation

### Task 16: HLD, LLD, Test Plan, User Manual

**Files:**
- Create: `docs/HLD.md`
- Create: `docs/LLD.md`
- Create: `docs/test_plan.md`
- Create: `docs/user_manual.md`
- Create: `docs/test_report.md`

- [ ] **Step 1: Create `docs/HLD.md`**
Write high-level design covering:
- Architecture diagram (ASCII version of the spec diagram)
- Component responsibilities and boundaries
- Design choices and rationale (why EfficientNet+LSTM, why MLflow, why Airflow)
- Loose coupling strategy
- Security approach (HTTPS, encrypted volumes, secrets management)
- Rollback procedure summary
- Reproducibility guarantee (Git SHA + MLflow run ID)

- [ ] **Step 2: Create `docs/LLD.md`**
Write low-level design covering:
- All 5 API endpoints with full I/O specification (match schemas.py exactly)
- Data flow for POST /predict (file → preprocess → mlflow-serve → response)
- Database schema (Postgres tables for MLflow + Airflow)
- File structure for `data/` directories
- Prometheus metrics list with labels

- [ ] **Step 3: Create `docs/test_plan.md`**
```markdown
# Test Plan

## Acceptance Criteria
- Accuracy ≥ 90% on held-out test set
- F1-score ≥ 0.90
- P95 inference latency < 200ms over 100 requests

## Test Cases

| ID | Type | Description | Expected |
|---|---|---|---|
| TC-01 | Unit | extract_frames returns 30 frames from valid MP4 | List of 30 numpy arrays |
| TC-02 | Unit | detect_faces falls back on full frame when no face found | Returns 224×224 crop |
| TC-03 | Unit | DeepfakeDetector output shape (2,30,3,224,224) → (2,1) | Shape == (2,1) |
| TC-04 | Unit | compute_drift_score within 1 std → score < 1.0 | Pass |
| TC-05 | Unit | PredictResponse validates confidence ∈ [0,1] | Pass |
| TC-06 | Integration | POST /predict with valid MP4 returns 200 | JSON with prediction field |
| TC-07 | Integration | POST /predict with .avi file returns 400 | HTTP 400 |
| TC-08 | Integration | GET /health returns {"status":"ok"} | Pass |
| TC-09 | Integration | GET /metrics returns Prometheus text | Content-Type text/plain |
| TC-10 | Acceptance | Model F1 ≥ 0.90 on test split | ≥ 0.90 |
| TC-11 | Acceptance | P95 latency < 200ms | < 200ms |
```

- [ ] **Step 4: Create `docs/user_manual.md`**
```markdown
# User Manual — Deepfake Detection System

## What this tool does
Upload an MP4 video and the system will tell you whether the video appears to be real or AI-generated (a deepfake).

## How to use

### Step 1: Open the application
Go to http://localhost:3000 in your web browser.

### Step 2: Upload a video
Click "browse" or drag and drop an MP4 video file onto the upload area.
- The file must be in MP4 format
- Maximum size: 100MB

### Step 3: Wait for the result
The system will analyze your video. This takes up to 30 seconds.

### Step 4: Read the result
- **GREEN — REAL**: The video appears to be authentic
- **RED — FAKE**: The video appears to be AI-generated or manipulated
- The confidence percentage shows how certain the system is
- The heatmap image shows which parts of the face influenced the decision most

## Pipeline Dashboard
Click "Pipeline Dashboard" in the navigation bar to see:
- Recent model training experiments and their performance metrics
- Data pipeline run history (success/failure)
- Current pipeline throughput
- Links to the MLflow and Airflow dashboards for detailed information

## Troubleshooting
| Problem | Solution |
|---|---|
| "Only MP4 files are accepted" | Convert your video to MP4 format first |
| "File must be under 100MB" | Trim your video or reduce its resolution |
| "An unexpected error occurred" | The system may be starting up — wait 30 seconds and try again |
| Blank result | Ensure the video contains a clearly visible human face |
```

- [ ] **Step 5: Create `docs/test_report.md` template**
```markdown
# Test Report

**Date:** [Fill after running tests]
**Commit:** [git rev-parse HEAD]
**MLflow Run ID:** [Fill after training]

## Summary
| Category | Total | Passed | Failed |
|---|---|---|---|
| Unit | 8 | ? | ? |
| Integration | 4 | ? | ? |
| Acceptance | 2 | ? | ? |

## Acceptance Criteria Results
| Criteria | Target | Actual | Status |
|---|---|---|---|
| Accuracy | ≥ 90% | ? | ? |
| F1-score | ≥ 0.90 | ? | ? |
| P95 Latency | < 200ms | ? | ? |

## Failed Tests
[List any failed test IDs here with error details]
```

- [ ] **Step 6: Commit**
```bash
git add docs/
git commit -m "docs: add HLD, LLD, test plan, user manual, test report template"
```

---

## Phase 9: MLflow Serve Container

### Task 17: MLflow Serve Dockerfile + ml Dockerfile

**Files:**
- Create: `ml/Dockerfile.serve`

- [ ] **Step 1: Create `ml/Dockerfile.serve`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN pip install mlflow==2.11.1 torch==2.2.1 torchvision==0.17.1 \
    efficientnet-pytorch==0.7.1 facenet-pytorch==2.5.3

ENV MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}
ENV MODEL_NAME=${MODEL_NAME:-deepfake}
ENV MODEL_STAGE=${MODEL_STAGE:-Production}

CMD mlflow models serve \
    -m "models:/${MODEL_NAME}/${MODEL_STAGE}" \
    --host 0.0.0.0 \
    --port 5001 \
    --no-conda
```

- [ ] **Step 2: Commit**
```bash
git add ml/Dockerfile.serve
git commit -m "feat(ml): add MLflow serve container"
```

---

## Phase 10: Final Wiring + Smoke Test

### Task 18: Smoke Test End-to-End

- [ ] **Step 1: Copy and fill `.env`**
```bash
cp .env.example .env
# Fill in real POSTGRES_PASSWORD, GRAFANA_ADMIN_PASSWORD, AIRFLOW__CORE__FERNET_KEY
```

Generate Fernet key:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

- [ ] **Step 2: Start infrastructure**
```bash
docker-compose up -d postgres redis
docker-compose up airflow-init
docker-compose up -d mlflow-server
```

- [ ] **Step 3: Train initial model**
```bash
# With sample data (place a few test MP4s in data/landing/)
docker-compose run --rm airflow-worker airflow dags trigger deepfake_pipeline
# Then train:
docker-compose run --rm ml python ml/train.py
```

- [ ] **Step 4: Promote model to Production**
```bash
# Via MLflow UI at http://localhost:5000
# Or via CLI:
docker-compose run --rm mlflow-server mlflow models transition-model-version-stage \
  --name deepfake --version 1 --stage Production
```

- [ ] **Step 5: Start all services**
```bash
docker-compose up -d
```

- [ ] **Step 6: Run smoke tests**
```bash
# Health check
curl http://localhost:8000/health

# Ready check
curl http://localhost:8000/ready

# Predict (with a sample MP4)
curl -X POST http://localhost:8000/predict \
  -F "file=@sample.mp4" | python -m json.tool

# Check Prometheus
curl http://localhost:9090/api/v1/targets | python -m json.tool

# Check frontend
open http://localhost:3000
```

- [ ] **Step 7: Run full test suite and fill test report**
```bash
pytest tests/ -v --tb=short 2>&1 | tee docs/test_report_raw.txt
# Fill in docs/test_report.md with actual results
```

- [ ] **Step 8: Final commit**
```bash
git add -A
git commit -m "chore: complete initial implementation — all services running"
```

---

## Quick Reference: Service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| MLflow UI | http://localhost:5000 |
| Airflow UI | http://localhost:8080 (admin/admin) |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| `airflow-init` | Internal — runs once to init DB and create admin user |

---

## Phase 11: Missing Components (Review Fixes)

### Task 19: Backend Pipeline Router

**Files:**
- Create: `backend/app/routers/pipeline.py`
- Modify: `backend/app/routers/__init__.py`

- [ ] **Step 1: Create `backend/app/routers/pipeline.py`**
```python
"""Pipeline data endpoints — proxy MLflow and Airflow APIs for frontend dashboard."""
import logging
import os
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter

pipeline_router = APIRouter()
logger = logging.getLogger(__name__)

MLFLOW_URL = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-server:5000")
AIRFLOW_URL = os.getenv("AIRFLOW_URL", "http://airflow-webserver:8080")
AIRFLOW_AUTH = ("admin", "admin")


@pipeline_router.get("/mlflow-runs")
async def get_mlflow_runs() -> List[Dict[str, Any]]:
    """Return recent MLflow runs for the dashboard experiment table."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{MLFLOW_URL}/api/2.0/mlflow/runs/search",
                json={"experiment_ids": [], "max_results": 20,
                      "order_by": ["start_time DESC"]},
            )
            resp.raise_for_status()
            runs = resp.json().get("runs", [])
            return [
                {
                    "run_id": r["info"]["run_id"],
                    "status": r["info"]["status"],
                    "metrics": {m["key"]: m["value"] for m in r.get("data", {}).get("metrics", [])},
                    "tags": {t["key"]: t["value"] for t in r.get("data", {}).get("tags", [])},
                }
                for r in runs
            ]
    except Exception as e:
        logger.error("mlflow_runs_fetch_failed", extra={"error": str(e)})
        return []


@pipeline_router.get("/airflow-runs")
async def get_airflow_runs() -> List[Dict[str, Any]]:
    """Return recent Airflow DAG runs for the pipeline console."""
    try:
        async with httpx.AsyncClient(timeout=10, auth=AIRFLOW_AUTH) as client:
            resp = await client.get(
                f"{AIRFLOW_URL}/api/v1/dags/deepfake_pipeline/dagRuns",
                params={"limit": 10, "order_by": "-execution_date"},
            )
            resp.raise_for_status()
            runs = resp.json().get("dag_runs", [])
            return [
                {
                    "dag_id": r["dag_id"],
                    "state": r["state"],
                    "start_date": r.get("start_date", ""),
                    "end_date": r.get("end_date", ""),
                }
                for r in runs
            ]
    except Exception as e:
        logger.error("airflow_runs_fetch_failed", extra={"error": str(e)})
        return []


@pipeline_router.get("/throughput")
async def get_throughput() -> Dict[str, Any]:
    """Compute videos-per-minute from last successful Airflow pipeline run."""
    try:
        async with httpx.AsyncClient(timeout=10, auth=AIRFLOW_AUTH) as client:
            resp = await client.get(
                f"{AIRFLOW_URL}/api/v1/dags/deepfake_pipeline/dagRuns",
                params={"limit": 1, "state": "success", "order_by": "-execution_date"},
            )
            resp.raise_for_status()
            runs = resp.json().get("dag_runs", [])
            if not runs:
                return {"videos_per_minute": None}
            run = runs[0]

            # Get task instance for ingest_videos to find video count via XCom
            xcom_resp = await client.get(
                f"{AIRFLOW_URL}/api/v1/dags/deepfake_pipeline/dagRuns"
                f"/{run['dag_run_id']}/taskInstances/ingest_videos/xcomEntries/video_count",
            )
            video_count = xcom_resp.json().get("value", 0) if xcom_resp.status_code == 200 else 0

            # Duration in minutes
            from datetime import datetime
            start = datetime.fromisoformat(run["start_date"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(run["end_date"].replace("Z", "+00:00"))
            duration_min = max((end - start).total_seconds() / 60, 0.01)
            return {"videos_per_minute": round(video_count / duration_min, 2)}
    except Exception as e:
        logger.error("throughput_fetch_failed", extra={"error": str(e)})
        return {"videos_per_minute": None}
```

- [ ] **Step 2: Commit**
```bash
git add backend/app/routers/pipeline.py backend/app/main.py
git commit -m "feat(backend): add pipeline proxy router for dashboard endpoints"
```

---

### Task 20: Missing Frontend Components

**Files:**
- Create: `frontend/src/components/PipelineStatus.tsx`
- Create: `frontend/src/components/ExperimentTable.tsx`
- Create: `frontend/src/hooks/usePrediction.ts`

- [ ] **Step 1: Create `frontend/src/hooks/usePrediction.ts`**
```typescript
import { useState, useCallback } from "react";
import { predictVideo, PredictResponse } from "../api/client";

interface UsePredictionResult {
  loading: boolean;
  result: PredictResponse | null;
  error: string | null;
  predict: (file: File) => Promise<void>;
  reset: () => void;
}

export const usePrediction = (): UsePredictionResult => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const predict = useCallback(async (file: File) => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await predictVideo(file);
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { loading, result, error, predict, reset };
};
```

- [ ] **Step 2: Update `frontend/src/pages/Home.tsx` to use `usePrediction` hook**
Replace the inline state management in `Home.tsx` with the hook:
```tsx
import React from "react";
import { VideoUpload } from "../components/VideoUpload";
import { ResultCard } from "../components/ResultCard";
import { usePrediction } from "../hooks/usePrediction";

export const Home: React.FC = () => {
  const { loading, result, error, predict } = usePrediction();

  return (
    <div style={{ maxWidth: 640, margin: "48px auto", padding: "0 16px" }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>
        Deepfake Detection
      </h1>
      <p style={{ color: "#6b7280", marginBottom: 24 }}>
        Upload an MP4 video to classify it as real or AI-generated.
      </p>
      <VideoUpload onFile={predict} disabled={loading} />
      {loading && (
        <div style={{ textAlign: "center", marginTop: 32, color: "#6b7280" }}>
          <p>Analyzing video... this may take up to 30 seconds.</p>
        </div>
      )}
      {error && (
        <div style={{
          marginTop: 16, padding: 16, background: "#fef2f2",
          border: "1px solid #fecaca", borderRadius: 8, color: "#dc2626",
        }}>
          {error}
        </div>
      )}
      {result && <ResultCard result={result} />}
    </div>
  );
};
```

- [ ] **Step 3: Create `frontend/src/components/ExperimentTable.tsx`**
```tsx
import React from "react";

interface MLflowRun {
  run_id: string;
  status: string;
  metrics: Record<string, number>;
  tags: Record<string, string>;
}

interface Props {
  runs: MLflowRun[];
}

export const ExperimentTable: React.FC<Props> = ({ runs }) => (
  <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 32 }}>
    <thead>
      <tr style={{ background: "#f3f4f6" }}>
        {["Run ID", "Status", "Val F1", "Val Acc", "Git Commit"].map((h) => (
          <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontSize: 13 }}>
            {h}
          </th>
        ))}
      </tr>
    </thead>
    <tbody>
      {runs.map((run) => (
        <tr key={run.run_id} style={{ borderBottom: "1px solid #e5e7eb" }}>
          <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 12 }}>
            {run.run_id.slice(0, 8)}...
          </td>
          <td style={{ padding: "8px 12px" }}>{run.status}</td>
          <td style={{ padding: "8px 12px" }}>
            {run.metrics?.val_f1?.toFixed(4) ?? "—"}
          </td>
          <td style={{ padding: "8px 12px" }}>
            {run.metrics?.val_accuracy?.toFixed(4) ?? "—"}
          </td>
          <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 12 }}>
            {run.tags?.git_commit?.slice(0, 7) ?? "—"}
          </td>
        </tr>
      ))}
      {runs.length === 0 && (
        <tr>
          <td colSpan={5} style={{ padding: 16, color: "#9ca3af" }}>
            No runs yet.
          </td>
        </tr>
      )}
    </tbody>
  </table>
);
```

- [ ] **Step 4: Create `frontend/src/components/PipelineStatus.tsx`**
```tsx
import React from "react";

interface AirflowRun {
  dag_id: string;
  state: string;
  start_date: string;
  end_date: string | null;
}

interface Props {
  runs: AirflowRun[];
  throughput: number | null;
}

const STATE_COLOR: Record<string, string> = {
  success: "#16a34a",
  failed: "#dc2626",
  running: "#d97706",
  queued: "#6b7280",
};

export const PipelineStatus: React.FC<Props> = ({ runs, throughput }) => (
  <div>
    <div style={{
      background: "#f0fdf4", border: "1px solid #bbf7d0",
      borderRadius: 8, padding: 16, marginBottom: 16, display: "inline-block",
    }}>
      <p style={{ margin: 0, color: "#166534" }}>
        Pipeline Throughput:{" "}
        <strong>
          {throughput !== null ? `${throughput.toFixed(1)} videos/min` : "—"}
        </strong>
      </p>
    </div>

    <div>
      {runs.length === 0 && (
        <p style={{ color: "#9ca3af" }}>No recent DAG runs.</p>
      )}
      {runs.map((r) => (
        <div
          key={r.dag_id + r.start_date}
          style={{
            display: "flex", justifyContent: "space-between",
            padding: "8px 12px", borderBottom: "1px solid #e5e7eb", fontSize: 13,
          }}
        >
          <span style={{ fontFamily: "monospace" }}>{r.dag_id}</span>
          <span style={{ color: STATE_COLOR[r.state] ?? "#374151", fontWeight: 600 }}>
            {r.state}
          </span>
          <span style={{ color: "#9ca3af" }}>{r.start_date.slice(0, 19)}</span>
        </div>
      ))}
    </div>
  </div>
);
```

- [ ] **Step 5: Update `PipelineDashboard.tsx` to use the new components**
```tsx
import React, { useEffect, useState } from "react";
import { ErrorConsole } from "../components/ErrorConsole";
import { ExperimentTable } from "../components/ExperimentTable";
import { PipelineStatus } from "../components/PipelineStatus";
import { apiClient } from "../api/client";

export const PipelineDashboard: React.FC = () => {
  const [mlflowRuns, setMlflowRuns] = useState([]);
  const [airflowRuns, setAirflowRuns] = useState([]);
  const [throughput, setThroughput] = useState<number | null>(null);

  useEffect(() => {
    apiClient.get("/pipeline/mlflow-runs").then(r => setMlflowRuns(r.data)).catch(() => {});
    apiClient.get("/pipeline/airflow-runs").then(r => setAirflowRuns(r.data)).catch(() => {});
    apiClient.get("/pipeline/throughput").then(r => setThroughput(r.data.videos_per_minute)).catch(() => {});
  }, []);

  const consoleEntries = airflowRuns.map((r: any) => ({
    id: r.dag_id + r.start_date,
    timestamp: r.start_date,
    type: (r.state === "success" ? "success" : r.state === "failed" ? "error" : "warning") as any,
    message: `${r.dag_id} — ${r.state}`,
  }));

  return (
    <div style={{ maxWidth: 900, margin: "48px auto", padding: "0 16px" }}>
      <h1 style={{ fontSize: 24, fontWeight: 700 }}>ML Pipeline Dashboard</h1>

      <h2 style={{ fontSize: 18 }}>Pipeline Status</h2>
      <PipelineStatus runs={airflowRuns} throughput={throughput} />

      <h2 style={{ fontSize: 18, marginTop: 32 }}>MLflow Experiments</h2>
      <ExperimentTable runs={mlflowRuns} />

      <h2 style={{ fontSize: 18 }}>Run Console</h2>
      <ErrorConsole entries={consoleEntries} />

      <div style={{ marginTop: 24, fontSize: 13, color: "#6b7280" }}>
        <a href="http://localhost:5000" target="_blank" rel="noreferrer" style={{ marginRight: 16 }}>
          Open MLflow UI ↗
        </a>
        <a href="http://localhost:8080" target="_blank" rel="noreferrer">
          Open Airflow UI ↗
        </a>
      </div>
    </div>
  );
};
```

- [ ] **Step 6: Commit**
```bash
git add frontend/src/components/PipelineStatus.tsx frontend/src/components/ExperimentTable.tsx frontend/src/hooks/usePrediction.ts frontend/src/pages/
git commit -m "feat(frontend): add PipelineStatus, ExperimentTable components and usePrediction hook"
```

---

### Task 21: Documentation Content (HLD + LLD + Architecture Diagram)

**Files:**
- Create: `docs/HLD.md` (full content)
- Create: `docs/LLD.md` (full content)
- Create: `docs/architecture_diagram.py` (generates PNG)

- [ ] **Step 1: Create `docs/HLD.md`**
```markdown
# High-Level Design — Deepfake Detection System

## 1. Architecture Diagram
```
User Browser
     │ HTTP (Nginx proxy)
     ▼
┌─────────────────┐
│  React Frontend  │  Port 3000  (Nginx)
│  - Home Page     │
│  - Pipeline Dash │
└────────┬────────┘
         │ REST /api/*
         ▼
┌─────────────────┐
│  FastAPI Backend │  Port 8000
│  - /predict      │
│  - /health       │
│  - /ready        │
│  - /metrics      │
│  - /pipeline/*   │
│  - /admin/*      │
└────────┬────────┘
         │ POST /invocations
         ▼
┌─────────────────┐         ┌──────────────────────┐
│  MLflow Serve   │         │  MLflow Tracking      │
│  Port 5001      │◄────────│  Server + Registry    │
│  (pyfunc model) │ loads   │  Port 5000            │
└─────────────────┘         └──────────┬───────────┘
                                        │ stores metadata
                                        ▼
                             ┌──────────────────────┐
                             │  PostgreSQL           │
                             │  Port 5432            │
                             │  (MLflow + Airflow DB)│
                             └──────────────────────┘

┌─────────────────────────────────────────────┐
│  Apache Airflow                              │
│  Webserver (8080) + Scheduler + Worker       │
│  DAGs: deepfake_pipeline, retraining_dag     │
│  Broker: Redis (6379)                        │
└─────────────────────────────────────────────┘

┌─────────────────┐      ┌─────────────────┐
│  Prometheus      │─────▶│  Grafana         │
│  Port 9090       │      │  Port 3001       │
│  Scrapes all     │      │  Dashboards +    │
│  services        │      │  Alerts          │
└─────────────────┘      └─────────────────┘
```

## 2. Component Responsibilities

| Component | Responsibility |
|---|---|
| React Frontend | User-facing UI: video upload, result display, pipeline dashboard |
| Nginx | Serve React static files, proxy `/api/*` → backend |
| FastAPI Backend | Video preprocessing (MTCNN), orchestrate inference, expose Prometheus metrics |
| MLflow Serve | Serve trained PyTorch model as REST endpoint (pyfunc) |
| MLflow Server | Track experiments, store model versions in registry |
| Airflow | Orchestrate data pipelines and automated retraining |
| Postgres | Persistent metadata for MLflow and Airflow |
| Redis | Celery message broker for Airflow task distribution |
| Prometheus | Scrape metrics from all services every 15s |
| Grafana | Visualize metrics in NRT; fire alerts on threshold breach |

## 3. Design Principles

**Loose Coupling:** Frontend communicates with backend exclusively via REST API.
The `VITE_API_URL` environment variable configures the API base URL — changing the backend URL requires no code changes.

**Reproducibility:** Every MLflow training run is tagged with the Git commit SHA:
`mlflow.set_tag("git_commit", git rev-parse HEAD)`. Any run can be reproduced by checking out that commit and re-running `mlflow run . -e train --run-id <id>`.

**Rollback:** MLflow Model Registry maintains `None → Staging → Production → Archived` stages. Rollback = demote current Production to Archived, promote previous Archived to Production. Backend reloads via `POST /admin/reload-model`.

## 4. Why These Technology Choices

| Choice | Rationale |
|---|---|
| EfficientNet-B0 + LSTM | EfficientNet provides strong spatial features at low compute cost. LSTM captures temporal inconsistencies across frames — key signal for deepfake detection |
| MLflow | Unified experiment tracking + model registry + serving. Avoids vendor lock-in vs cloud-specific tools |
| Airflow | Industry-standard DAG orchestrator. CeleryExecutor scales to multiple workers |
| MTCNN | Best balance of detection accuracy and speed for face cropping on CPU |
| FastAPI | Async Python API framework with automatic OpenAPI docs and Pydantic validation |
| Docker Compose | Single-command local deployment matching production topology |

## 5. Security

- All secrets in `.env` (not committed). `.env.example` documents required variables.
- HTTPS via Nginx TLS termination (production deployment).
- Prometheus and Grafana behind basic auth.
- Data volumes (face crops, feature tensors) on OS-encrypted filesystem (BitLocker/LUKS).
- No cloud usage — all data stays local.

## 6. Data Flow: POST /predict

1. User uploads MP4 → Nginx → FastAPI
2. FastAPI saves to temp file
3. `preprocessing.py`: extract 30 frames → MTCNN face detection → tensor (30, 3, 224, 224)
4. Feature vector extracted → `drift_detector.py` checks against baseline stats
5. Tensor sent to MLflow Serve via `POST /invocations`
6. Confidence score returned → label assigned (`fake` if ≥ 0.5)
7. Grad-CAM heatmap generated from model gradients
8. Prometheus metrics updated
9. JSON response returned to frontend
```

- [ ] **Step 2: Create `docs/LLD.md`**
```markdown
# Low-Level Design — Deepfake Detection System

## 1. API Endpoint Specifications

### `POST /predict`
**Description:** Accept MP4 video, return real/fake classification

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (binary MP4, max 100MB)

**Response 200:**
```json
{
  "prediction": "fake",           // string: "real" | "fake"
  "confidence": 0.94,             // float: [0.0, 1.0]
  "inference_latency_ms": 143.2,  // float: milliseconds
  "gradcam_image": "<base64>",    // string: base64-encoded PNG
  "mlflow_run_id": "abc123",      // string: UUID
  "frames_analyzed": 30           // int
}
```

**Response 400:** `{"error": "validation_error", "detail": "Only MP4 files are accepted"}`
**Response 500:** `{"error": "internal_error", "detail": "<exception message>"}`

---

### `GET /health`
**Description:** Liveness probe

**Response 200:**
```json
{"status": "ok", "model_loaded": true}
```

---

### `GET /ready`
**Description:** Readiness probe — fails if model not loaded

**Response 200:**
```json
{"status": "ready", "model_version": "deepfake/Production/3"}
```
**Response 503:** `{"detail": "Model not loaded"}`

---

### `GET /metrics`
**Description:** Prometheus metrics scrape endpoint

**Response 200:** Prometheus text exposition format
**Content-Type:** `text/plain; version=0.0.4`

---

### `POST /admin/reload-model`
**Description:** Force reload model from MLflow registry (used during rollback). Internal only — not exposed through Nginx.

**Request:** Empty body `{}`

**Response 200:**
```json
{"status": "reloaded", "model_version": "deepfake/Production/2"}
```

---

### `GET /pipeline/mlflow-runs`
**Response:** Array of MLflow run objects:
```json
[{"run_id": "abc", "status": "FINISHED", "metrics": {"val_f1": 0.92}, "tags": {"git_commit": "a1b2c3"}}]
```

### `GET /pipeline/airflow-runs`
**Response:** Array of Airflow DAG run objects:
```json
[{"dag_id": "deepfake_pipeline", "state": "success", "start_date": "2026-03-23T10:00:00", "end_date": "2026-03-23T10:15:00"}]
```

### `GET /pipeline/throughput`
**Response:**
```json
{"videos_per_minute": 12.5}
```

---

## 2. Prometheus Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `deepfake_requests_total` | Counter | method, endpoint, status | Total API requests |
| `deepfake_request_latency_seconds` | Histogram | endpoint | End-to-end request latency |
| `deepfake_inference_latency_ms` | Histogram | — | Model inference time |
| `deepfake_confidence_score` | Histogram | — | Confidence score distribution |
| `deepfake_predictions_total` | Counter | label | Predictions by real/fake |
| `deepfake_drift_score` | Gauge | — | Current feature drift z-score |
| `deepfake_drift_detected_total` | Counter | — | Drift detection events |
| `pipeline_validation_failures_total` | Counter | — | Airflow schema validation failures |

---

## 3. Data Directory Structure

```
data/
├── landing/          ← Drop MP4s here for ingestion
├── raw/              ← DVC-tracked source MP4s
├── frames/
│   └── {video_name}/
│       ├── frame_000.jpg
│       └── frame_029.jpg
├── faces/
│   └── {video_name}/
│       └── frame_000.jpg  ← 224×224 face crop
├── features/
│   └── {video_name}.pt    ← Tensor (N_frames, feature_dim)
└── feedback/
    └── feedback_log.jsonl  ← Ground truth log entries
```

---

## 4. Feature Tensor Schema

Each `.pt` file in `data/features/`:
- **Shape:** `(N, D)` where N = number of frames (≤30), D = EfficientNet-B0 output dim (1280)
- **dtype:** `torch.float32`
- **Value range:** approximately `[-5, 5]` (post-normalization)
- **NaN check:** No NaN values permitted (enforced by `validate_schema` Airflow task)
```

- [ ] **Step 3: Create `docs/architecture_diagram.py`** (generates PNG from ASCII)
```python
"""Generate architecture_diagram.png from ASCII art using matplotlib."""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis("off")

def box(ax, x, y, w, h, label, sublabel="", color="#dbeafe"):
    rect = mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.1", linewidth=1.5,
        edgecolor="#3b82f6", facecolor=color)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2 + (0.15 if sublabel else 0),
            label, ha="center", va="center", fontsize=9, fontweight="bold")
    if sublabel:
        ax.text(x + w/2, y + h/2 - 0.2, sublabel,
                ha="center", va="center", fontsize=7, color="#6b7280")

def arrow(ax, x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color="#374151", lw=1.5))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.1, my, label, fontsize=7, color="#6b7280")

box(ax, 5.5, 8.5, 3, 1, "User Browser", color="#f0fdf4")
box(ax, 5, 7, 4, 1, "React Frontend", "Nginx :3000", color="#dbeafe")
box(ax, 5, 5.5, 4, 1, "FastAPI Backend", ":8000", color="#dbeafe")
box(ax, 2.5, 3.5, 3, 1, "MLflow Serve", ":5001 pyfunc", color="#fef3c7")
box(ax, 8.5, 3.5, 3, 1, "MLflow Server", ":5000 Tracking+Registry", color="#fef3c7")
box(ax, 5.5, 2, 3, 1, "PostgreSQL", ":5432", color="#f3f4f6")
box(ax, 0.5, 5.5, 3, 1.8, "Airflow", "Webserver+Sched+Worker\n:8080", color="#ede9fe")
box(ax, 0.5, 3.5, 2, 1, "Redis", ":6379", color="#f3f4f6")
box(ax, 9, 6.5, 2, 0.8, "Prometheus", ":9090", color="#fce7f3")
box(ax, 11.5, 6.5, 2, 0.8, "Grafana", ":3001", color="#fce7f3")

arrow(ax, 7, 8.5, 7, 8)
arrow(ax, 7, 7, 7, 6.5)
arrow(ax, 5, 6, 3.5, 4.5, "POST /invocations")
arrow(ax, 8.5, 5.5, 9.5, 4.5)
arrow(ax, 4, 4, 6.5, 3)
arrow(ax, 9.5, 3.5, 7.5, 3)
arrow(ax, 2, 5.5, 2, 4.5)
arrow(ax, 9, 6.5, 9, 5.5, "scrape")
arrow(ax, 11, 6.9, 11.5, 6.9)

ax.set_title("Deepfake Detection System — Architecture", fontsize=13, fontweight="bold", pad=20)
fig.tight_layout()
fig.savefig(Path(__file__).parent / "architecture_diagram.png", dpi=150, bbox_inches="tight")
print("Saved docs/architecture_diagram.png")
```

- [ ] **Step 4: Generate the diagram**
```bash
cd deepfake-detection
pip install matplotlib
python docs/architecture_diagram.py
```

- [ ] **Step 5: Commit**
```bash
git add docs/HLD.md docs/LLD.md docs/architecture_diagram.py docs/architecture_diagram.png
git commit -m "docs: add full HLD, LLD, and architecture diagram"
```

---

### Task 22: Grafana Dashboard JSON Files

**Files:**
- Create: `monitoring/grafana/dashboards/data_pipeline.json`
- Create: `monitoring/grafana/dashboards/model_drift.json`
- Create: `monitoring/grafana/dashboards/inference.json`

- [ ] **Step 1: Create `monitoring/grafana/dashboards/inference.json`**
```json
{
  "title": "Deepfake Inference",
  "uid": "deepfake-inference",
  "schemaVersion": 37,
  "panels": [
    {
      "title": "Request Rate (req/s)",
      "type": "stat",
      "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
      "targets": [{"expr": "rate(deepfake_requests_total[1m])", "legendFormat": "{{status}}"}]
    },
    {
      "title": "Error Rate (%)",
      "type": "stat",
      "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
      "targets": [{"expr": "rate(deepfake_requests_total{status='500'}[5m]) / rate(deepfake_requests_total[5m]) * 100", "legendFormat": "Error %"}]
    },
    {
      "title": "Inference Latency P95 (ms)",
      "type": "graph",
      "gridPos": {"h": 6, "w": 12, "x": 0, "y": 4},
      "targets": [{"expr": "histogram_quantile(0.95, rate(deepfake_inference_latency_ms_bucket[5m]))", "legendFormat": "p95"}]
    },
    {
      "title": "Prediction Distribution",
      "type": "piechart",
      "gridPos": {"h": 6, "w": 6, "x": 0, "y": 10},
      "targets": [{"expr": "deepfake_predictions_total", "legendFormat": "{{label}}"}]
    }
  ],
  "time": {"from": "now-1h", "to": "now"},
  "refresh": "30s"
}
```

- [ ] **Step 2: Create `monitoring/grafana/dashboards/data_pipeline.json`**
```json
{
  "title": "Data Pipeline",
  "uid": "deepfake-pipeline",
  "schemaVersion": 37,
  "panels": [
    {
      "title": "Pipeline Validation Failures",
      "type": "stat",
      "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
      "targets": [{"expr": "pipeline_validation_failures_total", "legendFormat": "Failures"}],
      "fieldConfig": {"defaults": {"thresholds": {"steps": [{"color": "green", "value": 0}, {"color": "red", "value": 1}]}}}
    },
    {
      "title": "Airflow Task Success Rate",
      "type": "graph",
      "gridPos": {"h": 6, "w": 12, "x": 0, "y": 4},
      "targets": [{"expr": "rate(airflow_task_duration_seconds_count{state='success'}[5m])", "legendFormat": "success/s"}]
    }
  ],
  "time": {"from": "now-6h", "to": "now"},
  "refresh": "1m"
}
```

- [ ] **Step 3: Create `monitoring/grafana/dashboards/model_drift.json`**
```json
{
  "title": "Model Drift",
  "uid": "deepfake-drift",
  "schemaVersion": 37,
  "panels": [
    {
      "title": "Feature Drift Score",
      "type": "graph",
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
      "targets": [{"expr": "deepfake_drift_score", "legendFormat": "Drift Score"}],
      "fieldConfig": {
        "defaults": {
          "thresholds": {"steps": [{"color": "green", "value": 0}, {"color": "yellow", "value": 2}, {"color": "red", "value": 3}]}
        }
      }
    },
    {
      "title": "Drift Events (last 24h)",
      "type": "stat",
      "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8},
      "targets": [{"expr": "increase(deepfake_drift_detected_total[24h])", "legendFormat": "Events"}]
    },
    {
      "title": "Confidence Score Distribution",
      "type": "heatmap",
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12},
      "targets": [{"expr": "rate(deepfake_confidence_score_bucket[5m])", "legendFormat": "{{le}}"}]
    }
  ],
  "time": {"from": "now-24h", "to": "now"},
  "refresh": "1m"
}
```

- [ ] **Step 4: Commit**
```bash
git add monitoring/grafana/dashboards/
git commit -m "feat(monitoring): add Grafana dashboard JSON for inference, pipeline, and drift"
```
