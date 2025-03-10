#!/bin/bash

set -e errexit

## Setup script for local development
export PYTHON_VERSION=3.13.0

echo "🚀 Creating virtual environment using uv"
# Install Python
uv venv --python $PYTHON_VERSION
source .venv/bin/activate
uv sync

# Install dependencies
uv run pre-commit clean
uv run pre-commit install
