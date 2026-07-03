# Use Python 3.13-slim as the base image
FROM python:3.13-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency configuration
COPY pyproject.toml .

# Create virtual environment and install dependencies
RUN uv venv --python 3.13 && uv pip install -r pyproject.toml

# Copy project files
COPY src/ ./src/
COPY README.md .

# Final stage
FROM python:3.13-slim

WORKDIR /app

# Copy virtual environment and app files from builder
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

# Expose port for MCP or web interfaces (if running fastmcp over HTTP/SSE)
EXPOSE 8000

# Set default entrypoint to run the trading CLI (override args when running)
ENTRYPOINT ["python", "src/cli.py"]
CMD ["--ticker", "AAPL"]
