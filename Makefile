.PHONY: help venv install test run replay generate-data clean docker-build docker-run

# Default target
help:
	@echo "Donizo Truth Engine - Makefile Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make venv          - Create virtual environment (recommended)"
	@echo "  make install       - Install dependencies and package"
	@echo "  make install-dev   - Install with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make test-quick    - Run tests without coverage"
	@echo "  make test-verbose  - Run tests with verbose output"
	@echo ""
	@echo "Data Generation:"
	@echo "  make generate-data - Generate synthetic test data (1000+ events)"
	@echo ""
	@echo "Running:"
	@echo "  make run           - Process events.jsonl (uses run mode)"
	@echo "  make replay        - Replay events.jsonl with hash verification"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run engine in Docker container"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Remove generated files and caches"
	@echo "  make clean-all     - Remove all generated files including data"
	@echo ""
	@echo "Best Practice Setup (with venv):"
	@echo "  1. make venv"
	@echo "  2. source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
	@echo "  3. make install"

# Virtual Environment Setup (Python Best Practice)
venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo ""
	@echo "✅ Virtual environment created!"
	@echo ""
	@echo "To activate:"
	@echo "  Linux/macOS: source venv/bin/activate"
	@echo "  Windows:     venv\\Scripts\\activate"
	@echo ""
	@echo "Then run: make install"

# Installation (assumes venv is activated if using one)
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# Testing
test:
	pytest

test-quick:
	pytest --no-cov

test-verbose:
	pytest -vv

# Data generation
generate-data:
	python3 generate_test_data.py

# Running
run:
	donizo_engine run --events events.jsonl --state rules_state.json --audit audit_log.jsonl

replay: run
	@echo "Extracting final hash for verification..."
	@tail -1 audit_log.jsonl | python3 -c "import sys, json; print(json.load(sys.stdin)['rules_hash'])" > expected_hash.txt
	@echo "Running replay mode..."
	donizo_engine replay --events events.jsonl --state rules_state_replay.json --audit audit_log_replay.jsonl --verify expected_hash.txt

# Docker
docker-build:
	docker build -t donizo-engine:latest .

docker-run:
	docker run --rm -v $(PWD)/data:/data donizo-engine:latest donizo_engine run --events /data/events.jsonl --state /data/rules_state.json --audit /data/audit_log.jsonl

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -f rules_state_replay.json audit_log_replay.jsonl expected_hash.txt

clean-all: clean
	rm -f events.jsonl rules_state.json audit_log.jsonl
