# Model Card -- DeepScan Deepfake Detector

## Model Details

| Field | Value |
|---|---|
| Model name | DeepfakeDetector (EfficientNet-B0 + 2-layer LSTM) |
| Version | See MLflow registry: `models:/deepfake/Production` |
| Framework | PyTorch 2.x |
| Task | Binary video classification: real (0) / fake (1) |
| Input | MP4 video -> 30 evenly-sampled face-cropped frames (224x224 RGB) |
| Output | Sigmoid probability (>=0.5 = fake) |
| Architecture | EfficientNet-B0 spatial encoder (frozen) + 2-layer LSTM (256 hidden) + linear classifier |

## Training Data

- **Dataset:** SDFVD (Synthesised Deepfake Video Dataset) -- face-swap and expression-transfer manipulations
- **Split:** 80/20 train/validation (random seed fixed via `params.yaml`)
- **Labels:** Filename-encoded (`_fake` suffix = 1, else 0)
- **Preprocessing:** MTCNN face detection -> 224x224 resize -> ToTensor (no ImageNet normalisation at feature stage -- applied inside EfficientNet)

## Intended Use

- **Primary use:** Detecting AI-generated or face-swapped video content
- **Users:** Security researchers, content moderation teams, journalists
- **Deployment:** On-premises (no cloud), CPU or CUDA inference

## Limitations and Bias

- Trained on SDFVD only -- may not generalise to newer deepfake techniques (e.g. diffusion-based synthesis)
- Face detection (MTCNN) may fail on low-resolution or occluded faces, falling back to full frame -- reducing detection accuracy
- Model performs best on frontal-face videos; profile or obscured faces reduce F1
- Dataset may not represent equal distribution across ethnicities -- bias in false-positive rates across demographic groups has not been formally audited

## Evaluation Metrics

| Metric | Value (see `ml/eval_metrics.json` for latest run) |
|---|---|
| Test Accuracy | Logged per run |
| Test F1 | Logged per run |
| ROC-AUC | Logged per run |
| PR-AUC | Logged per run |
| Best threshold | Logged per run |

## Ethical Considerations

- This model should **not** be used as the sole basis for legal or disciplinary action
- False positives (authentic videos classified as fake) carry reputational risk -- human review is recommended
- Model output includes Grad-CAM saliency maps for transparency

## MLOps Metadata

- Experiment tracking: MLflow (`deepfake-detection` experiment)
- Reproducibility: every run tagged with `git_commit` SHA and `device`
- Retraining: automated weekly via Airflow `retraining_dag` when drift score > 3.0
- Monitoring: Prometheus/Grafana -- alerts on error rate >5%, latency >200ms P95, drift score >3.0
