#!/usr/bin/env bash
# setup.sh -- Bootstrap the deepfake detection stack from scratch.
# Usage: bash scripts/setup.sh
set -euo pipefail

echo "==> Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not found"; exit 1; }
command -v dvc >/dev/null 2>&1 || { echo "INFO: dvc not found -- installing..."; pip install dvc==3.48.4; }

echo "==> Copying .env.example -> .env (if not present)..."
[ -f .env ] || cp .env.example .env

echo "==> Pulling DVC-tracked data..."
dvc pull --no-run-cache || echo "WARN: dvc pull failed -- you may need to configure a DVC remote"

echo "==> Building Docker images..."
docker compose build --parallel

echo "==> Starting all services..."
docker compose up -d

echo ""
echo "==> Stack is running. Service URLs:"
echo "    Frontend:  http://localhost:3000"
echo "    API:       http://localhost:8000/docs"
echo "    MLflow:    http://localhost:5000"
echo "    Grafana:   http://localhost:3001  (admin / see .env)"
echo "    Airflow:   http://localhost:8080  (admin / admin)"
echo "    Prometheus:http://localhost:9090"
