#!/bin/bash
echo "🚀 Checking uv lock file consistency with 'pyproject.toml': Running uv lock --check"
uv lock

echo "🚀 Linting code: Running pre-commit"
uv run pre-commit run -a

echo "🚀 Static type checking: Running mypy"
uv run mypy
