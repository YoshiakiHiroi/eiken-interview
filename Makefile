.PHONY: install lint format typecheck test api-dev web-dev

install:
	cd api && uv sync
	cd web && npm ci

lint:
	cd api && uv run ruff check . ../scripts && uv run ruff format --check . ../scripts
	cd web && npm run lint

format:
	cd api && uv run ruff check --fix . ../scripts && uv run ruff format . ../scripts
	cd web && npm run format

typecheck:
	cd api && uv run pyright
	cd web && npm run typecheck

test:
	cd api && uv run pytest -q
	cd web && npm run test

api-dev:
	cd api && uv run uvicorn --factory eiken_api.main:build_app --reload --port 8080

web-dev:
	cd web && npm run dev
