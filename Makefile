# AliceMultiverse Monorepo Makefile

.PHONY: help install install-dev test lint format clean build docker-build docker-push

# Default target
help:
	@echo "AliceMultiverse Monorepo Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install      Install all packages and services"
	@echo "  make install-dev  Install with development dependencies"
	@echo "  make test        Run all tests"
	@echo "  make lint        Run linting"
	@echo "  make format      Format code"
	@echo "  make clean       Clean build artifacts"
	@echo "  make build       Build all packages"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build Build all Docker images"
	@echo "  make docker-push  Push Docker images"
	@echo ""
	@echo "Kubernetes (see also: make -f k8s.mk help):"
	@echo "  make k8s-quickstart  Complete K8s setup and deploy"
	@echo "  make k8s-deploy      Deploy all services to K8s"
	@echo "  make k8s-logs        View service logs"
	@echo "  make k8s-status      Show cluster status"

# Install all packages and services
install:
	@echo "Installing shared packages..."
	cd packages/alice-events && pip install -e .
	cd packages/alice-models && pip install -e .
	@echo "Installing main package..."
	pip install -e .

# Install with development dependencies
install-dev: install
	@echo "Installing development dependencies..."
	cd packages/alice-events && pip install -e ".[dev]"
	cd packages/alice-models && pip install -e ".[dev]"
	pip install -e ".[dev]"
	pip install pre-commit
	pre-commit install

# Run all tests
test:
	@echo "Running tests..."
	pytest -v tests/
	@for pkg in packages/*; do \
		if [ -d "$$pkg/tests" ]; then \
			echo "Testing $$pkg..."; \
			cd $$pkg && pytest -v tests/ || exit 1; \
			cd ../..; \
		fi \
	done
	@for svc in services/*; do \
		if [ -d "$$svc/tests" ]; then \
			echo "Testing $$svc..."; \
			cd $$svc && pytest -v tests/ || exit 1; \
			cd ../..; \
		fi \
	done

# Run linting
lint:
	@echo "Running ruff..."
	ruff check .
	@echo "Running mypy..."
	mypy alicemultiverse packages/*/alice_* services/*/src

# Format code
format:
	@echo "Formatting with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .
	@echo "Fixing with ruff..."
	ruff check --fix .

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete

# Build all packages
build: clean
	@echo "Building packages..."
	@for pkg in packages/*; do \
		if [ -f "$$pkg/pyproject.toml" ]; then \
			echo "Building $$pkg..."; \
			cd $$pkg && python -m build || exit 1; \
			cd ../..; \
		fi \
	done

# Docker commands
docker-build:
	@echo "Building Docker images..."
	@for svc in services/*; do \
		if [ -f "$$svc/Dockerfile" ]; then \
			echo "Building $$svc..."; \
			docker build -t alice/$$(basename $$svc):latest $$svc || exit 1; \
		fi \
	done

docker-push:
	@echo "Pushing Docker images..."
	@for svc in services/*; do \
		if [ -f "$$svc/Dockerfile" ]; then \
			svc_name=$$(basename $$svc); \
			docker tag alice/$$svc_name:latest ghcr.io/alicemultiverse/$$svc_name:latest; \
			docker push ghcr.io/alicemultiverse/$$svc_name:latest || exit 1; \
		fi \
	done

# Service-specific commands
.PHONY: run-alice-interface run-asset-processor run-quality-analyzer

run-alice-interface:
	cd services/alice-interface && python -m alice_interface

run-asset-processor:
	cd services/asset-processor && python -m asset_processor

run-quality-analyzer:
	cd services/quality-analyzer && python -m quality_analyzer

# Development helpers
.PHONY: dev-setup redis-start redis-stop

dev-setup: install-dev
	@echo "Setting up development environment..."
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Development setup complete!"

redis-start:
	@echo "Starting Redis..."
	docker run -d --name alice-redis -p 6379:6379 redis:alpine || docker start alice-redis

redis-stop:
	@echo "Stopping Redis..."
	docker stop alice-redis

# Kubernetes helpers
.PHONY: k8s-quickstart k8s-deploy k8s-logs k8s-status

k8s-quickstart:
	@make -f k8s.mk quickstart

k8s-deploy:
	@make -f k8s.mk deploy-all-services

k8s-logs:
	@echo "View logs for specific services:"
	@echo "  make -f k8s.mk logs-asset"
	@echo "  make -f k8s.mk logs-asset-db"

k8s-status:
	@make -f k8s.mk debug-pods