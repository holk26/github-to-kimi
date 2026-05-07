#!/bin/bash

set -e

echo "========================================"
echo "Starting Kimi CLI Service"
echo "========================================"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="/root/.local/bin:/root/.cargo/bin:$PATH"
fi

# Install kimi-cli if not present
if ! command -v kimi &> /dev/null; then
    echo "Installing kimi-cli..."
    uv tool install kimi-cli
fi

# Verify installation
echo "Kimi version:"
kimi --version

echo "========================================"
echo "Starting FastAPI server..."
echo "========================================"

# Start FastAPI
exec uvicorn main:app --host 0.0.0.0 --port 8000
