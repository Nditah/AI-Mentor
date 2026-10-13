.PHONY: up down test api web admin lint

up:
	docker compose -f infrastructure/compose.yaml up --build

down:
	docker compose -f infrastructure/compose.yaml down

test:
	cd backend && ../.venv/bin/python -m pytest

lint:
	cd backend && ../.venv/bin/ruff check app tests && ../.venv/bin/ruff format --check app tests

api:
	cd backend && ../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd frontend && npm run dev

admin:
	cd admin && npm run dev
