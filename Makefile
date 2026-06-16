.PHONY: install run mcp-server lint format type test check docker-build docker-run

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
	docker run --rm -p 8000:8000 --env-file .env miltech-demo