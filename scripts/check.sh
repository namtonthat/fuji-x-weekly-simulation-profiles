echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running uv lock --check"
uv check --lock

echo "🚀 Linting code: Running pre-commit"
uv run pre-commit run -a

echo "🚀 Static type checking: Running mypy"
uv run mypy
