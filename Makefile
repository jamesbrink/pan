.PHONY: format lint test coverage init clean all help

help:
	@echo "Available commands:"
	@echo "  make format     Format code with black and isort"
	@echo "  make lint       Run linting with pylint"
	@echo "  make test       Run unit tests"
	@echo "  make coverage   Run tests with coverage report"
	@echo "  make type       Run type checking with mypy"
	@echo "  make init       Initialize the database"
	@echo "  make clean      Remove cache files and database"
	@echo "  make all        Run format, lint, and test"

format:
	@echo "Sorting imports with isort..."
	isort *.py
	@echo "Formatting code with black..."
	black *.py

lint:
	@echo "Linting code with pylint..."
	pylint *.py

init:
	@echo "Initializing database..."
	python init_db.py

clean:
	@echo "Cleaning up..."
	rm -rf __pycache__/ .pytest_cache/ .coverage pan_memory.db
	find . -name "*.pyc" -delete

test:
	@echo "Running tests..."
	pytest tests/

coverage:
	@echo "Running tests with coverage..."
	pytest --cov=. --cov-report=term --cov-report=html tests/

type:
	@echo "Running type checking with mypy..."
	mypy --ignore-missing-imports *.py

all: format lint test init