# MLflow Enrichment + DVC Portability — Design Spec

**Goal:** Make simulated MLflow runs look realistic (proper durations aligned to git history), populate the MLflow Model Registry with versioned model progression, and make `dvc repro` work on any PC via a local DVC remote.

**Architecture:** Two independent changes to `ml/populate_mlflow.py` (MLflow enrichment) and the DVC configuration (`dvc.yaml`, `.dvc/config`, `data/raw.dvc`). No changes to backend, frontend, or Docker services.

**Tech Stack:** MLflow 3.x (SQL backend, MlflowClient API, aliases), DVC 3.x, Python 3.11, git.

---

## Sub-project A: MLflow Enrichment

### A1 — Realistic Run Timestamps

All runs in `populate_mlflow.py` are currently created via `mlflow.start_run()` which stamps them with wall-clock time (milliseconds apart). They need realistic start/end times anchored to the project's git history.

**Approach:** Replace `mlflow.start_run()` with `MlflowClient().create_run(experiment_id, start_time=<ms>)` + `client.set_terminated(run_id, end_time=<ms>)`. Log all metrics/params/tags/artifacts inside that run using `client.log_*` or `mlflow.start_run(run_id=...)` context.

**Timeline anchoring rules:**
- Training script committed: `2026-03-23 21:55 +0530` → first run starts at `2026-03-23 22:00`
- Runs are sequential (one finishes before next starts), simulating a single overnight sweep
- Duration per run = `epochs × avg_seconds_per_epoch`, where avg = 1.5–2.5 min/epoch for EfficientNet-B0 on CPU
- Evaluation runs follow the last training run (~05:15–06:00 Mar 24)
- Inference traces are scattered across Mar 24 morning (06:00–09:00)

**Timestamp implementation:** The `_ts(date_str)` helper parses date strings as IST (UTC+5:30) and converts to UTC epoch milliseconds for MLflow storage. Example: `"2026-03-23 22:00"` (IST) → subtract 5h30m → `2026-03-23 16:30:00 UTC` → `int(datetime(..., tzinfo=timezone.utc).timestamp() * 1000)`. All times in the schedule table below are IST; the helper handles the conversion.

**Exact run schedule (IST = UTC+5:30):**

| Run name | Start | Duration |
|---|---|---|
| lr-1e-3-batch16 | Mar 23 22:00 | 28 min |
| lr-5e-5-batch8 | Mar 23 22:35 | 38 min |
| lstm-hidden-128 | Mar 23 23:20 | 32 min |
| lstm-hidden-512 | Mar 24 00:00 | 48 min |
| dropout-0.5-regularized | Mar 24 01:00 | 52 min |
| 3layer-lstm | Mar 24 01:58 | 35 min |
| efficientnet-b1-backbone | Mar 24 02:40 | 43 min |
| overfit-no-dropout | Mar 24 03:30 | 28 min |
| batch-size-64 | Mar 24 04:05 | 22 min |
| adamw-weight-decay-1e-4 | Mar 24 04:32 | 38 min |
| eval-baseline-testset | Mar 24 05:15 | 12 min |
| eval-adamw-testset | Mar 24 05:30 | 10 min |
| eval-efficientnet-b1-testset | Mar 24 05:42 | 11 min |
| llm-judge-evaluation | Mar 24 05:55 | 18 min |

**Per-epoch metric timestamps:** Each of the `N` logged metric steps is spaced evenly between run start and end time. MLflow's `log_metric(timestamp=<ms>)` accepts an explicit timestamp, so the metric chart x-axis shows real wall-clock time.

### A2 — MLflow Model Registry

**Model name:** `deepfake-detector`

Five versions registered using `MlflowClient().create_model_version(name, source, run_id)`:

| Version | Source run | val_f1 | Aliases | Description |
|---|---|---|---|---|
| 1 | lr-1e-3-batch16 | 0.82 | `baseline` | Initial baseline — high LR, underfit |
| 2 | lstm-hidden-512 | 0.94 | — | Larger LSTM hidden dim |
| 3 | 3layer-lstm | 0.95 | — | Deeper LSTM stack |
| 4 | efficientnet-b1-backbone | 0.96 | `challenger` | Better CNN backbone |
| 5 | adamw-weight-decay-1e-4 | 0.97 | `champion` | Best model — AdamW optimizer |

**Implementation notes:**
- Uses MLflow 3.x aliases (`set_registered_model_alias`) not deprecated stage strings
- Each version gets tags: `val_f1`, `backbone`, `optimizer`, `git_commit`
- Model source URI obtained via `client.get_run(run_id).info.artifact_uri + "/model"` — this is the only correct approach for SQL-backed servers, which return absolute URIs (e.g. `/mlflow/mlruns/1/<run_id>/artifacts`). Do NOT construct manually from experiment `artifact_location` or hardcode `mlruns/<exp_id>/...`
- `create_registered_model` called once before versions; includes description
- Since `populate_mlflow.py` does not log actual PyTorch model artifacts (only simulated metrics), the `/model` subdirectory under `artifact_uri` won't exist — MLflow's model registry accepts this; the version is created with a URI pointer even without the files present

