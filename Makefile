.PHONY: help install dev test lint format migrate up down

help:
	@echo "Available targets:"
	@echo "  install  - install backend + frontend deps"
	@echo "  dev      - run backend with reload"
	@echo "  test     - run backend tests"
	@echo "  lint     - run linters"
	@echo "  format   - auto-format code"
	@echo "  migrate  - run alembic migrations"
	@echo "  up       - docker compose up"
	@echo "  down     - docker compose down"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	cd backend && uvicorn app.main:app --reload

test:
	cd backend && pytest

lint:
	cd backend && ruff check . && mypy app

format:
	cd backend && ruff format .
	cd frontend && npm run format

migrate:
	cd backend && alembic upgrade head

up:
	docker compose up -d

down:
	docker compose down
