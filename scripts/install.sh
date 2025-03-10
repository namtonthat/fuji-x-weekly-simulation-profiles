#!/bin/bash
set -e errexit

export PYTHON_VERSION=3.13.0

# Ensure uv is available.
ensure_uv() {
  if [ "$GITHUB_ACTIONS" = "true" ]; then
    echo "Running in GitHub Actions. Installing uv via pip..."
    pip install uv
  else
    echo "Running locally. Checking for uv..."
    if ! command -v uv >/dev/null 2>&1; then
      echo "Error: 'uv' command not found. Please install uv using one of:"
      echo "  brew install uv"
      echo "  pip install uv"
      exit 1
    fi
    echo "uv found: $(command -v uv)"
  fi
}

# Set up the Python virtual environment.
setup_env() {
  echo "🚀 Creating virtual environment using uv"
  uv venv --python "$PYTHON_VERSION"
  source .venv/bin/activate

  if [ -n "$GROUP_NAME" ]; then
    echo "Syncing dependencies for group: $GROUP_NAME"
    uv sync --group "$GROUP_NAME"
  else
    echo "Syncing dependencies"
    uv sync
  fi
}

# Set up pre-commit hooks only when running locally.
setup_precommit() {
  echo "Installing pre-commit hooks..."
  uv run pre-commit clean
  uv run pre-commit install
}

# Main execution flow.
ensure_uv
setup_env
setup_precommit

echo "Setup complete!"