### A3 — populate_mlflow.py rewrite scope

The existing file is fully replaced. Key changes:
- New `_ts(date_str)` helper converts `"2026-03-23 22:00"` → milliseconds UTC
- `create_training_run(cfg)` uses `client.create_run` + `client.set_terminated` instead of context manager
- Metric steps logged with explicit `timestamp` aligned to run duration
- New `create_model_registry()` function at end of `__main__` block
- Traces timestamps changed from `time.time()` to fixed Mar 24 06:00–09:00 window

---

## Sub-project B: DVC Portability

### B1 — Local DVC Remote

**Remote path:** `./dvc-storage` (relative to repo root, same folder).

```
dvc remote add -d localstore ./dvc-storage
```

`.dvc/config` after this change:
```ini
[core]
    remote = localstore
['remote "localstore"']
    url = dvc-storage
```

`dvc-storage/` is added to `.gitignore` — it is **not committed to git**. It is a local data cache that lives alongside the repo on disk. When migrating to another PC, the `dvc-storage/` folder must be transferred **out-of-band** (zip, USB, shared drive, OneDrive sync) alongside the git repo. Once both are present on the new machine, `dvc pull` restores `data/raw` from the cache. A `git clone` alone is insufficient; the migration steps in SETUP.md must be explicit that `dvc-storage/` is copied separately.

### B2 — Track Raw Data

```
dvc add data/raw
```

This creates:
- `data/raw.dvc` — pointer file committed to git (contains MD5 hash of raw data)
- `data/raw/.gitignore` — prevents git from tracking MP4s directly

Then `dvc push` pushes the 106 videos into `dvc-storage/` content-addressed cache.

### B3 — Fix dvc.yaml Train Stage

Current broken stage:
```yaml
train:
  cmd: mlflow run . -e train   # ← requires conda + mlflow CLI on PATH
```

**DVC file location:** `dvc.yaml` must remain at the **repo root** (not `ml/dvc.yaml`). DVC resolves all dep/out paths relative to the directory containing `dvc.yaml`. Since deps reference `data/features` and `ml/train.py` from the repo root, the file must stay at root. The Files Changed table is corrected accordingly.

Fixed stage:
```yaml
train:
  cmd: python ml/train.py --data_path data/features --params_file ml/params.yaml
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
  outs:
    - ml/best_model.pt:
        cache: true
```

**Windows portability note:** The `cmd` uses plain `python` with no inline shell variable substitution — no `${VAR:-default}` bash syntax. `MLFLOW_TRACKING_URI` is set via a `.env` file loaded by Docker Compose (already present in the project), or exported in the shell before running `dvc repro`. This works on Windows cmd, PowerShell, and bash equally.

`ml/best_model.pt` is added as a DVC-cached output so the trained model is versioned.

### B4 — metrics.json enrichment

`ml/train.py` writes `ml/metrics.json` at end of training. Extend it from just `run_id` to:
```json
{
  "run_id": "...",
  "val_f1": 0.9688,
  "val_accuracy": 0.9688,
  "val_loss": 0.133,
  "best_epoch": 18
}
```

This makes `dvc metrics show` and `dvc metrics diff` useful. `val_loss` is included alongside `val_f1` and `val_accuracy` for completeness.

### B5 — Migration Setup Instructions

`SETUP.md` at repo root (new file) with:
1. Prerequisites (Python 3.11, Docker, DVC)
2. Clone + copy `dvc-storage/` folder
3. `dvc pull` to restore raw data
4. `docker compose up -d`
5. `dvc repro` to re-run full pipeline
6. Optional: `python ml/populate_mlflow.py` to re-populate MLflow UI

---

## Files Changed

| File | Change |
|---|---|
| `ml/populate_mlflow.py` | Full rewrite — timestamps, model registry |
| `ml/train.py` | Minor — enrich `metrics.json` output |
| `dvc.yaml` | Fix train stage cmd (repo root, not `ml/`), add `ml/best_model.pt` output |
| `.dvc/config` | Add localstore remote pointing to `./dvc-storage` |
| `data/raw.dvc` | New — DVC pointer for raw videos (generated by `dvc add data/raw`) |
| `data/raw/.gitignore` | New — generated by `dvc add`, prevents MP4s from being git-tracked |
| `.gitignore` | Add `dvc-storage/` entry |
| `SETUP.md` | New — migration guide (explicit: copy `dvc-storage/` out-of-band) |

## Out of Scope

- No changes to backend, frontend, Docker Compose, Prometheus, or Grafana
- No actual model training (all MLflow data is simulated)
- No cloud DVC remote (S3/GCS)
- No Airflow DAG changes
