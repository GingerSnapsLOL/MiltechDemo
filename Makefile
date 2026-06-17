.PHONY: install run mcp-server lint format type test check docker-build docker-run pull-model

# Single source of truth for the model name is .env (MILTECH_MODEL_NAME).
# Override per-invocation with `make pull-model MODEL=...`.
-include .env
MODEL ?= $(or $(MILTECH_MODEL_NAME),qwen2.5:7b-instruct)

install:
	uv sync

run:
	uv run uvicorn miltech_demo.api.main:app --host 0.0.0.0 --port 8000 --reload

mcp-server:
	uv run python -m miltech_demo.mcp_server.server

lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy src

test:
	uv run pytest

check: lint type test

docker-build:
	docker build -t miltech-demo .

docker-run:
	docker run --rm -p 8000:8000 --env-file .env.example miltech-demo

pull-model:
	docker compose exec ollama ollama pull $(MODEL)