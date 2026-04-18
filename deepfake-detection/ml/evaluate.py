"""Standalone evaluation script. Generates confusion matrix and ROC curve artifacts."""
import sys
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import mlflow
import mlflow.pytorch
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    auc,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_curve,
)

sys.path.insert(0, str(Path(__file__).parent.parent))


def find_best_threshold(probs: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    """Sweep thresholds 0.1-0.9 and return the one maximising F1.

    Args:
        probs: 1-D array of model output probabilities
        labels: 1-D array of ground-truth binary labels

    Returns:
        Tuple of (best_threshold, best_f1_score)
    """
    best_threshold, best_f1 = 0.5, 0.0
    for t in np.arange(0.1, 0.95, 0.05):
        preds = (probs >= t).astype(int)
        f1 = f1_score(labels, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = float(t)
    return best_threshold, best_f1


def compute_extended_metrics(probs: np.ndarray, labels: np.ndarray) -> dict:
    """Compute PR-AUC, per-class precision/recall, and optimal threshold.

    Args:
        probs: 1-D array of model output probabilities (fake=1)
        labels: 1-D array of ground-truth binary labels

    Returns:
        Dict with keys: pr_auc, precision_real, recall_real, precision_fake,
                        recall_fake, best_threshold, best_f1
    """
    best_threshold, best_f1 = find_best_threshold(probs, labels)
    preds = (probs >= best_threshold).astype(int)
    pr_auc = average_precision_score(labels, probs)
    precision_fake = precision_score(labels, preds, pos_label=1, zero_division=0)
    recall_fake = recall_score(labels, preds, pos_label=1, zero_division=0)
    precision_real = precision_score(labels, preds, pos_label=0, zero_division=0)
    recall_real = recall_score(labels, preds, pos_label=0, zero_division=0)
    return {
        "pr_auc": float(pr_auc),
        "precision_real": float(precision_real),
        "recall_real": float(recall_real),
        "precision_fake": float(precision_fake),
        "recall_fake": float(recall_fake),
        "best_threshold": float(best_threshold),
        "best_f1": float(best_f1),
    }


def evaluate_model(model, loader, device, run_id: str):
    """Evaluate model and log confusion matrix + ROC curve to MLflow run.

    Args:
        model: Trained DeepfakeDetector
        loader: DataLoader for test set
        device: torch.device
        run_id: MLflow run ID to log artifacts to

    Returns:
        Tuple of (accuracy, f1_score)
    """
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

    # Cross-platform temp paths for artifacts
    _cm_path = Path(tempfile.gettempdir()) / "confusion_matrix.png"
    _roc_path = Path(tempfile.gettempdir()) / "roc_curve.png"

    extended = compute_extended_metrics(np.array(all_probs), np.array(all_labels))

    with mlflow.start_run(run_id=run_id):
        mlflow.log_metrics({
            "test_accuracy": acc,
            "test_f1": f1,
            "roc_auc": roc_auc,
            **{k: v for k, v in extended.items()},
        })

        fig, ax = plt.subplots()
        ax.matshow(cm, cmap="Blues")
        for (i, j), val in np.ndenumerate(cm):
            ax.text(j, i, str(val), ha="center", va="center")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        fig.savefig(str(_cm_path))
        mlflow.log_artifact(str(_cm_path))
        plt.close(fig)

        fig2, ax2 = plt.subplots()
        ax2.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}")
        ax2.plot([0, 1], [0, 1], "k--")
        ax2.set_xlabel("FPR")
        ax2.set_ylabel("TPR")
        ax2.legend()
        fig2.savefig(str(_roc_path))
        mlflow.log_artifact(str(_roc_path))
        plt.close(fig2)

    return acc, f1, all_probs, all_labels


if __name__ == "__main__":
    import argparse
    import json
    from ml.data_loader import FrameDataset
    from torch.utils.data import DataLoader

    parser = argparse.ArgumentParser(description="Evaluate Deepfake Detection model")
    parser.add_argument("--run_id", type=str, required=True,
                        help="MLflow run ID to evaluate")
    parser.add_argument("--data_path", type=str, default="data/features",
                        help="Path to directory of .pt feature files")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load model from MLflow run
    model_uri = f"runs:/{args.run_id}/model"
    model = mlflow.pytorch.load_model(model_uri)
    model = model.to(device)

    # Load test samples
    features_dir = Path(args.data_path)
    samples = []
    for pt_file in features_dir.rglob("*.pt"):
        tensor = torch.load(pt_file, weights_only=True)
        label = 1 if "fake" in pt_file.stem.lower() else 0
        samples.append((tensor, label))

    if not samples:
        print(f"No .pt files found in {args.data_path}. Exiting.")
        raise SystemExit(1)

    test_ds = FrameDataset(samples)
    test_loader = DataLoader(test_ds, batch_size=4, shuffle=False)

    acc, f1, all_probs_list, all_labels_list = evaluate_model(model, test_loader, device, args.run_id)
    print(f"Test accuracy: {acc:.4f} | F1: {f1:.4f}")

    # Write metrics for DVC tracking
    extended = compute_extended_metrics(np.array(all_probs_list), np.array(all_labels_list))
    eval_metrics = {"test_accuracy": acc, "test_f1": f1, **extended}
    Path("ml/eval_metrics.json").write_text(json.dumps(eval_metrics, indent=2))
    print("Metrics written to ml/eval_metrics.json")
