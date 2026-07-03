#!/bin/bash
set -e

echo "=== Bootstrapping Project Environment ==="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with Python 3.13..."
    uv venv --python 3.13
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing project dependencies..."
uv pip install -e .

echo "=== Setup Completed Successfully ==="
echo "To activate the environment, run: source .venv/bin/activate"
