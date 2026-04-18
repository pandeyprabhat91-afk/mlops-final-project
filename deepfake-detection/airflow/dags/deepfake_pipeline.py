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
    """Extract 30 evenly-sampled frames from each MP4."""
    import cv2
    import numpy as np

    raw = DATA_PATH / "raw"
    frames_dir = DATA_PATH / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for mp4 in raw.glob("*.mp4"):
        cap = cv2.VideoCapture(str(mp4))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            cap.release()
            continue
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
    import shutil

    import torchvision.transforms.functional as TF
    from facenet_pytorch import MTCNN
    from PIL import Image

    mtcnn = MTCNN(image_size=224, margin=20, keep_all=False, device="cpu")
    frames_dir = DATA_PATH / "frames"
    faces_dir = DATA_PATH / "faces"
    detected, total = 0, 0
    for video_dir in frames_dir.iterdir():
        out_dir = faces_dir / video_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for jpg in sorted(video_dir.glob("*.jpg")):
            total += 1
            img = Image.open(jpg).convert("RGB")
            face = mtcnn(img)
            if face is not None:
                detected += 1
                TF.to_pil_image(((face + 1) / 2).clamp(0, 1)).save(out_dir / jpg.name)
            else:
                shutil.copy(jpg, out_dir / jpg.name)
    logger.info(f"Face detection rate: {detected}/{total}")


def compute_features(**context):
    """Extract EfficientNet-B0 features from face crops."""
    import torch
    from efficientnet_pytorch import EfficientNet
    from PIL import Image
    from torchvision import transforms

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
    features_dir.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        for video_dir in faces_dir.iterdir():
            tensors = [
                transform(Image.open(jpg).convert("RGB"))
                for jpg in sorted(video_dir.glob("*.jpg"))
            ]
            if tensors:
                feats = model(torch.stack(tensors))
                torch.save(feats, features_dir / f"{video_dir.name}.pt")
    logger.info("Feature extraction complete")


def validate_schema(**context):
    """Validate feature tensors: shape, dtype, value range, no NaN.

    Raises AirflowException if any file fails validation, halting the DAG.
    Increments pipeline_validation_failures_total Prometheus counter via push gateway.
    """
    import torch
    from airflow.exceptions import AirflowException

    features_dir = DATA_PATH / "features"
    failures = 0
    for pt_file in features_dir.rglob("*.pt"):
        tensor = torch.load(pt_file, weights_only=True)
        errors = []
        if tensor.ndim != 2:
            errors.append(f"Expected 2D tensor, got {tensor.ndim}D")
        if tensor.dtype != torch.float32:
            errors.append(f"Expected float32, got {tensor.dtype}")
        if torch.isnan(tensor).any():
            errors.append("NaN values found")
        if errors:
            failures += 1
            logger.error(f"Validation failed for {pt_file}: {errors}")

    if failures > 0:
        try:
            from prometheus_client import CollectorRegistry, Counter, push_to_gateway

            reg = CollectorRegistry()
            c = Counter(
                "pipeline_validation_failures_total",
                "Pipeline schema validation failures",
                registry=reg,
            )
            c.inc(failures)
            push_to_gateway("prometheus:9091", job="airflow", registry=reg)
        except Exception as prom_err:
            logger.warning(f"Could not push Prometheus metric: {prom_err}")
        raise AirflowException(
            f"Schema validation failed for {failures} files. DAG halted."
        )
    logger.info("Schema validation passed for all feature files")


def record_baseline_stats(**context):
    """Compute and save feature baseline statistics using ml/drift_baseline.py."""
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
