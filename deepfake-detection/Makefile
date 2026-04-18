.PHONY: setup up down test test-e2e train lint build logs help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup:  ## First-time setup: dvc pull + docker compose build + up
	bash scripts/setup.sh

up:  ## Start all Docker services
	docker compose up -d

down:  ## Stop all Docker services
	docker compose down

build:  ## Rebuild Docker images
	docker compose build --parallel

test:  ## Run unit and integration tests
	pytest tests/unit/ tests/integration/ -v --tb=short

test-e2e:  ## Run e2e latency tests (requires running backend)
	pytest tests/e2e/ -v --tb=short

train:  ## Run full DVC training pipeline
	dvc repro

lint:  ## Run linters (black, flake8, isort)
	black --check backend/ ml/ tests/
	flake8 backend/ ml/ tests/
	isort --check backend/ ml/ tests/

logs:  ## Tail backend logs
	docker compose logs -f backend

mlflow:  ## Open MLflow UI in browser
	python -c "import webbrowser; webbrowser.open('http://localhost:5000')"
