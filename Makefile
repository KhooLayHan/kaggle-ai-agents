.PHONY: install test test-unit test-integration lint run web clean

install:
	uv pip install -e .

test:
	pytest

test-unit:
	pytest tests/unit

test-integration:
	pytest -m integration

lint:
	ruff check src/ tests/ main.py

format:
	ruff format src/ tests/ main.py

run:
	adk run src/agents/trading_agent

web:
	adk web src/agents

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
