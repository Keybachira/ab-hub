.PHONY: help install install-dev lint format typecheck test test-cov smoke ci clean build

PYTHON ?= python3
PIP ?= pip

help:
	@echo "AB-hub development targets"
	@echo ""
	@echo "  make install       Install package"
	@echo "  make install-dev   Install with dev dependencies"
	@echo "  make lint          Ruff check"
	@echo "  make format        Ruff format"
	@echo "  make typecheck     mypy"
	@echo "  make test          pytest"
	@echo "  make test-cov      pytest with coverage"
	@echo "  make smoke         CLI smoke checks"
	@echo "  make ci            Run lint + test (local CI parity)"
	@echo "  make build         Build sdist + wheel"
	@echo "  make clean         Remove build artifacts"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

lint:
	ruff check ab_hub tests

format:
	ruff format ab_hub tests
	ruff check --fix ab_hub tests || true

typecheck:
	mypy ab_hub --ignore-missing-imports

test:
	pytest -q --tb=short

test-cov:
	pytest -q --tb=short --cov=ab_hub --cov-report=term-missing

smoke:
	ab-hub --version
	ab-hub --help
	ab-hub auth --help
	ab-hub scan --help

ci: lint test smoke
	@echo "✓ Local CI checks passed"

build:
	$(PYTHON) -m pip install --upgrade build twine
	$(PYTHON) -m build
	twine check dist/*

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
