.PHONY: help install dev run clean test test-verbose test-cov test-cov-html test-watch lint lint-fix format pre-commit-install pre-commit-run docker-build docker-run docker-stop docker-logs docker-clean docker-compose-up docker-compose-down

# Docker configuration
DOCKER_IMAGE_NAME=letterbox-list-generator
DOCKER_CONTAINER_NAME=letterbox-app
DOCKER_PORT=8000

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Local Development:"
	@echo "  make install          - Create virtual environment and install dependencies"
	@echo "  make dev              - Install dependencies and start development server"
	@echo "  make run              - Start the FastAPI server with hot reload"
	@echo "  make run-prod         - Start the FastAPI server (production mode, no reload)"
	@echo "  make clean            - Remove virtual environment and cache files"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make test-cov-html    - Run tests and generate HTML coverage report"
	@echo "  make test-watch       - Run tests in watch mode (re-run on file changes)"
	@echo ""
	@echo "Linting and Code Quality:"
	@echo "  make lint             - Run pylint on source code"
	@echo "  make format           - Format code with black and isort"
	@echo "  make lint-fix         - Format code and run linter"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run   - Run all pre-commit hooks manually"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build       - Build Docker image"
	@echo "  make docker-run         - Run Docker container"
	@echo "  make docker-stop        - Stop Docker container"
	@echo "  make docker-logs        - View Docker container logs"
	@echo "  make docker-clean       - Remove Docker container and image"
	@echo ""
	@echo "Docker Compose Commands:"
	@echo "  make docker-compose-up  - Start application with docker-compose"
	@echo "  make docker-compose-down - Stop application with docker-compose"

# Create virtual environment and install dependencies
install:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Installing dependencies..."
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "Installation complete!"

# Install and run development server
dev: install run

# Start the FastAPI server with hot reload
run:
	@echo "Starting FastAPI server with hot reload..."
	. venv/bin/activate && uvicorn index:app --reload --host 0.0.0.0 --port 8000 --log-config uvicorn_log_config.json

# Start server without hot reload
run-prod:
	@echo "Starting FastAPI server (production mode)..."
	. venv/bin/activate && python index.py

# Clean up virtual environment and cache files
clean:
	@echo "Cleaning up..."
	rm -rf venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf **/__pycache__
	rm -rf **/.pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

# Run tests
test:
	@echo "Running tests..."
	. venv/bin/activate && pytest

# Run tests with verbose output
test-verbose:
	@echo "Running tests with verbose output..."
	. venv/bin/activate && pytest -v

# Run tests with coverage report
test-cov:
	@echo "Running tests with coverage..."
	. venv/bin/activate && pytest --cov=. --cov-report=term-missing

# Run tests and generate HTML coverage report
test-cov-html:
	@echo "Running tests and generating HTML coverage report..."
	. venv/bin/activate && pytest --cov=. --cov-report=html
	@echo "Coverage report generated at htmlcov/index.html"

# Run tests in watch mode
test-watch:
	@echo "Running tests in watch mode..."
	. venv/bin/activate && pytest-watch

# Linting and code quality commands

# Run pylint on source code
lint:
	@echo "Running pylint..."
	. venv/bin/activate && pylint --rcfile=.pylintrc \
		index.py \
		logger.py \
		controllers/ \
		routers/ \
		services/ \
		models/ \
		utils/ \
		jobs/

# Format code with black and isort
format:
	@echo "Formatting code with black..."
	. venv/bin/activate && black --line-length=120 .
	@echo "Sorting imports with isort..."
	. venv/bin/activate && isort --profile=black --line-length=120 .
	@echo "Code formatting complete!"

# Format and lint
lint-fix: format lint

# Install pre-commit hooks
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	. venv/bin/activate && pre-commit install
	@echo "Pre-commit hooks installed!"

# Run all pre-commit hooks manually
pre-commit-run:
	@echo "Running all pre-commit hooks..."
	. venv/bin/activate && pre-commit run --all-files

# Docker commands

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE_NAME):latest .
	@echo "Docker image built successfully!"

# Run Docker container
docker-run:
	@echo "Starting Docker container..."
	docker run -d \
		--name $(DOCKER_CONTAINER_NAME) \
		-p $(DOCKER_PORT):8000 \
		--env-file .env \
		$(DOCKER_IMAGE_NAME):latest
	@echo "Docker container started!"
	@echo "Access the application at http://localhost:$(DOCKER_PORT)"
	@echo "View logs with: make docker-logs"

# Stop Docker container
docker-stop:
	@echo "Stopping Docker container..."
	docker stop $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	docker rm $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	@echo "Docker container stopped!"

# View Docker container logs
docker-logs:
	@echo "Viewing Docker container logs (Ctrl+C to exit)..."
	docker logs -f $(DOCKER_CONTAINER_NAME)

# Clean up Docker resources
docker-clean: docker-stop
	@echo "Removing Docker image..."
	docker rmi $(DOCKER_IMAGE_NAME):latest 2>/dev/null || true
	@echo "Docker cleanup complete!"

# Docker Compose commands

# Start application with docker-compose
docker-compose-up:
	@echo "Starting application with docker-compose..."
	docker-compose up -d
	@echo "Application started!"
	@echo "Access the application at http://localhost:$(DOCKER_PORT)"
	@echo "View logs with: docker-compose logs -f"

# Stop application with docker-compose
docker-compose-down:
	@echo "Stopping application with docker-compose..."
	docker-compose down
	@echo "Application stopped!"
