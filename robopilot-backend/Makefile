# Backend service management
start:
	docker-compose up -d --build

stop:
	docker-compose down

restart: stop start

migrate:
	docker-compose run --rm -T backend uv run alembic upgrade head

create-migration:
	docker-compose run --rm -T backend uv run alembic revision --autogenerate -m "$(MESSAGE)"

create-admin:
	docker-compose run --rm -T backend uv run python create_admin.py

shell:
	docker-compose exec backend bash

logs:
	docker-compose logs -f backend

logs-db:
	docker-compose logs -f db

clean:
	docker-compose down -v
	docker system prune -f

reset-db: stop
	docker-compose down -v
	docker-compose up -d db
	sleep 5
	docker-compose run --rm -T backend uv run alembic upgrade head

# LLM troubleshooting
check-llm:
	@echo "Checking LLM provider connectivity..."
	@echo "LM Studio (port 1234):"
	@curl -s http://localhost:1234/v1/models || echo "  ❌ LM Studio not running"
	@echo "Ollama (port 11434):"
	@curl -s http://localhost:11434/api/tags || echo "  ❌ Ollama not running"
	@echo "Current connections:"
	@curl -s http://localhost:8009/api/connections/ | python3 -m json.tool 2>/dev/null || echo "  ❌ Backend not running"

test-api:
	@echo "Testing backend API endpoints..."
	@curl -s -o /dev/null -w "Health check: %{http_code}\n" http://localhost:8009/docs
	@curl -s -o /dev/null -w "Connections API: %{http_code}\n" http://localhost:8009/api/connections/
	@curl -s -o /dev/null -w "Chat API: %{http_code}\n" http://localhost:8009/api/lmstudio/chat/sessions

# Code quality and linting
lint:
	@echo "🚀 Running Python code quality checks..."
	uv run ruff check app
	uv run ruff format app --check
	uv run mypy app

lint-fix:
	@echo "🚀 Running Python linting with auto-fix..."
	uv run ruff check app --fix
	uv run ruff format app
	uv run ruff check app --select I --fix

lint-check:
	@echo "🚀 Running Python checks only (no fixing)..."
	uv run ruff check app
	uv run mypy app

help:
	@echo "Available commands:"
	@echo "  start/stop/restart     - Service management"
	@echo "  migrate/create-migration - Database operations"
	@echo "  create-admin           - User management"
	@echo "  shell/logs/logs-db     - Container access"
	@echo "  clean/reset-db         - Cleanup operations"
	@echo "  check-llm/test-api     - Troubleshooting tools"
	@echo "  lint/lint-fix/lint-check - Code quality tools"
