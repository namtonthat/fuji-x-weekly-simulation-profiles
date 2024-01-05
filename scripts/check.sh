echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry lock --check"
poetry check --lock

echo "🚀 Linting code: Running pre-commit"
poetry run pre-commit run -a

echo "🚀 Static type checking: Running mypy"
poetry run mypy
