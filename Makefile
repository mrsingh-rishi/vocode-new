.PHONY: chat speak listen lint lint_diff test help docker-build docker-run docker-compose-up docker-compose-down docker-logs docker-clean

# Development commands
chat:
	poetry run python playground/streaming/agent/chat.py

transcribe:
	poetry run python playground/streaming/transcriber/transcribe.py

synthesize:
	poetry run python playground/streaming/synthesizer/synthesize.py

turn_based_conversation:
	poetry run python quickstarts/turn_based_conversation.py

streaming_conversation:
	poetry run python quickstarts/streaming_conversation.py

# Run the main application locally
run:
	poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Docker commands
docker-build:
	docker build -t vocode-app .

docker-run: docker-build
	docker run -p 8000:8000 --env-file .env vocode-app

docker-compose-up:
	docker-compose up --build

docker-compose-up-detached:
	docker-compose up --build -d

docker-compose-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-logs-app:
	docker-compose logs -f vocode-app

docker-logs-redis:
	docker-compose logs -f redis

docker-clean:
	docker-compose down -v
	docker system prune -f

# Development setup
setup:
	cp .env.example .env
	@echo "Please edit .env with your actual API keys"

install:
	poetry install --extras "telephony"

install-dev:
	poetry install --extras "telephony" --group lint --group typing --group dev

# Testing and linting
PYTHON_FILES=.
lint: PYTHON_FILES=vocode/ quickstarts/ playground/
lint_diff typecheck_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$')

lint lint_diff:
	poetry run black $(PYTHON_FILES)

typecheck:
	poetry run mypy -p vocode
	poetry run mypy -p quickstarts
	poetry run mypy -p playground

typecheck_diff:
	poetry run mypy $(PYTHON_FILES)

test:
	poetry run pytest

test-docker:
	docker-compose exec vocode-app pytest

# Production commands
deploy:
	docker-compose -f docker-compose.yml up -d

stop:
	docker-compose stop

restart:
	docker-compose restart

status:
	docker-compose ps

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Development:"
	@echo "  setup              Copy .env.example to .env"
	@echo "  install            Install dependencies with Poetry"
	@echo "  install-dev        Install with development dependencies"
	@echo "  run                Run the application locally with hot reload"
	@echo "  chat               Run chat agent"
	@echo "  transcribe         Transcribe audio to text"
	@echo "  synthesize         Synthesize text into audio"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build       Build Docker image"
	@echo "  docker-run         Build and run Docker container"
	@echo "  docker-compose-up  Build and run with docker-compose"
	@echo "  docker-compose-up-detached  Run detached with docker-compose"
	@echo "  docker-compose-down Stop docker-compose services"
	@echo "  docker-logs        View all logs"
	@echo "  docker-logs-app    View application logs"
	@echo "  docker-logs-redis  View Redis logs"
	@echo "  docker-clean       Clean up Docker containers and volumes"
	@echo ""
	@echo "Production:"
	@echo "  deploy             Deploy to production"
	@echo "  stop               Stop services"
	@echo "  restart            Restart services"
	@echo "  status             Show service status"
	@echo ""
	@echo "Testing:"
	@echo "  lint               Lint all Python files"
	@echo "  lint_diff          Lint changed Python files"
	@echo "  typecheck          Type check code"
	@echo "  test               Run tests locally"
	@echo "  test-docker        Run tests in Docker"
	@echo "  help               Show this help message"

