"""Automated retraining DAG — triggered by drift detection or schedule.

Pipeline: check_drift → fetch_new_data → run_mlproject →
          evaluate_model → register_if_better → promote_to_production
"""
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "mlops",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

DRIFT_THRESHOLD = 3.0
MIN_F1_THRESHOLD = 0.9


def check_drift(**context):
    """Check if retraining is needed based on baseline age or drift score.

    Returns the task_id to branch to: 'fetch_new_data' or 'skip_retraining'.
    """
    from pathlib import Path

    baseline_path = Path("/opt/airflow/ml/feature_baseline.json")
    if not baseline_path.exists():
        logger.info("No baseline found — skipping retraining")
        return "skip_retraining"
    # If baseline is older than 7 days, trigger retraining
    age_days = (datetime.now().timestamp() - baseline_path.stat().st_mtime) / 86400
    if age_days > 7:
        logger.info(f"Baseline is {age_days:.1f} days old — triggering retraining")
        return "fetch_new_data"
    logger.info(f"Baseline is {age_days:.1f} days old — no retraining needed")
    return "skip_retraining"


def fetch_new_data(**context):
    """Trigger deepfake_pipeline DAG to ingest fresh data."""
    from airflow.api.client.local_client import Client

    c = Client(None, None)
    c.trigger_dag("deepfake_pipeline")
    logger.info("Triggered deepfake_pipeline DAG for data ingestion")


def run_mlproject(**context):
    """Run MLflow project training entry point via CLI."""
    import subprocess

    result = subprocess.run(
        ["mlflow", "run", ".", "-e", "train"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"MLflow run failed:\n{result.stderr}")
    # Extract run_id from stdout
    run_id = None
    for line in result.stdout.split("\n"):
        if "Run ID:" in line:
            run_id = line.split("Run ID:")[-1].strip()
    if run_id:
        context["ti"].xcom_push(key="run_id", value=run_id)
    logger.info(f"MLflow training complete. run_id={run_id}")


def evaluate_model(**context):
    """Read new model metrics from MLflow and push them to XCom."""
    import mlflow

    run_id = context["ti"].xcom_pull(key="run_id", task_ids="run_mlproject")
    client = mlflow.tracking.MlflowClient()
    run = client.get_run(run_id)
    new_f1 = run.data.metrics.get("val_f1", 0.0)
    context["ti"].xcom_push(key="new_f1", value=new_f1)
    context["ti"].xcom_push(key="run_id", value=run_id)
    logger.info(f"Evaluated model: val_f1={new_f1:.4f}")


def register_if_better(**context):
    """Register model to Staging if it meets the F1 threshold."""
    import mlflow
    from airflow.exceptions import AirflowException

    new_f1 = context["ti"].xcom_pull(key="new_f1", task_ids="evaluate_model")
    run_id = context["ti"].xcom_pull(key="run_id", task_ids="evaluate_model")

    if new_f1 < MIN_F1_THRESHOLD:
        raise AirflowException(
            f"New model F1 {new_f1:.4f} < {MIN_F1_THRESHOLD} threshold. Not registering."
        )

    model_uri = f"runs:/{run_id}/model"
    result = mlflow.register_model(model_uri, "deepfake")
    client = mlflow.tracking.MlflowClient()
    client.transition_model_version_stage(
        name="deepfake",
        version=result.version,
        stage="Staging",
    )
    logger.info(f"Registered version {result.version} to Staging (F1={new_f1:.4f})")


def promote_to_production(**context):
    """Promote the Staging model version to Production, archiving the old one."""
    import mlflow

    client = mlflow.tracking.MlflowClient()
    staging_versions = client.get_latest_versions("deepfake", stages=["Staging"])
    if not staging_versions:
        logger.warning("No Staging model found to promote")
        return
    client.transition_model_version_stage(
        name="deepfake",
        version=staging_versions[0].version,
        stage="Production",
        archive_existing_versions=True,
    )
    logger.info(f"Promoted version {staging_versions[0].version} to Production")


with DAG(
    dag_id="retraining_dag",
    default_args=DEFAULT_ARGS,
    schedule_interval="@weekly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["deepfake", "retraining"],
) as dag:

    check = BranchPythonOperator(task_id="check_drift", python_callable=check_drift)
    skip = DummyOperator(task_id="skip_retraining")
    fetch = PythonOperator(task_id="fetch_new_data", python_callable=fetch_new_data)
    run = PythonOperator(task_id="run_mlproject", python_callable=run_mlproject)
    evaluate = PythonOperator(task_id="evaluate_model", python_callable=evaluate_model)
    register = PythonOperator(task_id="register_if_better", python_callable=register_if_better)
    promote = PythonOperator(task_id="promote_to_production", python_callable=promote_to_production)

    check >> [fetch, skip]
    fetch >> run >> evaluate >> register >> promote
