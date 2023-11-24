## Setup script for local development
export PYTHON_VERSION=3.11.6

echo "🚀 Creating virtual environment using pyenv and poetry"
# Install Python
pyenv install $PYTHON_VERSION
pyenv virtualenv-delete -f fuji-x-weekly-simulation-profiles-$PYTHON_VERSION
pyenv virtualenv $PYTHON_VERSION fuji-x-weekly-simulation-profiles-$PYTHON_VERSION
pyenv local fuji-x-weekly-simulation-profiles-$PYTHON_VERSION

# Install dependencies
poetry shell
poetry run pre-commit install
poetry install --no-root
