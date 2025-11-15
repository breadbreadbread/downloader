# Makefile for reference-downloader

.PHONY: help install install-dev test test-coverage validate clean lint format security-check

# Default target
help:
    @echo "Available targets:"
    @echo "  install        Install runtime dependencies"
    @echo "  install-dev    Install development dependencies"
    @echo "  test           Run unit tests"
    @echo "  test-coverage  Run tests with coverage (enforces minimum threshold)"
    @echo "  validate       Run full validation (pip check + pip-audit + coverage)"
    @echo "  security-check Run security checks only (pip check + pip-audit)"
    @echo "  lint           Run linting tools (black, isort, flake8, mypy)"
    @echo "  format         Format code (black, isort)"
    @echo "  clean          Clean temporary files and artifacts"
    @echo "  help           Show this help message"

# Installation
install:
    pip install -r requirements.txt

install-dev:
    pip install -r requirements.txt -r requirements-dev.txt
    pip install -e .

# Testing
test:
    python -m unittest discover tests/ -v

test-coverage:
    python -m pytest --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=80

# Validation and security
validate:
    python scripts/validate_dependencies.py --coverage --verbose

security-check:
    python scripts/validate_dependencies.py --verbose

# Code quality
lint:
    @echo "Running black --check..."
    black --check src/ tests/ scripts/
    @echo "Running isort --check-only..."
    isort --check-only src/ tests/ scripts/
    @echo "Running flake8..."
    flake8 src/ tests/ scripts/
    @echo "Running mypy..."
    mypy src/

format:
    @echo "Running black..."
    black src/ tests/ scripts/
    @echo "Running isort..."
    isort src/ tests/ scripts/

# Cleanup
clean:
    @echo "Cleaning Python files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type f -name ".coverage" -delete
    find . -type f -name "coverage.json" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    rm -rf build/ dist/ validation-results.xml validation-results.json

# Full CI pipeline locally
ci: clean install-dev lint test-coverage security-check
    @echo "🎉 All CI checks passed!"