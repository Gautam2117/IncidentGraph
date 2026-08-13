.PHONY: help bootstrap dev lint typecheck test docker-up docker-down db-migrate clean verify-clone

PYTHON ?= python3
VENV ?= .venv

help:
	@echo "IncidentGraph Command Palette:"
	@echo "  make bootstrap       Setup virtual environment and install dependencies"
	@echo "  make dev             Start control-plane and console in dev mode"
	@echo "  make lint            Run Python (ruff) and TS linters"
	@echo "  make typecheck       Run mypy and tsc"
	@echo "  make test            Run backend unit & integration tests"
	@echo "  make docker-up       Spin up PostgreSQL (pgvector), Redis, and OTel stack"
	@echo "  make docker-down     Tear down containers"
	@echo "  make db-migrate      Apply database migrations"
	@echo "  make verify-clone    Run clean-clone verification check"
	@echo "  make clean           Remove temporary files & build caches"

bootstrap:
	$(PYTHON) -m venv $(VENV)
	./$(VENV)/bin/pip install --upgrade pip setuptools wheel
	./$(VENV)/bin/pip install -e ".[dev]"
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi

lint:
	./$(VENV)/bin/ruff check services/ tests/
	@if [ -d "apps/console/node_modules" ]; then cd apps/console && npm run lint; fi

typecheck:
	./$(VENV)/bin/mypy services/control-plane/app
	@if [ -d "apps/console/node_modules" ]; then cd apps/console && npx tsc --noEmit; fi

test:
	./$(VENV)/bin/pytest services/control-plane/tests -v

docker-up:
	docker compose up -d

docker-down:
	docker compose down -v

db-migrate:
	cd services/control-plane && ../../$(VENV)/bin/alembic upgrade head

verify-clone:
	@bash scripts/verify_clone.sh

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache htmlcov coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
