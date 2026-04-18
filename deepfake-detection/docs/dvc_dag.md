# DVC Pipeline DAG — Deepfake Detection

The DVC pipeline (`dvc.yaml`) defines a reproducible, dependency-tracked ML pipeline. Every stage tracks its inputs (`deps`), outputs (`outs`), and metrics. Running `dvc repro` re-executes only stages whose inputs have changed.

---

## Pipeline DAG

```
data/raw  (MP4s — DVC-tracked)
    │
    ▼
┌─────────────────────┐
│   extract_frames    │  python ml/preprocessing_pipeline.py extract_frames
│   deps: data/raw    │  → OpenCV samples 30 frames evenly per video
│   outs: data/frames │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│    detect_faces     │  python ml/preprocessing_pipeline.py detect_faces
│   deps: data/frames │  → MTCNN crops faces; fallback to resized frame
│   outs: data/faces  │
└─────────────────────┘
    │
    ▼
┌──────────────────────┐
│  compute_features    │  python ml/preprocessing_pipeline.py compute_features
│  deps: data/faces    │  → EfficientNet-B0 extracts 1280-dim features per frame
│  outs: data/features │  → saves per-video .pt tensors
└──────────────────────┘
    │
    ├──────────────────────────────────────┐
    ▼                                      ▼
┌──────────────────┐           ┌───────────────────────────┐
│ validate_schema  │           │          train             │
│ deps: data/feat  │           │ deps: data/features,       │
│ (no outs —       │           │       ml/train.py,         │
│  halts on fail)  │           │       ml/model.py,         │
└──────────────────┘           │       ml/params.yaml       │
                               │ params: ml/params.yaml     │
                               │ metrics: ml/metrics.json   │
                               │ outs: ml/best_model.pt     │
                               └───────────────────────────┘
                                           │
                                           ▼
                               ┌───────────────────────────┐
                               │         evaluate           │
                               │ deps: data/features,       │
                               │       ml/best_model.pt     │
                               │ metrics: ml/eval_metrics   │
                               │         .json              │
                               └───────────────────────────┘
                                           │
                                           ▼
                               ┌───────────────────────────┐
                               │         quantize           │
                               │ deps: ml/best_model.pt,    │
                               │       ml/quantize.py       │
                               │ outs: ml/best_model_       │
                               │       quantized.pt         │
                               └───────────────────────────┘
```

Run `dvc dag` in the repo root to see the live graph in the terminal.

---

## Stage Descriptions

| Stage | Command | Purpose |
|---|---|---|
| `extract_frames` | `preprocessing_pipeline.py extract_frames` | Sample 30 frames evenly per MP4 using `np.linspace` |
| `detect_faces` | `preprocessing_pipeline.py detect_faces` | MTCNN face detection; fallback to resized full frame if no face found |
| `compute_features` | `preprocessing_pipeline.py compute_features` | EfficientNet-B0 feature extraction → saves `(30, 1280)` tensors as `.pt` files |
| `validate_schema` | `validate_schema.py` | Assert tensor shape, dtype, no NaNs — halts pipeline on failure |
| `train` | `train.py` | EfficientNet-B0 + LSTM training; logs all metrics/params/artifacts to MLflow; saves `best_model.pt` |
| `evaluate` | `evaluate.py` | Confusion matrix, ROC-AUC, PR-AUC, per-class precision/recall; logs artifacts to MLflow |
| `quantize` | `quantize.py` | INT8 dynamic quantization of LSTM + Linear layers for CPU-optimised inference |

---

## Metrics Tracked by DVC

```bash
dvc metrics show        # prints val_f1, val_accuracy, val_loss, best_epoch
dvc metrics diff HEAD~1 # compare metrics vs previous commit
dvc params diff         # compare hyperparameters vs previous commit
```

`ml/metrics.json` (training) and `ml/eval_metrics.json` (evaluation) are committed to Git at each run so metric history is preserved across branches.

---

## Reproducibility

```bash
# Reproduce the full pipeline from data/raw
dvc repro

# Reproduce only training onwards (data unchanged)
dvc repro train

# Verify DAG integrity without running (used in CI)
dvc repro --dry
```

The `dvc.lock` file records the exact content hashes of every stage input and output. Checking out any Git commit and running `dvc repro` recreates the exact same model from that commit's data and code state.

---

## CI Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs `dvc repro --dry` on every push to validate that:
- All stage dependencies are declared correctly
- No circular dependencies exist
- The pipeline graph is consistent with the current code

This catches DVC misconfiguration before it reaches a machine with actual data.
