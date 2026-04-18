# Test Plan — Deepfake Detection System

## Acceptance Criteria

| Criterion | Target |
|---|---|
| Accuracy | ≥ 90% on held-out test set |
| F1-score | ≥ 0.90 |
| P95 inference latency | < 200ms over 100 requests |

---

## Test Cases

| ID | Type | Description | Expected Result |
|---|---|---|---|
| TC-01 | Unit | `extract_frames` returns list ≤ requested count from mocked video | List of numpy arrays, len == num_frames |
| TC-02 | Unit | `extract_frames` raises ValueError when video cannot be opened | ValueError with "Cannot open video" |
| TC-03 | Unit | `extract_frames` raises ValueError when total_frames <= 0 | ValueError with "Video has no frames" |
| TC-04 | Unit | `detect_faces` fallback returns (224,224,3) when no face detected | Shape == (224,224,3) |
| TC-05 | Unit | `preprocess_video` output shape is (30, 3, 224, 224) | Tensor shape matches |
| TC-06 | Unit | `DeepfakeDetector` output shape (2,30,3,224,224) → (2,1) | Shape == (2,1) |
| TC-07 | Unit | `DeepfakeDetector` output in [0,1] | All values in sigmoid range |
| TC-08 | Unit | `DeepfakeDetector` gradients flow through all parameters | No frozen gradients |
| TC-09 | Unit | `compute_drift_score` returns < 1.0 at baseline mean | Score < 1.0 |
| TC-10 | Unit | `compute_drift_score` returns > 3.0 far from mean | Score > 3.0 |
| TC-11 | Unit | `is_drifted` returns True above threshold, False below | Boolean correct |
| TC-12 | Unit | `PredictResponse` rejects invalid confidence (1.5) | ValidationError |
| TC-13 | Unit | `PredictResponse` rejects invalid prediction ("unknown") | ValidationError |
| TC-14 | Integration | GET /health returns 200 with status="ok" | HTTP 200 |
| TC-15 | Integration | GET /ready returns 200 with model loaded | HTTP 200 |
| TC-16 | Integration | GET /ready returns 503 without model | HTTP 503 |
| TC-17 | Integration | GET /metrics returns Prometheus text | HTTP 200, body contains metric names |
| TC-18 | Integration | POST /predict with .avi file returns 400 | HTTP 400 |
| TC-19 | Integration | POST /predict with valid MP4 returns PredictResponse | HTTP 200, prediction in (real,fake) |
| TC-20 | Integration | POST /predict confidence >= 0.5 gives prediction="fake" | prediction == "fake" |
| TC-21 | Integration | POST /predict confidence < 0.5 gives prediction="real" | prediction == "real" |
| TC-22 | Acceptance | Model F1 ≥ 0.90 on test split | F1 >= 0.90 |
| TC-23 | Acceptance | P95 latency < 200ms over 100 requests | p95 < 200ms |
| TC-24 | Unit | `POST /feedback` with valid body returns `{"status": "logged"}` | HTTP 200 |
| TC-25 | Unit | `POST /feedback` with invalid ground_truth ("unknown") returns 422 | HTTP 422 |
| TC-26 | Unit | `POST /admin/rollback` with valid version triggers model reload | HTTP 200, model_version updated |
| TC-27 | Unit | `POST /admin/rollback` when reload raises exception returns 500 | HTTP 500 |
| TC-28 | Unit | `GET /admin/model-info` returns model_version, run_id, model_loaded | HTTP 200, all fields present |
| TC-29 | Unit | `evaluate.py` extended metrics includes pr_auc, precision_fake, recall_fake | Dict contains all 7 keys |
| TC-30 | Unit | `find_best_threshold` returns float in [0,1] | isinstance float, 0.0 <= t <= 1.0 |
| TC-31 | Unit | `quantize_model` saves a loadable file smaller than or equal to original | File exists, torch.load succeeds |
| TC-32 | Unit | `validate_feature_file` returns errors for wrong-shape tensor | errors list non-empty |
| TC-33 | Unit | `validate_feature_file` returns no errors for valid (30,3,224,224) tensor named `test_real.pt` | errors list empty |
| TC-34 | E2E | POST /predict with MP4 returns prediction in < 200ms (backend running) | HTTP 200, latency < 200ms |
