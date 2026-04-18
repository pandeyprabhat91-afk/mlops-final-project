"""Prometheus metrics definitions for the deepfake detection backend.

Metric types used:
  Counter   → monotonically increasing totals, exposed with _total suffix
  Gauge     → current point-in-time values (can go up/down)
  Histogram → latency / size distributions (_bucket, _sum, _count)
  Summary   → client-side quantile estimation (_sum + _count, i.e. _sum and _total equivalent)

Custom labels enrich every series with client metadata (mode, source_type, etc.)
so that Grafana can slice/filter without separate metrics.
"""
from prometheus_client import Counter, Gauge, Histogram, Summary

# ─── Counters (_total suffix) ─────────────────────────────────────────────────

# Total HTTP requests — sliced by HTTP method, endpoint, status code, and analysis mode
REQUEST_COUNT = Counter(
    "deepfake_requests_total",
    "Total HTTP requests received by the backend",
    ["method", "endpoint", "status", "mode"],  # mode: single | bulk
)

# Total media files submitted for analysis
IMAGES_PROCESSED = Counter(
    "deepfake_images_processed_total",
    "Total media files submitted for deepfake analysis",
    ["mode", "status"],  # mode: single | bulk; status: success | error
)

# Prediction outcomes labelled by result, mode, and caller type
PREDICTION_COUNTER = Counter(
    "deepfake_predictions_total",
    "Total predictions issued, broken down by label, analysis mode, and client type",
    ["label", "mode", "source_type"],
    # label: real | fake
    # mode: single | bulk
    # source_type: api | web | unknown  (derived from User-Agent)
)

# Errors categorised for alerting/SLO tracking
ERROR_COUNTER = Counter(
    "deepfake_errors_total",
    "Total errors by endpoint and error category",
    ["endpoint", "error_type"],
    # error_type: validation | inference | preprocessing | timeout | unknown
)

# Drift detection events
DRIFT_DETECTED = Counter(
    "deepfake_drift_detected_total",
    "Number of requests where feature distribution drift was detected",
)

# Bulk job lifecycle tracking
BULK_JOBS = Counter(
    "deepfake_bulk_jobs_total",
    "Total bulk analysis jobs by final status",
    ["status"],  # status: completed | failed | partial
)

# Data pipeline schema / format validation failures
PIPELINE_VALIDATION_FAILURES = Counter(
    "pipeline_validation_failures_total",
    "Number of data pipeline schema or validation failures",
)

# Video frames extracted (useful to correlate with compute cost)
FRAMES_EXTRACTED = Counter(
    "deepfake_frames_extracted_total",
    "Total video frames extracted for analysis",
    ["mode"],
)

# Model reloads triggered (admin or automatic)
MODEL_RELOADS = Counter(
    "deepfake_model_reloads_total",
    "Total model reload operations",
    ["trigger"],  # trigger: admin | automatic | startup
)

# ─── Gauges (current snapshot) ────────────────────────────────────────────────

# In-flight request count
ACTIVE_REQUESTS = Gauge(
    "deepfake_active_requests",
    "Number of prediction requests currently being processed",
)

# Estimated model size in RAM (MB) — set once at load time
MODEL_MEMORY_MB = Gauge(
    "deepfake_model_memory_mb",
    "Estimated model memory footprint in megabytes (parameter bytes / 1 MiB)",
)

# Latest feature drift z-score
DRIFT_SCORE = Gauge(
    "deepfake_drift_score",
    "Most recent feature drift z-score (0 = no drift, >3 = alert threshold)",
)

# Bulk processing backlog depth
BULK_QUEUE_DEPTH = Gauge(
    "deepfake_bulk_queue_depth",
    "Number of bulk analysis jobs currently queued or in-progress",
)

# Confidence score of the last prediction per label
LAST_CONFIDENCE = Gauge(
    "deepfake_last_confidence_score",
    "Confidence score of the most recent prediction (0.0-1.0)",
    ["label"],  # label: real | fake
)

# ─── Histograms (_bucket, _sum, _count) ───────────────────────────────────────

# End-to-end HTTP round-trip latency
REQUEST_LATENCY = Histogram(
    "deepfake_request_latency_seconds",
    "End-to-end HTTP request latency in seconds",
    ["endpoint", "mode"],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# Pure model forward-pass time (excludes preprocessing)
INFERENCE_LATENCY = Histogram(
    "deepfake_inference_latency_ms",
    "CNN+LSTM model forward-pass latency in milliseconds",
    ["mode"],
    buckets=[10, 25, 50, 100, 200, 500, 1000, 2000],
)

# Frame extraction + resize + normalisation time
PREPROCESSING_LATENCY = Histogram(
    "deepfake_preprocessing_latency_ms",
    "Video frame extraction and preprocessing latency in milliseconds",
    ["mode"],
    buckets=[50, 100, 250, 500, 1000, 2500, 5000],
)

# Output confidence distribution — tracks prediction calibration over time
CONFIDENCE_SCORE = Histogram(
    "deepfake_confidence_score",
    "Model output confidence score distribution",
    ["prediction", "mode"],  # prediction: real | fake
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# Uploaded file sizes — helps capacity planning
VIDEO_SIZE_BYTES = Histogram(
    "deepfake_video_size_bytes",
    "Size of uploaded video files in bytes",
    buckets=[
        10_000, 100_000, 500_000,
        1_000_000, 5_000_000, 10_000_000,
        50_000_000, 100_000_000, 200_000_000,
    ],
)

# Frames per video — informs compute cost and model input variability
FRAME_COUNT = Histogram(
    "deepfake_frame_count",
    "Number of video frames extracted per analysis request",
    buckets=[1, 2, 4, 8, 16, 32, 64, 128],
)

# ─── Summary (_sum and _count — the "_total" equivalent for suitable measures) ─
# Summary produces:
#   <name>_sum   — cumulative total time (seconds) across all observations
#   <name>_count — total number of observations (functionally a _total counter)
# This satisfies the requirement for metrics with _sum and _total suffixes.

INFERENCE_DURATION_SUMMARY = Summary(
    "deepfake_inference_processing_seconds",
    "Summary of model inference time — exposes _sum (CPU-seconds accumulated) "
    "and _count (total inferences run, i.e. _total equivalent)",
    ["mode"],
)

REQUEST_DURATION_SUMMARY = Summary(
    "deepfake_request_processing_seconds",
    "Summary of full request wall-clock time — exposes _sum and _count",
    ["endpoint", "mode"],
)

PREPROCESSING_DURATION_SUMMARY = Summary(
    "deepfake_preprocessing_processing_seconds",
    "Summary of video preprocessing time — exposes _sum and _count",
    ["mode"],
)
