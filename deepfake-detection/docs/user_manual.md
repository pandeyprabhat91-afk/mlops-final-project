# User Manual — Deepfake Detection System

## What this system does

Upload an MP4 video and the system will classify it as **REAL** or **FAKE** (AI-generated/deepfake). The system uses a deep learning model trained to detect manipulated faces in videos.

---

## Getting Started

### Prerequisites
- Docker and Docker Compose installed
- Host filesystem encrypted (BitLocker/LUKS) — required for data security

### Starting the system

```bash
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, GRAFANA_ADMIN_PASSWORD, AIRFLOW__CORE__FERNET_KEY
docker compose up -d
```

Wait approximately 60 seconds for all services to start. Then open:
- **Application:** http://localhost:3000
- **MLflow UI:** http://localhost:5000
- **Airflow UI:** http://localhost:8080
- **Grafana:** http://localhost:3001

---

## Using the Application

### Step 1: Open the application
Navigate to http://localhost:3000 in your web browser.

### Step 2: Upload a video
Click **browse** or drag and drop an MP4 video file onto the upload area.
- File must be in **MP4 format**
- Maximum size: **100MB**

### Step 3: Wait for the result
The system analyzes your video. This typically takes 5–30 seconds depending on video length.

### Step 4: Read the result

| Result | Meaning |
|---|---|
| **REAL** (green) | The video appears to be authentic footage |
| **FAKE** (red) | The video appears to be AI-generated or manipulated |

- **Confidence %:** How certain the model is (higher = more confident)
- **Grad-CAM heatmap:** Shows which parts of the face influenced the decision most (red = high influence)
- **Frames analyzed:** Number of frames the model processed

### Step 5: Submit feedback (optional)

After seeing the result, two buttons appear: **Correct** and **Incorrect**.

- Click **Correct** if the prediction matches what you know about the video.
- Click **Incorrect** if the prediction is wrong.

This feedback is saved and used to improve the model over time. A confirmation message "Feedback recorded" will appear once submitted.

---

## Pipeline Dashboard

Click **Pipeline Dashboard** in the navigation bar to see:

| Widget | Description |
|---|---|
| Pipeline Throughput | Videos processed per minute in the last pipeline run |
| MLflow Experiments | Recent training runs with accuracy, F1-score, and git commit |
| Airflow DAG Status | History of data pipeline and retraining runs |

Links at the bottom open the full MLflow and Airflow UIs.

---

## Admin Page

Click **Admin** in the navigation bar to access the Admin page. This page is for technical users and shows:

| Section | Description |
|---|---|
| **Current Model** | The MLflow model version and run ID currently loaded for inference |
| **Rollback** | Enter a version number and click **Rollback** to switch to a previous model version |
| **External Tools** | Quick links to MLflow, Grafana, Prometheus, and Airflow UIs |

### Rolling back to a previous model version

1. Open the MLflow UI (http://localhost:5000) and note the version number you want to restore.
2. Go to the Admin page in the application.
3. Enter the version number in the **Rollback to version** field and click **Rollback**.
4. The system will reload the model — the status box will update to confirm.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Only MP4 files are accepted" | Convert your video to MP4 format |
| "File must be under 100MB" | Trim the video or reduce resolution |
| "An unexpected error occurred" | Wait 30 seconds and retry — system may be initializing |
| Blank result / confidence = 0 | Video may not contain a clearly visible human face |
| Grafana shows no data | Wait for the first Prometheus scrape (15s interval) |
| Airflow DAG not running | Check Airflow UI at localhost:8080; ensure data is in `data/landing/` |
