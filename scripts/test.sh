echo "🚀 Testing code: Running pytest"
poetry run pytest --cov --cov-config=pyproject.toml --cov-report=xml
