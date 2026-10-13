.PHONY: up down test test-pg lint lint-migrations migrate seed seed-pack write-pack grant-admin api web admin audit

PG_URL ?= postgresql+psycopg://mentor:mentor@localhost:5432/mentor

up:
	docker compose -f infrastructure/compose.yaml up --build

down:
	docker compose -f infrastructure/compose.yaml down

test:
	cd backend && ../.venv/bin/python -m pytest

# Runs the suite against an empty PostgreSQL database (it is downgraded to base first).
test-pg:
	cd backend && TEST_DATABASE_URL=$(PG_URL) ALEMBIC_DATABASE_URL=$(PG_URL) ../.venv/bin/python -m pytest --no-cov

lint:
	cd backend && ../.venv/bin/ruff check app tests alembic && ../.venv/bin/ruff format --check app tests alembic

# Lints every revision after the frozen baseline with squawk (Database migration strategy, phase 0).
lint-migrations:
	cd backend && ../.venv/bin/alembic upgrade 20261013_0001:head --sql > /tmp/new-migrations.sql && npx --yes squawk-cli@2 /tmp/new-migrations.sql

migrate:
	cd backend && ../.venv/bin/python -m app.cli migrate

seed:
	cd backend && ../.venv/bin/python -m app.cli seed

seed-pack:
	cd backend && ../.venv/bin/python -m app.cli seed-pack

write-pack:
	cd backend && ../.venv/bin/python -m app.cli write-pack

# make grant-admin CLERK_ID=user_123 REASON="first admin"
grant-admin:
	cd backend && ../.venv/bin/python -m app.cli grant-admin $(CLERK_ID) --reason "$(REASON)"

audit:
	cd backend && ../.venv/bin/pip-audit --skip-editable && ../.venv/bin/bandit -q -r app -ll
	cd frontend && npm audit --omit=dev --audit-level=high
	cd admin && npm audit --omit=dev --audit-level=high

api:
	cd backend && ../.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

web:
	cd frontend && npm run dev

admin:
	cd admin && npm run dev
