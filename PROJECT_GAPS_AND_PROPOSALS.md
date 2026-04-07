# Deepfake Detection — Gap Analysis & Improvement Proposals

## What Already Exists ✓

| Area | Status |
|---|---|
| DVC pipeline (4-stage DAG) | ✓ Complete |
| MLflow experiment tracking + model registry | ✓ Complete |
| Docker Compose (multi-container: backend, frontend, mlflow, airflow, prometheus, grafana) | ✓ Complete |
| GitHub Actions CI (lint → unit → dvc-repro → integration → docker build) | ✓ Complete |
| `/health`, `/ready`, `/metrics` endpoints | ✓ Complete |
| Prometheus alerts (error rate >5%, P95 latency >200ms, drift, pipeline failure) | ✓ Complete |
| Grad-CAM explainability | ✓ Complete |
| Drift detection (z-score baseline) | ✓ Complete |
| Airflow DAGs (pipeline + retraining) | ✓ Complete |
| Feedback logger (JSONL) | ✓ Exists but not wired |
| React frontend with Pipeline dashboard | ✓ Complete |
| Unit + integration tests | ✓ Complete |

---

## What's Missing — Gap Analysis vs Guidelines + Evaluation Measures

### 🔴 Critical Gaps (required by guidelines, clearly absent)

**1. Feedback loop endpoint not wired**
`feedback_logger.py` exists but `/predict` never calls it, and there's no `POST /feedback` endpoint. The guideline explicitly requires "log ground-truth labels as they become available." This is spec'd but broken.

**2. Feature Store separation**
Guidelines say: *"version feature engineering logic separately from model logic."* Currently `preprocessing_pipeline.py` and `ml/data_loader.py` are entangled. A separate `ml/feature_store/` module with versioned feature schemas is missing.

**3. Model quantization / pruning**
Guidelines say: *"optimize models for local/on-prem hardware (quantization or pruning)"* given No-Cloud restriction. Nothing in `train.py`, `evaluate.py`, or the DVC pipeline quantizes/prunes the exported model.

**4. Rollback mechanism**
Guidelines require it for failed deployments. The `/admin/reload-model` endpoint reloads but has no version-pinning — it always loads "latest". No rollback-to-specific-version logic.

**5. Data encryption**
Guidelines: *"all sensitive data must be encrypted at rest and in transit."* No encryption at rest for uploaded videos or features. TLS is not configured in nginx or docker-compose.

---

### 🟡 Evaluation Gaps (commonly assessed in end-to-end AI projects)

**6. Precision, Recall, AUC per class — missing from metrics**
`evaluate.py` tracks accuracy + F1 + ROC-AUC globally, but deepfake detection is an imbalanced problem. Missing: per-class precision/recall, average precision (PR-AUC), and a calibration curve.

**7. Confidence threshold tuning**
Currently hardcoded at 0.5. A proper evaluation should include threshold sweep (finding optimal F1 threshold) and persisting it to `params.yaml`.

**8. Inference latency benchmark**
The guideline specifies `< 200ms` as a business metric. There's a Prometheus alert but no automated benchmark test that validates this during CI.

**9. End-to-end test (video → prediction)**
Tests exist for unit + integration, but no true e2e test: upload a real `.mp4` → assert prediction shape/type → assert latency < 200ms. This is the most visible eval measure.

**10. Grafana dashboard provisioning**
`docker-compose.yml` mounts `./monitoring/grafana/provisioning` and `./monitoring/grafana/dashboards` but those directories are empty/missing. Grafana won't auto-configure dashboards on startup.

**11. Data validation schema (Great Expectations or Pydantic)**
Guidelines require automated schema checks during ingestion. Only Prometheus alerts on pipeline failures — no upfront schema validation step in the DVC pipeline.

**12. Model card / documentation for model decisions**
Best practice for AI applications: a `MODEL_CARD.md` documenting training data, bias considerations, intended use, limitations.

---

### 🟢 Nice-to-Have (ease of use, comprehensiveness)

**13. One-command setup script**
`SETUP.md` exists but requires many manual steps. A `make` or `scripts/setup.sh` that does `dvc pull → docker compose up` in order would dramatically improve UX.

**14. Batch prediction endpoint**
Currently only single-file upload. A `POST /predict/batch` accepting multiple videos (or a zip) is important for real-world use.

**15. Frontend feedback UI**
The React frontend shows predictions but has no way for users to submit ground-truth (correct/incorrect button), which is needed to close the feedback loop (#1).

**16. Admin dashboard page (model version, drift status, recent predictions)**
The frontend links to Grafana externally but has no native admin view. A simple `/admin` page showing current model version, drift score, last 10 predictions would make the system self-contained.

---

## Proposed Priority Order

| # | Item | Effort | Impact |
|---|---|---|---|
| 1 | Wire feedback loop + `POST /feedback` endpoint + frontend button | Low | High |
| 2 | Grafana dashboard provisioning files | Low | High |
| 3 | End-to-end test with latency assertion | Low | High |
| 4 | Model quantization (torch.quantization) in DVC evaluate stage | Medium | High |
| 5 | Extended metrics: PR-AUC, per-class, threshold tuning | Medium | High |
| 6 | Data validation schema step in DVC pipeline | Medium | Medium |
| 7 | Rollback to specific model version endpoint | Medium | Medium |
| 8 | One-command setup script | Low | High (UX) |
| 9 | Batch prediction endpoint | Medium | Medium |
| 10 | Frontend admin dashboard page | Medium | Medium |
| 11 | Feature store separation | High | Medium |
| 12 | TLS / data encryption | High | Required by guidelines |
| 13 | Model card | Low | Documentation |
