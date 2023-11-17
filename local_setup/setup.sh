## Setup script for local development
export PYTHON_VERSION=3.11.6

echo "🚀 Creating virtual environment using pyenv and poetry"
# Install Python
pyenv install $PYTHON_VERSION
pyenv virtualenv $PYTHON_VERSION fuji-x-weekly-simluation-profiles-$PYTHON_VERSION

# Install dependencies
poetry install --no-root
poetry run pre-commit install
poetry shell
