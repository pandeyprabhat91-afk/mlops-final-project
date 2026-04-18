"""Training entry point. Logs all metrics, params, and artifacts to MLflow."""
import subprocess
import sys
import tempfile
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
import torch.nn as nn
import yaml
from sklearn.metrics import accuracy_score, f1_score
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torchvision import transforms

sys.path.insert(0, str(Path(__file__).parent.parent))
from ml.model import DeepfakeDetector
from ml.data_loader import get_dataloaders


def load_params(params_file: str = "ml/params.yaml") -> dict:
    """Load hyperparameters from params.yaml."""
    with open(params_file) as f:
        return yaml.safe_load(f)["train"]


def get_git_commit() -> str:
    """Return current git commit SHA for reproducibility tagging."""
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


_AUG_TRANSFORM = transforms.Compose([
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.RandomGrayscale(p=0.05),
])


def extract_cnn_features(model, samples, device, aug_copies: int = 3):
    """Run EfficientNet on all samples and cache features in memory.

    With aug_copies > 1, each training sample is augmented aug_copies times
    (at the pixel level before CNN) to expand the effective dataset size.
    This is the correct way to augment when the CNN is frozen — augmentation
    must happen before feature extraction, not after.

    Returns:
        List of (feature_tensor[num_frames, cnn_dim], label) tuples
    """
    print(f"Pre-extracting CNN features for {len(samples)} videos (aug_copies={aug_copies})...")
    model.eval()
    cached = []
    with torch.no_grad():
        for i, (frames, label) in enumerate(samples):
            # Always include the original (no aug)
            flat = frames.to(device).view(-1, *frames.shape[1:])  # [F, 3, 224, 224]
            feats = model.cnn(flat).cpu()
            cached.append((feats, label))
            # Add augmented copies
            for _ in range(aug_copies - 1):
                aug_frames = torch.stack([_AUG_TRANSFORM(f) for f in frames]).to(device)
                aug_feats = model.cnn(aug_frames).cpu()
                cached.append((aug_feats, label))
            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{len(samples)} done")
    print(f"Feature extraction complete. {len(cached)} total samples (was {len(samples)}). Shape: {cached[0][0].shape}")
    return cached


def train_epoch(model, loader, optimizer, criterion, device):
    """Run one training epoch on cached CNN features. Returns (avg_loss, accuracy, f1)."""
    model.train()
    total_loss, all_preds, all_labels = 0.0, [], []
    for feats, labels in loader:
        feats, labels = feats.to(device), labels.float().to(device)
        optimizer.zero_grad()
        preds = model.forward_features(feats).squeeze(1)
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
    """Evaluate on cached CNN features. Returns (avg_loss, accuracy, f1)."""
    model.eval()
    total_loss, all_preds, all_labels = 0.0, [], []
    with torch.no_grad():
        for feats, labels in loader:
            feats, labels = feats.to(device), labels.float().to(device)
            preds = model.forward_features(feats).squeeze(1)
            total_loss += criterion(preds, labels).item()
            all_preds.extend((preds > 0.5).long().cpu().numpy())
            all_labels.extend(labels.long().cpu().numpy())
    avg_loss = total_loss / len(loader)
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    return avg_loss, acc, f1


def run_training(samples, params_file: str = "ml/params.yaml"):
    """Main training loop. Tracks everything to MLflow.

    Args:
        samples: List of (tensor, label) tuples from FrameDataset
        params_file: Path to params.yaml

    Returns:
        MLflow run_id string
    """
    params = load_params(params_file)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mlflow.set_experiment(params.get("experiment_name", "deepfake-detection"))

    # Cross-platform temp path for best model checkpoint
    _checkpoint_path = Path(tempfile.gettempdir()) / "best_model.pt"

    with mlflow.start_run() as run:
        mlflow.set_tag("git_commit", get_git_commit())
        mlflow.set_tag("device", str(device))
        mlflow.log_params(params)

        model = DeepfakeDetector(
            num_frames=params["num_frames"],
            lstm_hidden=params["lstm_hidden"],
            lstm_layers=params["lstm_layers"],
            dropout=params["dropout"],
        ).to(device)

        # Freeze CNN — pre-extract features once, train only LSTM + classifier.
        # With only 106 samples, CNN fine-tuning collapses scores; frozen is more stable.
        for param in model.cnn.parameters():
            param.requires_grad = False
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        print(f"Trainable: {trainable:,} / {total:,} params ({100*trainable/total:.1f}%)")

        # One-time CNN feature extraction — moves GPU bottleneck out of training loop
        cached_samples = extract_cnn_features(model, samples, device)

        optimizer = Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=params["lr"])
        criterion = nn.BCELoss()
        scheduler = ReduceLROnPlateau(optimizer, patience=3)
        # No image transforms — cached_samples are already CNN feature tensors
        train_loader, val_loader = get_dataloaders(
            cached_samples, batch_size=params["batch_size"],
            val_split=params["val_split"], transform=None
        )

        best_val_f1 = 0.0
        best_val_acc = 0.0
        best_val_loss = float("inf")
        best_epoch = 0
        for epoch in range(params["epochs"]):
            tr_loss, tr_acc, tr_f1 = train_epoch(model, train_loader, optimizer, criterion, device)
            val_loss, val_acc, val_f1 = eval_epoch(model, val_loader, criterion, device)
            scheduler.step(val_loss)

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
                best_val_acc = val_acc
                best_val_loss = val_loss
                best_epoch = epoch
                torch.save(model.state_dict(), str(_checkpoint_path))

        model.load_state_dict(torch.load(str(_checkpoint_path), weights_only=True))

        # Save to a stable local path so the backend can always find it
        stable_path = Path("ml/best_model.pt")
        torch.save(model.state_dict(), str(stable_path))

        mlflow.pytorch.log_model(model, artifact_path="model", registered_model_name="deepfake")
        mlflow.log_artifact(str(stable_path), artifact_path="checkpoints")
        print(f"Run ID: {run.info.run_id} | Best val F1: {best_val_f1:.4f}")
        return run.info.run_id, best_val_f1, best_val_acc, best_val_loss, best_epoch


if __name__ == "__main__":
    import argparse
    import json
    from ml.data_loader import FrameDataset

    parser = argparse.ArgumentParser(description="Train Deepfake Detection model")
    parser.add_argument("--data_path", type=str, default="data/features",
                        help="Path to directory of .pt feature files")
    parser.add_argument("--params_file", type=str, default="ml/params.yaml",
                        help="Path to params.yaml")
    args = parser.parse_args()

    # Load samples from .pt feature files and label CSV (or infer label from filename)
    # Filename convention: {video_name}.pt where name ends in _real or _fake
    features_dir = Path(args.data_path)
    samples = []
    for pt_file in features_dir.rglob("*.pt"):
        tensor = torch.load(pt_file, weights_only=True)
        # Label convention: filename containing 'fake' = 1, else 0
        label = 1 if "fake" in pt_file.stem.lower() else 0
        samples.append((tensor, label))

    if not samples:
        print(f"No .pt files found in {args.data_path}. Exiting.")
        raise SystemExit(1)

    run_id, val_f1, val_acc, val_loss, best_epoch = run_training(
        samples, params_file=args.params_file
    )

    metrics = {
        "run_id": run_id,
        "val_f1": round(val_f1, 4),
        "val_accuracy": round(val_acc, 4),
        "val_loss": round(float(val_loss), 4),
        "best_epoch": best_epoch,
    }
    Path("ml/metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"Metrics written to ml/metrics.json")
