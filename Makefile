.PHONY: help install install-dev test lint format security quality clean pre-commit

# Default target
help:
	@echo "AliceMultiverse Development Commands"
	@echo "===================================="
	@echo "install       Install package in production mode"
	@echo "install-dev   Install package with development dependencies"
	@echo "test          Run tests with coverage"
	@echo "lint          Run all linters"
	@echo "format        Auto-format code"
	@echo "security      Run security scans"
	@echo "quality       Run all quality checks"
	@echo "clean         Clean build artifacts"
	@echo "pre-commit    Run pre-commit on all files"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,full]"
	pip install -r requirements-dev.txt
	pre-commit install

# Testing
test:
	pytest tests/ -v --cov=alicemultiverse --cov-report=term-missing

test-quick:
	pytest tests/ -v -x --tb=short

# Code Quality - Linting
lint: lint-python lint-yaml lint-shell lint-docker

lint-python:
	@echo "Running Python linters..."
	ruff check .
	mypy alicemultiverse --ignore-missing-imports
	pylint alicemultiverse --errors-only || true

lint-yaml:
	@echo "Running YAML linter..."
	yamllint .

lint-shell:
	@echo "Running shell script linter..."
	find . -name "*.sh" -o -name "*.bash" | xargs shellcheck || true

lint-docker:
	@echo "Running Dockerfile linter..."
	find . -name "Dockerfile*" | xargs hadolint || true

# Code Formatting
format: format-python format-yaml

format-python:
	@echo "Formatting Python code..."
	black .
	ruff check . --fix

format-yaml:
	@echo "Note: YAML formatting must be done manually"

# Security Scanning
security: security-secrets security-python security-deps

security-secrets:
	@echo "Scanning for secrets..."
	detect-secrets scan --baseline .secrets.baseline

security-python:
	@echo "Running Python security scan..."
	bandit -r alicemultiverse -ll --skip B101,B601

security-deps:
	@echo "Checking dependency vulnerabilities..."
	safety check || true

# Combined Quality Check
quality: lint security test
	@echo "All quality checks completed!"

# Pre-commit
pre-commit:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate

# Clean
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml

# Quick checks before commit
check: format lint test
	@echo "Ready to commit!"