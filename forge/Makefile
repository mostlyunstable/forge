.PHONY: help install dev test lint docker-up docker-down migrate migrate-new migrate-down migrate-history

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	cd backend && poetry install

dev: ## Start development server
	cd backend && uvicorn forge.presentation.app:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	cd backend && pytest

lint: ## Run linters
	cd backend && ruff check src/ && mypy src/

docker-up: ## Start all services with Docker
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-build: ## Build the backend image
	docker compose build backend

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-new: ## Generate a new migration (usage: make migrate-new MESSAGE="add users table")
	cd backend && alembic revision --autogenerate -m "$(MESSAGE)"

migrate-down: ## Downgrade by one revision
	cd backend && alembic downgrade -1

migrate-history: ## Show migration history
	cd backend && alembic history

migrate-current: ## Show current revision
	cd backend && alembic current

index: ## Index a repository (usage: make index REPO_PATH=/path/to/repo)
	curl -X POST http://localhost:8000/api/v1/code/index \
		-H "Content-Type: application/json" \
		-d '{"project_id": "default", "repo_path": "$(REPO_PATH)"}'

health: ## Check backend health
	curl http://localhost:8000/health
