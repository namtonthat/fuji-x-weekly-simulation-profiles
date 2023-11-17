## Setup script for local development
export PYTHON_VERSION=3.11.6

# Install Python
pyenv install $PYTHON_VERSION
pyenv virtualenv $PYTHON_VERSION fuji-x-weekly-simluation-profiles-$PYTHON_VERSION

# Install dependencies
poetry install
poetry run pre-commit install
poetry shell
