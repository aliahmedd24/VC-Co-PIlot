.PHONY: install dev test lint migrate worker status

install:
	cd backend && poetry install

dev:
	docker-compose up -d postgres redis minio
	cd backend && poetry run uvicorn app.main:app --reload

test:
	cd backend && poetry run pytest

lint:
	cd backend && poetry run ruff check .
	cd backend && poetry run mypy . --ignore-missing-imports

migrate:
	cd backend && poetry run alembic upgrade head

worker:
	cd backend && poetry run celery -A app.workers.celery_app worker --loglevel=info

status:
	@echo "=== Git Status ==="
	@git status --short
	@echo ""
	@echo "=== Docker Services ==="
	@docker-compose ps 2>/dev/null || echo "Docker not running"
