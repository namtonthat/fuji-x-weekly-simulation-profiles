#!/bin/bash

set -e errexit

## Setup script for local development
export PYTHON_VERSION=3.13.0

check_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "Error: 'uv' command not found. Please install uv and try again."
    echo "You can install uv using one of the following commands:"
    echo "  brew install uv"
    echo "or"
    echo "  pip install uv"
    exit 1
  else
    echo "uv found: $(command -v uv)"
  fi
}

check_uv

echo "🚀 Creating virtual environment using uv"
# Install Python
uv venv --python $PYTHON_VERSION
source .venv/bin/activate
uv sync

uv run pre-commit clean
# Install dependencies
uv run pre-commit install
