.PHONY: dev test lint migrate infra

infra:
	docker compose up -d postgres redis minio minio-init

dev:
	cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd backend && poetry run celery -A app.workers.celery_app worker --loglevel=info

test:
	cd backend && poetry run pytest -v

lint:
	cd backend && poetry run ruff check .
	cd backend && poetry run mypy .

migrate:
	cd backend && poetry run alembic upgrade head

migrate-new:
	cd backend && poetry run alembic revision --autogenerate -m "$(msg)"
